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

    @api.multi
    def invoice_print(self):
        """ Print the invoice and mark it as sent, so that we can see more
            easily the next step of the workflow
        """
        return self.env.ref('l10n_lv_account.action_report_docket_invoice').report_action(self)
