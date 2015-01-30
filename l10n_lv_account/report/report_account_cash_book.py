# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012 ITS-1 (<http://www.its1.lv/>)
#                       E-mail: <info@its1.lv>
#                       Address: <Vienibas gatve 109 LV-1058 Riga Latvia>
#                       Phone: +371 66116534
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

import time
from openerp.osv import osv
from openerp.report import report_sxw
from openerp.addons.l10n_lv_verbose import convert as convert

class report_account_cash_book(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(report_account_cash_book, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'turnover': self.turnover,
            'line_count': self.line_count,
            'time': time,
        })
        self.context = context

    def turnover(self, lines):
        inc = 0.0
        exp = 0.0
        for l in lines:
            if l.amount >= 0.0:
                inc += l.amount
            if l.amount < 0.0:
                exp += (l.amount * (-1.0))
        return {'income': inc, 'expense': exp}

    def line_count(self, lines):
        i_count = 0
        e_count = 0
        for line in lines:
            if line.amount >= 0.0:
                i_count += 1
            if line.amount < 0.0:
                e_count += 1
        i_count = convert(i_count).lower()
        e_count = convert(e_count).lower()
        return {'income': i_count, 'expense': e_count}

class cash_book(osv.AbstractModel):
    _name = 'report.l10n_lv_account.cash_book'
    _inherit = 'report.abstract_report'
    _template = 'l10n_lv_account.cash_book'
    _wrapped_report_class = report_account_cash_book

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: