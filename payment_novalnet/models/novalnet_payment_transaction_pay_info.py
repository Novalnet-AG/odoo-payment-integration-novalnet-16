# -*- coding: utf-8 -*-

from odoo.osv import expression
from odoo import fields, models


class NovalnetPaymentTransactionBank(models.Model):
    _name = 'novalnet.payment.transaction.bank'
    _description = 'Novalnet bank details for a transaction'

    account_holder = fields.Char(string="Account holder name")
    bank_name = fields.Char(string="Name of the bank that need to be transferred")
    bank_place = fields.Char(string="Place of the bank that need to be transferred")
    bic = fields.Char(string="BIC")
    iban = fields.Char(string="IBAN")

class NovalnetPaymentTransactionStore(models.Model):
    _name = 'novalnet.payment.transaction.store'
    _description = 'Novalnet store details for a transaction'

    transaction_id = fields.Many2one(
            string="Store details to which customer has to transfer the transaction amount, Applies only for cashpayment ", comodel_name='payment.transaction', readonly=True,
            domain='[("provider_id", "=", "provider_id")]', ondelete='restrict')
    city = fields.Char(string="City of the store")
    country_code = fields.Char(string="Country Code of the store")
    store_name = fields.Char(string="Store name")
    street = fields.Char(string="Street")
    zip = fields.Char(string="zip")
