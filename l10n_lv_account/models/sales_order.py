from odoo import models, fields, api

try:
    from num2words import num2words
except:
    num2words = None


class SaleOrder(models.AbstractModel):
    _inherit = 'account.invoice'

    @property
    def num2words(self):
        if num2words:
            return lambda n: num2words(n, lang=self.env.lang, to='currency')
        return None
