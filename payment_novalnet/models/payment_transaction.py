# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging, pprint, datetime, socket
from werkzeug import urls
from odoo.http import request
from odoo import _, fields, models, service
from odoo.exceptions import UserError, ValidationError
from odoo.tools import format_amount
from  ipaddress import ip_interface

from datetime import date
from odoo.addons.payment import utils as payment_utils
from odoo.addons.payment_novalnet.const import RESULT_CODES_MAPPING
from odoo.addons.payment_novalnet.controllers.main import PaymentNovalnetController
from odoo.tools.misc import get_lang

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    novalnet_invoice_ref = fields.Char(string="Transaction reference for invoice payment")
    novalnet_payment_method = fields.Many2one('novalnet.payment.method', string="Novalnet payment method ")
    novalnet_txn_secret = fields.Char(string="Transaction secret is a temporary identifier for the payment types with the redirect flow and it travels across the transaction, useful in verifying the payment result")


    novalnet_transaction_amount_status_id = fields.Many2one('novalnet.transaction.amount.status', string=" Novalnet transaction amount status ")
    novalnet_bank_account = fields.Many2one('novalnet.payment.transaction.bank', string=" Bank details to which customer has to transfer the transaction amount ")

    novalnet_callback_ids = fields.One2many(string="Novalnet transaction callback details", comodel_name='novalnet.callback', inverse_name='transaction_id')

    novalnet_nearest_store_ids = fields.One2many(string="Store details to which customer has to transfer the transaction amount, Applies only for cashpayment", comodel_name='novalnet.payment.transaction.store', inverse_name='transaction_id')

    novalnet_multibanco_payment_reference = fields.Char(string="The payment reference for the Multibanco payment type. Using this reference, the customer pays in online portal or in the Multibanco ATM to complete the purchase")

    novalnet_multibanco_service_supplier_id = fields.Char(string="Service supplier ID from Multibanco")
    novalnet_due_date = fields.Char(string="Novalnet due date for Invoice, Prepayment, DIRECT_DEBIT_SEPA, GUARANTEED_INVOICE, GUARANTEED_DIRECT_DEBIT_SEPA, cashpayment")


    def _send_capture_request(self):
        super()._send_capture_request()
        if self.provider_code != 'novalnet':
            return

        if not self.provider_reference :
            raise ValidationError(_("Could not find Novalnet parent transaction "))
        capture_payload = {
                            'transaction' : {
                                    'tid' : self.provider_reference
                                    },
                            'custom' : {
                                    'shop_invoked' : 1
                            }
                         }
        _portal_comments = _(
            'The transaction has been confirmed on %(datetime)s ',
            datetime = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        )

        capture_response = self.provider_id._novalnet_make_request("transaction/capture",data=capture_payload)
        self._log_message_on_linked_documents(_portal_comments)
        self._handle_notification_data('novalnet', {'nn_tid' : self.provider_reference,'portal_comments':_portal_comments})


    def _send_payment_request(self):
        """ Override of payment to simulate a payment request.

        Note: self.ensure_one()

        :return: None
        """
        super()._send_payment_request()
        if self.provider_code != 'novalnet':
            return

        if not self.token_id:
            raise UserError("novalnet: " + _("The transaction is not linked to a token."))

        if self.operation !='offline':
            return
        processing_val = self._get_processing_values()
        self._handle_notification_data('novalnet', processing_val)

    def _send_void_request(self):
        super()._send_void_request()
        if self.provider_code != 'novalnet':
            return

        void_payload = {
                            'transaction' : {
                                    'tid' : self.provider_reference
                                    },
                            'custom' : {
                                    'shop_invoked' : 1
                            }
                         }
        _portal_comments = _(
            'The transaction has been canceled on %(datetime)s ',
            datetime = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        )
        void_response = self.provider_id._novalnet_make_request("transaction/cancel",data=void_payload)
        self._log_message_on_linked_documents(_portal_comments)
        self._handle_notification_data('novalnet', {'nn_tid' : self.provider_reference,'portal_comments':_portal_comments,'nn_status':'DEACTIVATED'})

    def _execute_callback(self):
        if self.provider_code != 'novalnet':
            return
        for nn_callback in self.novalnet_callback_ids.filtered(lambda t: not t.is_done):
            nn_callback._validate_callback()



    def _send_refund_request(self, amount_to_refund=None):
        refund_tx = super()._send_refund_request(amount_to_refund)
        if self.provider_code != 'novalnet':
            return refund_tx
        converted_amount = payment_utils.to_minor_currency_units( refund_tx.amount, refund_tx.currency_id )
        refund_payload = {
                            'transaction' : {
                                    'tid' : self.provider_reference,
                                    'amount' : abs(converted_amount),
                                    'reason' : f'Refund for payment transaction with reference/{refund_tx.reference}',
                                    },
                            'custom' : {
                                    'shop_invoked' : 1
                            }
                         }
        refund_response = self.provider_id._novalnet_make_request("transaction/refund",data=refund_payload)
        formatted_amount = format_amount(refund_tx.env, refund_tx.amount, refund_tx.currency_id)
        notification_data = {}
        if 'transaction' not in refund_response or 'tid' not in refund_response.get('transaction'):
            notification_date={'nn_status': refund_response.get('result')['status'], 'nn_status_text': refund_response.get('result')['status_text']}
        elif 'refund' in refund_response.get('transaction') and 'tid' in refund_response.get('transaction')['refund']:
            _portal_comments = _(
                'Refund has been initiated for the TID: %(parent_tid)s with the amount %(amount)s. New TID:%(child_tid)s for the refunded amount',
                parent_tid = refund_response.get('transaction')['tid'], amount=formatted_amount, child_tid= refund_response.get('transaction')['refund']['tid']
            )
            refund_tx._log_message_on_linked_documents(_portal_comments)
            notification_data = {'nn_tid' : refund_response.get('transaction')['refund']['tid'], 'portal_comments':_portal_comments, 'nn_status': refund_response.get('transaction')['status'] }
        else:
            _portal_comments = _(
                'Refund has been initiated for the TID:%(parent_tid)s with the amount %(amount)s',
                parent_tid = refund_response.get('transaction')['tid'], amount=formatted_amount
            )
            notification_data = {'nn_tid' : refund_response.get('transaction')['tid'], 'portal_comments':_portal_comments,'nn_status': refund_response.get('transaction')['status']}
            if refund_response.get('transaction')['status'] == 'DEACTIVATED': refund_tx= self
            refund_tx._log_message_on_linked_documents(_portal_comments)
        refund_tx._handle_notification_data('novalnet', notification_data)
        return refund_tx




    def _get_specific_processing_values(self, processing_values):
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != 'novalnet':
            return res
        self.novalnet_payment_method = self.env['novalnet.payment.method'].search([('id', '=', request.params.get('providerPaymentMethodId'))])

        processing_values.update(self._novalnet_prepare_tokenized_params())
        if  not self.novalnet_payment_method:
            raise ValidationError(_("Could not find payment please try any other payment "))

        self._log_message_on_linked_documents(_(
            "Transaction initiated with %(provider_name)s payment type %(payment_type)s for %(ref)s.",
            provider_name=self.provider_id.name,payment_type=self.novalnet_payment_method.name, ref=self.reference
        ))
        payload = self._novalnet_prepare_payment_request(processing_values)

        endpoint = self._novalnet_prepare_end_point()
        payment_response = self.provider_id._novalnet_make_request(endpoint,data=payload)

        if self.operation in ['online_direct','online_token','offline']:
            if 'transaction' not in  payment_response or 'tid' not in payment_response.get('transaction'):
                raise ValidationError(_("Invalid transaction"))
            self.provider_reference = payment_response.get('transaction')['tid']
            return {'nn_tid':str(payment_response.get('transaction')['tid'])}
        elif self.operation in ['online_redirect']:
            if 'transaction' not in  payment_response or 'txn_secret' not in payment_response.get('transaction') or 'redirect_url' not in payment_response.get('result'):
                raise ValidationError(_("Could not redirect to acquirer, please try again later"))
            self.novalnet_txn_secret = payment_response.get('transaction')['txn_secret']
            return {'redirect_url': payment_response.get('result')['redirect_url']}

    def _novalnet_prepare_end_point(self):
        if not self.novalnet_payment_method: return
        if self.novalnet_payment_method.capture_manually:
            return "authorize"
        return "payment"
    def _novalnet_prepare_tokenized_params(self):
        payload = {'paydata':request.params.get('paydata')}
        if self.token_id:
            payload = {'paydata':{'token':self.token_id.provider_ref}}
            self.novalnet_payment_method =  self.token_id.novalnet_payment_method
        return payload

    def _get_specific_rendering_values(self, processing_values):
        return processing_values

    def _novalnet_prepare_payment_request(self,processing_values):
        user_lang = self.env.context.get('lang')
        base_url = self.provider_id.get_base_url()
        customer = self._create_customer_payload()
        transactionPayload = self._create_transaction_payload(processing_values)
        return {
                'customer':customer,
                 'custom': {
                        'lang': 'EN' if user_lang == 'en_US' else 'DE'
                    },
                 'transaction' : transactionPayload
            }
    def _initiate_transaction_callback(self,notification_data):
        nn_ip = ip_interface(socket.gethostbyname('pay-nn.de'))
        request_ip = ip_interface(payment_utils.get_customer_ip_address())
        if nn_ip != request_ip and not self.provider_id.novalnet_webhook_testing:
            raise ValidationError(_('Unauthorized request from IP %s', payment_utils.get_customer_ip_address()) )

        if 'event_type' not in notification_data or 'check_sum' not in notification_data:
            raise ValidationError(_("Could not initiate callback"))

        self.write({
            'novalnet_callback_ids': [(0, 0,  {
                                    'event_type' : notification_data.get('event_type'),
                                    'parent_tid' : notification_data.get('nn_tid'),
                                    'check_sum' : notification_data.get('check_sum'),
                                    'transaction_id' : self.id,
                                    'callback_json' : request.httprequest.data
                                    })],
        })

    def _create_transaction_payload(self,processing_values):

        odoo_version = service.common.exp_version()['server_version']
        module_version = self.env.ref('base.module_payment_novalnet').installed_version
        converted_amount = payment_utils.to_minor_currency_units( self.amount, self.currency_id )
        payData = processing_values['paydata']
        transaction_payload =  {
            'payment_type': self.novalnet_payment_method.payment_code,
            'amount'  : converted_amount,
            'system_name': f'Odoo/{odoo_version}',
            'system_version': f'V/{module_version}',
            'currency'  : self.currency_id.name,
            'order_no'  : self.reference,
            'test_mode' : 1 if self.provider_id.state == 'test' else 0
        }
        if processing_values['paydata']: transaction_payload['payment_data'] = processing_values['paydata']
        if request.params.get('tokenization_requested'): transaction_payload['create_token'] =1
        if self.novalnet_payment_method.enforce_3d: transaction_payload['enforce_3d'] = 1
        if self.novalnet_payment_method.payment_term_id:
            ipt = self.env.ref('account.account_payment_term_immediate', False)

            if ipt and ipt.sudo().id != self.novalnet_payment_method.payment_term_id.id:

                sales_orders = self.sale_order_ids.filtered(lambda so: so.state in ['draft'])
                sales_orders.write({'payment_term_id':self.novalnet_payment_method.payment_term_id})
                terms = self.novalnet_payment_method.payment_term_id._compute_terms(
                        date_ref=self.novalnet_payment_method.payment_term_id.example_date,
                        currency=self.currency_id,
                        company=self.env.company,
                        tax_amount=0,
                        tax_amount_currency=0,
                        untaxed_amount=self.amount,
                        untaxed_amount_currency=self.amount,
                        sign=1)
                due_date = date.today().strftime("%Y-%m-%d")
                for balance_val in terms:
                    due_date = balance_val['date'].strftime("%Y-%m-%d")
                transaction_payload['due_date'] = due_date
        if self.operation in ['online_redirect']:
            base_url = self.provider_id.get_base_url()
            transaction_payload['return_url'] = urls.url_join(base_url, PaymentNovalnetController._return_url)
        return transaction_payload

    def _create_customer_payload(self):
        """ Create and return a Customer.

        :return: The Customer
        :rtype: dict
        """
        first_name, last_name = payment_utils.split_partner_name(self.partner_id.name)
        customer = {
                'first_name': first_name,
                'last_name': last_name,
                'customer_ip': payment_utils.get_customer_ip_address(),
                'customer_no': self.partner_id.id,
                'billing': {
                        'company': self.partner_id.company_name or None,
                        'city': self.partner_city or None,
                        'country_code': self.partner_country_id.code or None,
                        'street': self.partner_address or None,
                        'zip': self.partner_zip or None,
                        'state': self.partner_state_id.name or None,
                    },
                'shipping': {'same_as_billing' : 1},
                'email': self.partner_email or None,
                'name': self.partner_name,
                'phone': self.partner_phone or None,
            }
        order= None
        if len(self.sale_order_ids)==1:
            order = self.sale_order_ids[0]
        if order and self.partner_id.id != order.partner_shipping_id.id:
            shipping_first_name, shipping_last_name = payment_utils.split_partner_name(order.partner_shipping_id.name)
            customer['shipping'] = {
                                'first_name': shipping_first_name,
                                'last_name': shipping_last_name,
                                'email': order.partner_shipping_id.email,
                                'company':order.partner_shipping_id.company_name or '' ,
                                'street': order.partner_shipping_id.street,
                                'city': order.partner_shipping_id.city,
                                'zip': order.partner_shipping_id.zip,
                                'country_code': order.partner_shipping_id.country_id.code,
                                'tel': order.partner_shipping_id.phone,
                                'mobile': order.partner_shipping_id.mobile,
                                }
        if 'birth_date' in request.params and request.params.get('birth_date'): customer['birth_date'] = request.params.get('birth_date')
        return customer

    def _get_tx_from_notification_data(self, provider_code, notification_data):
        """ Override of payment to find the transaction based on dummy data.

        :param str provider_code: The code of the provider that handled the transaction
        :param dict notification_data: The dummy notification data
        :return: The transaction if found
        :rtype: recordset of `payment.transaction`
        :raise: ValidationError if the data match no transaction
        """
        tx = super()._get_tx_from_notification_data(provider_code, notification_data)
        if provider_code != 'novalnet' or len(tx) == 1:
            return tx

        reference = notification_data.get('reference')
        tx = self.search([('reference', '=', reference), ('provider_code', '=', 'novalnet')])
        if not tx:
            raise ValidationError(
                "Demo: " + _("No transaction found matching reference %s.", reference)
            )
        return tx
    def _create_payment_data(self,notification_data):
        payment_data = {}
        if notification_data['providerPaymentMethodId'].payment_code not in ['CREDITCARD']: return payment_data
        if notification_data['providerPaymentMethodId'].payment_code == 'CREDITCARD':
            payment_data['payment_data'] = {'pan_hash':notification_data['hash'],'unique_id':notification_data['unique_id']}
        return payment_data


    def _validate_create_multibanco_payment_info(self, _partner_payment_reference, _service_supplier_id):
        if not _partner_payment_reference or not _service_supplier_id: return
        self.novalnet_multibanco_payment_reference = _partner_payment_reference
        self.novalnet_multibanco_service_supplier_id = _service_supplier_id

    def _validate_create_store_info_for_cashpayment(self,_nearest_stores):
        if len(_nearest_stores)<0: return

        for key,val in _nearest_stores.items():
            self.write({
                'novalnet_nearest_store_ids': [(0, 0,  val)],
            })



    def _validate_create_bank_account(self,_bank_details):
        if not set(('account_holder','bank_name','bank_place','bic','iban')) <=  set(_bank_details): return
        bank_info = self.env['novalnet.payment.transaction.bank'].search([('account_holder', '=', _bank_details['account_holder']),('bank_name', '=', _bank_details['bank_name']),('bic', '=', _bank_details['bic']),('iban', '=', _bank_details['iban']),('bank_place', '=', _bank_details['bank_place'])])

        if bank_info:
            self.novalnet_bank_account = bank_info.id
        else:
            bank_info = self.env['novalnet.payment.transaction.bank'].create({'account_holder':_bank_details['account_holder'], 'bank_place':_bank_details['bank_place'], 'bank_name':_bank_details['bank_name'], 'bic':_bank_details['bic'], 'iban':_bank_details['iban']})
            self.novalnet_bank_account = bank_info.id

    def _set_pending(self):
        if self.provider_code != 'novalnet':
            return
        lang = self.partner_id.lang or get_lang(self.env).code
        for order in self.sale_order_ids:
            order.write({'note': order.note + ' \n ' + self.env['ir.ui.view'].sudo().with_context(lang=lang)._render_template(
                        "payment_novalnet.novalnet_payment_information",
                        {'payment_tx_id': self.with_context(lang=lang), 'order': order}
                    )})
        super()._set_pending()

    def _set_authorized(self):
        if self.provider_code != 'novalnet':
            return
        lang = self.partner_id.lang or get_lang(self.env).code
        for order in self.sale_order_ids:
            order.write({'note': order.note + ' \n ' + self.env['ir.ui.view'].with_context(lang=lang)._render_template(
                        "payment_novalnet.novalnet_payment_information",
                        {'payment_tx_id': self.with_context(lang=lang), 'order': order}
                    )})
        super()._set_authorized()


    def _set_done(self):
        super()._set_done()
        if self.provider_code != 'novalnet':
            return
        lang = self.partner_id.lang or get_lang(self.env).code
        for order in self.sale_order_ids:
            order.write({'note': order.note + ' \n ' + self.env['ir.ui.view'].sudo().with_context(lang=lang)._render_template(
                        "payment_novalnet.novalnet_payment_information",
                        {'payment_tx_id': self.with_context(lang=lang), 'order': order}
                    )})



    def _process_notification_data(self, notification_data):
        """ Override of payment to process the transaction based on dummy data.

        Note: self.ensure_one()

        :param dict notification_data: The dummy notification data
        :return: None
        :raise: ValidationError if inconsistent data were received
        """
        super()._process_notification_data(notification_data)
        if self.provider_code != 'novalnet':
            return

        if 'event_type' in notification_data:
            self._initiate_transaction_callback(notification_data)
            if notification_data.get('event_type') == 'PAYMENT' and self.state !='draft':
                _logger.info(_("Callback received for event type %s but communication failure not found" , notification_data.get('event_type')))
                return
            elif notification_data.get('event_type') != 'PAYMENT':
                return

        if 'nn_status' in notification_data and notification_data.get('nn_status') == 'FAILURE':
            self._set_error(_("%s", notification_data.get('nn_status_text')))
            return
        elif 'nn_status' in notification_data and notification_data.get('nn_status') == 'DEACTIVATED':
            self._set_canceled()
            return

        if 'nn_tid' not in notification_data:
            raise ValidationError(_("Invalid transaction"))





        retrieve_transaction = self.provider_id._novalnet_make_request("transaction/details",data={'transaction':{'tid':notification_data.get('nn_tid')},'custom': { 'lang': self.env.context.get('lang')}})

        if 'transaction' not in  retrieve_transaction or not retrieve_transaction.get('transaction')['tid']:
            raise ValidationError(_("Invalid transaction"))
        if self.tokenize and 'payment_data' in  retrieve_transaction.get('transaction') and 'token' in retrieve_transaction.get('transaction')['payment_data'] and retrieve_transaction.get('transaction')['payment_data']['token']:
            _token = retrieve_transaction.get('transaction')['payment_data']['token']
            if self.novalnet_payment_method.payment_code == 'CREDITCARD':
                _token_name = ("%s - %s" % (retrieve_transaction.get('transaction')['payment_data']['card_number'], retrieve_transaction.get('transaction')['payment_data']['card_brand'] ))
            elif self.novalnet_payment_method.payment_code in ['DIRECT_DEBIT_SEPA','GUARANTEED_DIRECT_DEBIT_SEPA']:
                _token_name = ("%s" % (retrieve_transaction.get('transaction')['payment_data']['iban'] ))
            self._novalnet_tokenize_from_notification_data(_token, _token_name)

        state = RESULT_CODES_MAPPING[retrieve_transaction.get('transaction')['status']]
        converted_amount = payment_utils.to_minor_currency_units( self.amount, self.currency_id )

        if 'bank_details' in retrieve_transaction.get('transaction'): self._validate_create_bank_account(retrieve_transaction.get('transaction')['bank_details'])
        if 'nearest_stores' in retrieve_transaction.get('transaction'): self._validate_create_store_info_for_cashpayment(retrieve_transaction.get('transaction')['nearest_stores'])
        if set(('partner_payment_reference','service_supplier_id')) <=  set( retrieve_transaction.get('transaction') ): self._validate_create_multibanco_payment_info( retrieve_transaction.get('transaction')['partner_payment_reference'], retrieve_transaction.get('transaction')['service_supplier_id'])

        self.provider_reference = self.provider_reference or notification_data.get('nn_tid')
        if 'due_date'  in  retrieve_transaction.get('transaction'): self.novalnet_due_date =  retrieve_transaction.get('transaction')['due_date']
        if 'invoice_ref' in retrieve_transaction.get('transaction'): self.novalnet_invoice_ref = retrieve_transaction.get('transaction')['invoice_ref'] or ''

        _transaction_amount_dict = {
                                'paid_amount' : converted_amount,
                                }

        if state == 'pending':
            _transaction_amount_dict['paid_amount'] = 0
            if self.novalnet_payment_method.payment_code != 'PREPAYMENT' and retrieve_transaction.get('transaction')['status_code'] ==100:
                state= 'done'
        self.novalnet_transaction_amount_status_id =  self.env['novalnet.transaction.amount.status'].create(_transaction_amount_dict)

        if state == 'pending':
            self._set_pending()
        elif state == 'authorize':
            self._set_authorized()
        elif state == 'done':
            self._set_done()
            if self.operation == 'refund':
                self.env.ref('payment.cron_post_process_payment_tx')._trigger()
        elif state == 'cancel':
            self._set_canceled()
        else:  # Simulate an error state.
            self._set_error(_("You selected the following novalnet payment status: %s", state))



    def _novalnet_tokenize_from_notification_data(self, _token, _token_name):
        self.ensure_one()

        token = self.env['payment.token'].create({
            'provider_id': self.provider_id.id,
            'payment_details': _token_name,
            'partner_id': self.partner_id.id,
            'provider_ref': _token,
            'novalnet_payment_method': self.novalnet_payment_method.id,
            'verified': True,
        })
        self.write({
            'token_id': token,
            'tokenize': False,
        })
        _logger.info(
            "Created token with id %s for partner with id %s.", token.id, self.partner_id.id
        )
