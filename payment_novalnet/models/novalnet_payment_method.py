# -*- coding: utf-8 -*-

from odoo.osv import expression
from odoo import fields, models


class NovalnetPaymentMethod(models.Model):
    _name = 'novalnet.payment.method'
    _description = 'Novalnet payment method'
    _order = "sequence, id"

    name = fields.Char(translate=True,string="Name")
    display_as = fields.Text(
        string="Displayed as", help="Novalnet payment types for customers",
        translate=True)
    description = fields.Text(
        string="Description", help="Description of the novalnet payment types for customers",
        translate=True)
    sequence = fields.Integer()
    provider_id = fields.Many2one('payment.provider', string='provider',readonly=True)
    payment_code = fields.Char(string="Payment code",readonly=True)
    payment_icon_ids = fields.Many2many('payment.icon', string='Supported Payment Icons')
    active = fields.Boolean(default=True,readonly=True,invisible=True)
    flow = fields.Selection( string="Operation",selection=[
                                        ('redirect', "Online payment with redirection"),
                                        ('direct', "Online direct payment"),
                                    ],
                                    readonly=True,default='direct',
                                    index=True)
    shop_active_status = fields.Boolean(string="Status on shop", default=True)
    capture_manually = fields.Boolean(string="Capture manually from shop", default=False)
    enforce_3d = fields.Boolean(string="Enforce 3D Secure payments outside the EU", default=False)
    country_ids = fields.Many2many('res.country', string='Country Availability')
    company_id = fields.Many2one(related="provider_id.company_id")

    payment_term_id = fields.Many2one(
        comodel_name='account.payment.term',
        string="Payment Terms",
        compute='_compute_payment_term_id',
        store=True, readonly=False, precompute=True, check_company=True,  # Unrequired company
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", help = 'Novalnet due date')

    journal_id = fields.Many2one(
        'account.journal', string="Journal",
        compute='_compute_journal_id', inverse='_inverse_journal_id',
        domain="[('type', '=', 'bank'), ('company_id', '=', company_id)]")

    def _compute_payment_term_id(self):
        pt = self.env.ref('account.account_payment_term_immediate', False)
        for novalnet_payment_method in self:
            if novalnet_payment_method.payment_code in ('INVOICE','PREPAYMENT','CASHPAYMENT','GUARANTEED_INVOICE'):
                pt = self.env.ref('payment_novalnet.novalnet_invoice_account_payment_term_14days', False)
            novalnet_payment_method.payment_term_id = pt

    def _compute_journal_id(self):
        for novalnet_method in self:
            payment_method = self.env['account.payment.method.line'].search([
                ('journal_id.company_id', '=', novalnet_method.company_id.id),
                ('code', '=', novalnet_method._get_journal_method_code()),
            ], limit=1)
            if payment_method:
                novalnet_method.journal_id = payment_method.journal_id
            else:
                novalnet_method.journal_id = False

    def _get_journal_method_code(self):
        self.ensure_one()
        return f'novalnet_{self.payment_code}'
