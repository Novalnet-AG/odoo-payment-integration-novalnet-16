from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import PaymentPortal
import logging,pprint,json
from odoo import _
from odoo.exceptions import UserError,ValidationError
_logger = logging.getLogger(__name__)


class PaymentNovalnetController(http.Controller):
    _direct_simulate_payment_url = '/payment/novalnet/simulate_payment'
    _return_url = '/payment/novalnet/return'
    _webhook_url = '/payment/novalnet/webhook'

    @http.route(_direct_simulate_payment_url, type='json', auth='public')
    def novalnet_simulate_payment(self, **data):
        """ Simulate the response of a payment request.

        :param dict data: The simulated notification data.
        :return: None
        """
        _logger.info(data)
        request.env['payment.transaction'].sudo()._handle_notification_data('novalnet', data)

    @http.route(_webhook_url, type='json', auth='public',methods=['POST'], csrf=False,website=True)
    def novalnet_webhook(self, **data):
        data = json.loads(request.httprequest.data)
        _logger.info("notification received from Novalnet with data:\n%s", pprint.pformat(data))
        payment_provider = request.env['payment.provider'].sudo().search([('code','=','novalnet')])

        if not set(('event','result','transaction')) <=  set(data):
            raise ValidationError(_("webhook necessary information not found"))
        tid = data.get('event')['parent_tid'] if 'parent_tid' in  data.get('event') else data.get('event')['tid']
        event_type, checksum =  data.get('event')['type'], data.get('event')['checksum']

        if 'order_no' not in data.get('transaction'):
            raise ValidationError(_("Order number not found"))

        transaction_info = request.env['payment.transaction'].sudo().search([('reference','=',data.get('transaction')['order_no'])])
        if not transaction_info:
            raise ValidationError(_("Could not found order number"))
        transaction_info._handle_notification_data('novalnet', {'nn_tid':tid, 'event_type':event_type, 'check_sum': checksum, 'nn_status': data.get('result')['status'], 'nn_status_text': data.get('result')['status_text'], 'reference':transaction_info.reference})


    @http.route(_return_url, type='http', auth='public')
    def novalnet_return_payment(self, **data):
        _logger.info(pprint.pformat(data))

        if not set(('status','status_text','status_code')) <=  set(data):
            return request.render('payment_novalnet.novalnet_redirect_failure', {
                'failure_message': _('Unknown error occured please try after some time')
            })

        _nn_status, _nn_status_text = data['status'] , data['status_text']

        if not set(('txn_secret','tid','checksum')) <=  set(data):
            return request.render('payment_novalnet.novalnet_redirect_failure', {
                'failure_message': _nn_status_text
            })

        transaction_info = request.env['payment.transaction'].sudo().search([('novalnet_txn_secret','=',data['txn_secret'])])
        if not transaction_info:
            return request.render('payment_novalnet.novalnet_redirect_failure', {
                'failure_message': _('Could not found transaction')
            })
        transaction_info._handle_notification_data('novalnet', {'nn_tid':data['tid'],'nn_status': _nn_status, 'nn_status_text': _nn_status_text, 'reference':transaction_info.reference})
        return request.redirect('/payment/status')
