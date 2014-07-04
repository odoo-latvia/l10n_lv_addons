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
from openerp.

class report_account_cash_order(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(report_account_cash_order, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'abs_amount': self.abs_amount, 
           # 'time': time,
           # 'cr':cr,
           # 'uid': uid
        })
        self.context = context
        
    def abs_amount(self, amount):
        return abs(amount)

class cash_order(osv.AbstractModel):
    _name = 'report.l10n_lv_account.cash_order'
    _inherit = 'report.abstract_report'
    _template = 'l10n_lv_account.cash_order'
    _wrapped_report_class = report_account_cash_order

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
