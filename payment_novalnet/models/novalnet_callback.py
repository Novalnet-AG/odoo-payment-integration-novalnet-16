# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging,pprint,datetime, json
from werkzeug import urls
from odoo.http import request
from odoo import _, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import format_amount

from odoo.addons.payment import utils as payment_utils
from odoo.addons.payment_novalnet.const import RESULT_CODES_MAPPING
from odoo.addons.payment_novalnet.controllers.main import PaymentNovalnetController

_logger = logging.getLogger(__name__)

_event_selection = [
                ('PAYMENT','PAYMENT'),
                ('TRANSACTION_CAPTURE','TRANSACTION_CAPTURE'),
                ('TRANSACTION_CANCEL','TRANSACTION_CANCEL'),
                ('TRANSACTION_REFUND','TRANSACTION_REFUND'),
                ('TRANSACTION_UPDATE','TRANSACTION_UPDATE'),
                ('CREDIT','CREDIT'),
                ('CHARGEBACK','CHARGEBACK'),
                ]

class NovalnetTransactionAmountStatus(models.Model):
    _name = 'novalnet.transaction.amount.status'
    _description = 'Novalnet transaction amount status'

    paid_amount = fields.Integer(default = 0)
    refund_amount = fields.Integer(default = 0)

class NovalnetCallback(models.Model):
    _name = 'novalnet.callback'
    _description = 'Novalnet callback'

    event_type = fields.Selection( selection=_event_selection, default='PAYMENT')
    parent_tid = fields.Char( string='NN Transaction ID of parent transaction ' )
    tid = fields.Char( string='NN Transaction ID ' )
    check_sum = fields.Char(string = 'checksum')

    transaction_id = fields.Many2one( string="Payment transaction", comodel_name='payment.transaction', readonly=True, domain='[("provider_id", "=", "provider_id")]', ondelete='restrict')

    callback_json = fields.Text(string="callback reqest from novalnet", required=True)
    is_done = fields.Boolean( string="Callback Done", help="Whether the callback has already been executed", default=False)

    def _process_credit(self,data):
        if self.event_type != 'CREDIT':
            return
        _logger.info("Entering in to Novalnt callback credit")
        converted_amount = payment_utils.to_major_currency_units( data.get('transaction')['amount'], self.transaction_id.currency_id )
        formatted_amount = format_amount(self.transaction_id.env, converted_amount, self.transaction_id.currency_id)
        _credit_msg = _(
            'Credit has been successfully received for the TID: %(parent_tid)s with amount on %(amount)s. Please refer PAID order details in our Novalnet Admin Portal for the TID: %(child_tid)s',
            parent_tid = self.parent_tid, child_tid= self.tid,amount=formatted_amount
        )

        self.transaction_id._log_message_on_linked_documents(_credit_msg)
        if self.transaction_id.novalnet_payment_method.payment_code in ['PREPAYMENT'] and self.transaction_id.novalnet_transaction_amount_status_id.paid_amount <= converted_amount:
            if self.transaction_id.novalnet_transaction_amount_status_id.paid_amount + data.get('transaction')['amount'] >=  converted_amount and self.transaction_id.state in ['pending','authorized'] :
                self.transaction_id._set_done()

        self.transaction_id.novalnet_transaction_amount_status_id.paid_amount+=data.get('transaction')['amount']
        self._send_callback_email(_credit_msg)
        self.is_done=True

    def _process_capture(self,data):
        if self.event_type != 'TRANSACTION_CAPTURE':
            return
        _logger.info("Entering in to Novalnt callback Capture")

        if self._check_shop_invoked_request(data):
            self.is_done=True
            _logger.info("Process already handled in the shop")
            return
        _capture_msg = _(
            'The transaction has been confirmed on %(datetime)s ',
            datetime = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        )
        self.transaction_id._log_message_on_linked_documents(_capture_msg)
        if self.transaction_id.state in ('authorized'):
            self.transaction_id._set_done()
        self._send_callback_email(_capture_msg)
        self.is_done=True

    def _process_cancel(self,data):
        if self.event_type != 'TRANSACTION_CANCEL':
            return
        _logger.info("Entering in to Novalnt callback Cancel")
        if self._check_shop_invoked_request(data):
            self.is_done=True
            _logger.info("Process already handled in the shop")
            return
        _cancel_msg = _(
            'The transaction has been canceled on %(datetime)s ',
            datetime = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        )
        self.transaction_id._log_message_on_linked_documents(_cancel_msg)
        if self.transaction_id.state in ('authorized'):
            self.transaction_id._set_canceled()
        self._send_callback_email(_cancel_msg)
        self.is_done=True

    def _check_shop_invoked_request(self,data):
        if 'custom' in data and  'shop_invoked' in data.get('custom'):
            return True
        return False


    def _process_refund(self,data):
        if self.event_type != 'TRANSACTION_REFUND':
            return
        _logger.info("Entering in to Novalnt callback Refund")
        _shop_invoked = self._check_shop_invoked_request(data)
        converted_amount = payment_utils.to_major_currency_units( data.get('transaction')['refund']['amount'], self.transaction_id.currency_id )
        formatted_amount = format_amount(self.transaction_id.env, converted_amount, self.transaction_id.currency_id)
        if self.transaction_id.refunds_count >0:
            refund_tx_from_source = self.env['payment.transaction'].search([('source_transaction_id', '=', self.transaction_id.id)])
            refund_tx_from_nn_tid = refund_tx_from_source.filtered(lambda tx: tx.provider_reference == self.tid)
            if _shop_invoked or (refund_tx_from_nn_tid and refund_tx_from_nn_tid[0].provider_reference != self.transaction_id.provider_reference):
                _logger.info("Callback received for already executed event")
                self.is_done=True
                return

        _refund_msg = _(
            'Refund has been initiated for the TID: %(parent_tid)s with the amount %(amount)s. The subsequent TID:%(child_tid)s for the refunded amount',
            parent_tid = self.parent_tid, amount=formatted_amount, child_tid= self.tid
        )
        self.transaction_id._log_message_on_linked_documents(_refund_msg)
        refund_tx = self.transaction_id._create_refund_transaction(amount_to_refund=converted_amount)
        if refund_tx:
            refund_tx.provider_reference = self.tid
            refund_tx._set_done()
        self._send_callback_email(_refund_msg)
        self.is_done=True

    def _process_chargeback(self,data):
        if self.event_type != 'CHARGEBACK':
            return
        _logger.info("Entering in to Novalnt callback Chargeback")
        converted_amount = payment_utils.to_major_currency_units( data.get('transaction')['amount'], self.transaction_id.currency_id )
        formatted_amount = format_amount(self.transaction_id.env, converted_amount, self.transaction_id.currency_id)
        _chargeback_msg = _(
            'Chargeback executed successfully for the TID: %(parent_tid)s amount: %(amount)s on %(datetime)s . The subsequent TID: %(child_tid)s',
            parent_tid = self.parent_tid, amount=formatted_amount, child_tid= self.tid, datetime = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        )
        self.transaction_id._log_message_on_linked_documents(_chargeback_msg)
        self._send_callback_email(_chargeback_msg)
        self.is_done=True

    def _process_update(self,data):
        if self.event_type != 'TRANSACTION_UPDATE':
            return
        _logger.info("Entering in to Novalnt callback TRANSACTION_UPDATE")
        converted_amount = payment_utils.to_major_currency_units( data.get('transaction')['amount'], self.transaction_id.currency_id )
        formatted_amount = format_amount(self.transaction_id.env, converted_amount, self.transaction_id.currency_id)

        update_type = data.get('transaction')['update_type']
        if update_type == 'AMOUNT_DUE_DATE':
            _update_msg = _(
                'The transaction has been updated with amount and due date',
            )
        elif update_type == 'DUE_DATE':
            _update_msg = _(
            'The transaction has been updated with a new due date',
            )
        elif update_type == 'AMOUNT':
            _update_msg = _(
                'Transaction amount %(amount)s has been updated successfully on %(datetime)s',
                amount=formatted_amount, datetime = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
            )
        elif update_type == 'STATUS':
            _update_msg = _(
                'Transaction updated successfully for the TID: %(parent_tid)s with the amount %(amount)s on %(datetime)s ',
                parent_tid = self.parent_tid, amount=formatted_amount, datetime = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
            )
            if 'status' not in data.get('transaction'):
                self.is_done=True
                raise ValidationError('Status Not found')
            state = RESULT_CODES_MAPPING[data.get('transaction')['status']]
            if self.transaction_id.state == state:
                self.is_done=True
                _logger.info(" Order already in the same state ")
                return
            if state == 'pending':
                self.transaction_id._set_pending()
            elif state == 'authorize':
                self.transaction_id._set_authorized()
            elif state == 'done':
                self.transaction_id._set_done()
            elif state == 'cancel':
                self.transaction_id._set_canceled()
        self.transaction_id._log_message_on_linked_documents(_update_msg)
        self._send_callback_email(_update_msg)
        self.is_done=True

    def _send_callback_email(self,comment):
        if not self.transaction_id.provider_id.novalnet_webhook_email:
            return
        mail_template = request.env.ref('payment_novalnet.novalnet_callback_notification').sudo()
        _subject = 'Novalnet odoo callback script'
        _email_to = self.transaction_id.provider_id.novalnet_webhook_email
        _email_from = "no-reply@odoo.com"
        _values={'comments': comment}
        mail_template.with_context(_values).send_mail(self.transaction_id.id, email_values={'email_to': _email_to, 'email_from': _email_from, 'subject': _subject,})

    def _validate_callback(self):
        if self.event_type == 'PAYMENT':
            self.is_done= True
            return

        data = json.loads(self.callback_json)
        _logger.info(data)
        _logger.info(self.event_type)
        self.tid = data.get('event')['tid']
        if self.event_type == 'CREDIT':
            self._process_credit(data)
        elif self.event_type == 'TRANSACTION_CAPTURE':
            self._process_capture(data)
        elif self.event_type == 'TRANSACTION_CANCEL':
            self._process_cancel(data)
        elif self.event_type == 'TRANSACTION_REFUND':
            self._process_refund(data)
        elif self.event_type == 'CHARGEBACK':
            self._process_chargeback(data)
        elif self.event_type == 'TRANSACTION_UPDATE':
            self._process_update(data)
