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
from openerp import pooler

class report_account_cash_order(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(report_account_cash_order, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'get_analytic_account': self.get_analytic_account,
            'get_id': self.get_id
        })
        self.context = context  

    def get_analytic_account(self, line):
        account = ''
        acc_list = []
        if line.journal_entry_id:
            for l in line.journal_entry_id.line_id:
                if l.analytic_account_id and l.analytic_account_id not in acc_list:
                    acc_list.append(l.analytic_account_id)
        if acc_list:
            account = acc_list.join(', ')
        return account

    def get_id(self, partner):
        res = False
        if partner.is_company:
            if hasattr(partner, 'company_registry'):
                res = partner.company_registry
            if not res:
                res = partner.vat
        if (not partner.is_company) and hasattr(partner, 'identification_id'):
            res = partner.identification_id
        return res

class cash_order(osv.AbstractModel):
    _name = 'report.l10n_lv_account.cash_order'
    _inherit = 'report.abstract_report'
    _template = 'l10n_lv_account.cash_order'
    _wrapped_report_class = report_account_cash_order

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
