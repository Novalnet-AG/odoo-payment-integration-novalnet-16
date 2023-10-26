# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging, requests, base64, pprint, json, re, hashlib
from werkzeug import urls
from odoo import _, api, fields, models, service
from odoo.exceptions import UserError,ValidationError
from odoo.addons.payment_novalnet.const import PAYMENT_FLOW, DEACTIVATED_PAYMENT, PAYMENT_NAME
from odoo.addons.payment import utils as payment_utils
from odoo.addons.payment_novalnet.controllers.main import PaymentNovalnetController

_logger = logging.getLogger(__name__)


class NovalnetTariff(models.Model):
    _name = 'novalnet.tariff'
    _description = 'Novalnet tariff'

    name = fields.Char(translate=True)
    tariff_id = fields.Integer()
    tariff_type = fields.Integer()

class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[('novalnet', 'novalnet')], ondelete={'novalnet': 'set default'}
    )
    novalnet_public_key = fields.Char(
        string="Product activation key",
        help="Your product activation key is a unique token for merchant authentication and payment processing. ",
        required_if_provider="novalnet", groups="base.group_system"
    )

    @api.model
    def _default_webhook_url(self):
        base_url = self.get_base_url()
        return urls.url_join(base_url, PaymentNovalnetController._webhook_url)

    novalnet_webhook_url = fields.Char(string="Notification / Webhook URL",default =_default_webhook_url,readonly = 1 )
    novalnet_webhook_testing = fields.Boolean(default=False ,string = 'Allow manual testing of notification/webhook URL')
    novalnet_webhook_email = fields.Char(string="Send emails to" )
    novalnet_key_password = fields.Char(
        string="Payment access key",
        help="Your secret key used to encrypt the data to avoid user manipulation and fraud.",
        required_if_provider="novalnet", groups="base.group_system"
    )
    novalnet_client_key = fields.Char( string="Client Key",readonly = 1)
    hide_novalnet_tariff = fields.Boolean(default=False)
    novalnet_tariff_selection = fields.Many2one('novalnet.tariff', string="Select Tariff ID ", help="Select a Tariff ID to match the preferred tariff plan you created at the Novalnet Admin Portal for this project")
    novalnet_payment_methods_ids = fields.One2many('novalnet.payment.method', 'provider_id')




    def _compute_feature_support_fields(self):
        """ Override of `payment` to enable additional features. """
        super()._compute_feature_support_fields()
        self.filtered(lambda p: p.code == 'novalnet').update({
            # 'support_fees': True,
            'support_manual_capture': True,
            'support_refund': 'partial',
            'support_tokenization': True,
        })

    @api.onchange('novalnet_public_key')
    def _on_change_novalnet_public_key(self):
        if not self.novalnet_public_key:
            self.hide_novalnet_tariff = False

    @api.onchange('novalnet_key_password')
    def _on_change_novalnet_key_password(self):
        if not self.novalnet_key_password:
            self.hide_novalnet_tariff = False

    def _validate_checsum(self, checksum, tid, event_type, status, amount=None, currency=None):

        if None in (checksum, tid, event_type, status):
            raise ValidationError(_("'While notifying some data has been changed. The hash validation failed"))

        regenerated_checksum = f"{tid}{event_type}{status}"
        if amount: regenerated_checksum =  f"{regenerated_checksum}{amount}"
        if currency: regenerated_checksum =  f"{regenerated_checksum}{currency}"
        access_key = self.novalnet_key_password[::-1]
        regenerated_checksum = f"{regenerated_checksum}{access_key}"
        regenerated_checksum = hashlib.sha256(regenerated_checksum.encode())
        checksum_sha_digest = regenerated_checksum.hexdigest()
        _logger.info(("generated Hash %s") % (checksum_sha_digest))
        if checksum_sha_digest!= checksum:
            raise ValidationError(_("'While notifying some data has been changed. The hash check failed"))


    def _novalnet_get_available_payments(self, order, invoice, amount, currency, partner_id):
        if not order:
            return
        methods = self.novalnet_payment_methods_ids.filtered(lambda m: m.active and m.shop_active_status)

        payment_guaranteed = methods.filtered( lambda m: re.search( r"GUARANTEED",m.payment_code ) )
        converted_amount = payment_utils.to_minor_currency_units( amount, currency )

        if order and payment_guaranteed:
            if partner_id != order.partner_shipping_id.id or currency.name != 'EUR' or converted_amount <= 999:
                methods = methods - payment_guaranteed
            else:
                for guranteed_payment in payment_guaranteed:
                    payment_need_to_removed = None
                    try:
                        payment_need_to_removed = re.search( 'GUARANTEED_(.+?)$', guranteed_payment.payment_code ).group(1)
                    except AttributeError:
                        _logger.info("could not extract guranteed_payment name")
                    _logger.info(payment_need_to_removed)
                    if payment_need_to_removed:
                        methods = methods.filtered( lambda m: m.payment_code != payment_need_to_removed )
        return methods

    def get_novalnet_access_details(self):
        if not self.novalnet_public_key or not self.novalnet_key_password or self.code != 'novalnet':
            raise ValidationError("novalnet: " + _("Mandatory fields missing"))
        data = {
            "merchant": {
                "signature" :  self.novalnet_public_key
            },
            "custom" : {
                "lang": "EN"
            }
        }
        merchant_dict = self._novalnet_make_request("merchant/details",data=data)

        if not merchant_dict.get('merchant')['tariff']:
            raise ValidationError("novalnet: " + _("Could not found tariff information"))

        if not merchant_dict.get('merchant')['tariff']:
            raise ValidationError("novalnet: " + _("Could not found tariff information"))

        if 'client_key' in  merchant_dict.get('merchant') and merchant_dict.get('merchant')['client_key']:
            self.novalnet_client_key = merchant_dict.get('merchant')['client_key']

        for tariff_id,val in merchant_dict.get('merchant')['tariff'].items():
            noval_tariff= self.env['novalnet.tariff'].search([('tariff_id', '=', tariff_id)])
            create_dict = {'name': val['name'] ,'tariff_id': tariff_id, 'tariff_type' : val['type']}
            noval_tariff.write(create_dict) if noval_tariff  else self.env['novalnet.tariff'].create(create_dict)
        self.hide_novalnet_tariff = True
        if 'payment_types' in merchant_dict.get('merchant') and merchant_dict.get('merchant')['payment_types']:
            self.sync_novalnet_payment_methods(merchant_dict.get('merchant')['payment_types'])

    def sync_novalnet_payment_methods(self,payment_methods):
        novalnet_payment_method = self.env['novalnet.payment.method']
        saved_payment_methods = self.with_context(active_test=False).novalnet_payment_methods_ids
        for payment_method in saved_payment_methods:
            payment_method.active = payment_method.payment_code in payment_methods
        methods_to_create = set(payment_methods) - set(saved_payment_methods.mapped('payment_code'))
        methods_to_create = set(methods_to_create) - set( DEACTIVATED_PAYMENT )
        for payment_name in methods_to_create:
            val_dict = {
                'name' : PAYMENT_NAME[payment_name]['lang']['en_US'],
                'display_as' : PAYMENT_NAME[payment_name]['lang']['en_US'],
                'description' : PAYMENT_NAME[payment_name]['description']['en_US'],
                'provider_id' : self.id,
                'payment_code' : payment_name,
                'flow' : PAYMENT_FLOW[payment_name] if payment_name in PAYMENT_FLOW else 'direct',
            }
            nn_payment_method = novalnet_payment_method.create(val_dict)
            if self.env['res.lang'].sudo().with_context(active=True).search([('code','=','de_DE')]):
                nn_payment_method.update_field_translations('name',PAYMENT_NAME[payment_name]['lang'])
                nn_payment_method.update_field_translations('display_as',PAYMENT_NAME[payment_name]['lang'])
                nn_payment_method.update_field_translations('description',PAYMENT_NAME[payment_name]['description'])

    def _novalnet_make_request(self, endpoint, data=None, method='POST'):
        """ Make a request at novalnet endpoint.

        Note: self.ensure_one()

        :param str endpoint: The endpoint to be reached by the request
        :param dict data: The payload of the request
        :param str method: The HTTP method of the request
        :return The JSON-formatted content of the response
        :rtype: dict
        :raise: ValidationError if an HTTP error occurs
        """
        self.ensure_one()
        endpoint = f'/v2/{endpoint.strip("/")}'
        url = urls.url_join('https://payport.novalnet.de', endpoint)

        odoo_version = service.common.exp_version()['server_version']
        module_version = self.env.ref('base.module_payment_novalnet').installed_version

        base64_bytes = base64.b64encode(self.novalnet_key_password.encode("ascii"))
        encoded_data = base64_bytes.decode("ascii")
        Headers = {

            "Content-Type":"application/json",
            "Charset": "utf-8",
            "Accept":"application/json",
            "X-NN-Access-Key":encoded_data,

        }

        if 'merchant' not in data:
            data['merchant'] = {'signature':self.novalnet_public_key,'tariff':self.novalnet_tariff_selection.tariff_id}
        if 'custom' not in data:
            data['custom'] = {'lang':'EN' if self.env.context.get('lang') == 'en_US' else 'DE'}
        _logger.info(
            "novalnet payment transfer header "
            "\n%(values)s",
            { 'values': pprint.pformat(Headers)},
        )
        _logger.info(
            "novalnet payment transfer data "
            "\n%(values)s",
            {'values': pprint.pformat(data)},
        )
        try:
            response = requests.request(method, url, json=data, headers=Headers, timeout=60)
            result = response.json()
            if response.status_code == 204:
                return True  # returned no content
            if response.status_code not in [200]:
                error_msg = f"Error[{response.status_code}]"
                _logger.exception("Error from Novalnet: %s", result)
            response.raise_for_status()
        except requests.exceptions.RequestException:
            _logger.exception("Unable to communicate with novalnet: %s", url)
            raise ValidationError("novalnet: " + _("Could not establish the connection to the API."))
        _logger.info(
            "novalnet payment transfer response "
            "\n%(values)s",
            {'values': pprint.pformat(result)},
        )
        if result.get('result')['status'] == 'FAILURE':
            error_msg = f"Error[{result.get('result')['status']}] : {result.get('result')['status_code']} - {result.get('result')['status_text']}"
            raise ValidationError("novalnet: " + _(error_msg))
        return result
