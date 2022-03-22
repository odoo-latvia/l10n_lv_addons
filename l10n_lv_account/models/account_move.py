# -*- encoding: utf-8 -*-
##############################################################################
#
#    Part of Odoo.
#    Copyright (C) 2021 Ozols Grupa (<http://www.ozols.lv/>)
#                       E-mail: <info@ozols.lv>
#                       Address: <Vienibas gatve 109 LV-1058 Riga Latvia>
#                       Phone: +371 67289211
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import models, fields, api

try:
    from num2words import num2words
except:
    num2words = None


class AccountMove(models.Model):
    _inherit = 'account.move'

    @property
    def num2words(self):
        if num2words:
            lg = self.env.context.get('lang', 'en')
            if not lg:
                lg = 'en'
            if '_' in lg:
                lg = self.env.lang.split('_')[0]
            return lambda n: num2words(n, lang=lg, to='currency')
        return None

    def action_invoice_print(self):
        res = super(AccountMove, self).invoice_print()
        res = self.env.ref('l10n_lv_account.action_report_docket_invoice').report_action(self)
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
