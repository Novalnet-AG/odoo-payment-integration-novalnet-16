# Part of Odoo. See LICENSE file for full copyright and licensing details

from odoo import fields, models


class PaymentToken(models.Model):
    _inherit = 'payment.token'

    novalnet_payment_method = fields.Many2one('novalnet.payment.method', string="Novalnet payment method ")

    def _build_display_name(self, *args, should_pad=True, **kwargs):
        """ Override of `payment` to build the display name without padding.

        Note: self.ensure_one()

        :param list args: The arguments passed by QWeb when calling this method.
        :param bool should_pad: Whether the token should be padded or not.
        :param dict kwargs: Optional data.
        :return: The novlanet token name.
        :rtype: str
        """
        if self.provider_code != 'novalnet':
            return super()._build_display_name(*args, should_pad=should_pad, **kwargs)
        return super()._build_display_name(*args, should_pad=False, **kwargs)
