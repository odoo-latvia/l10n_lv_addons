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
from openerp.report import report_sxw
from openerp.osv import osv
from openerp.tools.translate import _

class report_hr_expense_account(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(report_hr_expense_account, self).__init__(cr, uid, name, context=context)
        self.result_exp = []
        self.result_bank = []
        self.localcontext.update({
            'time': time,
            'cr':cr,
            'uid': uid,
            'lines': self.lines,
            'bank_lines': self.bank_lines,
            'move_lines': self.move_lines
        })
        self.context = context

    def move_lines(self, bank_statement_lines):
        line_list = []
        for bsl in bank_statement_lines:
            for ml in bsl.journal_entry_id.line_id:
                if ml not in line_list:
                    line_list.append(ml)
        return line_list

    def bank_lines(self, form, ids=[]):
        bank_obj = self.pool.get('account.bank.statement.line')
        if form:
            self.result_bank = bank_obj.browse(self.cr, self.uid, form['bank_statement_line_ids'])
        else:
            expense_obj = self.pool.get('hr.expense.expense')
            exp_ids = self.localcontext.get('active_ids',[])
            partners = []
            for exp in expense_obj.browse(self.cr, self.uid, exp_ids):
                if exp.employee_id.address_home_id:
                    partners.append(exp.employee_id.address_home_id.id)
            bst_ids = bank_obj.search(self.cr, self.uid, [('partner_id','in',partners)])
            self.result_bank = bank_obj.browse(self.cr, self.uid, bst_ids)
        return self.result_bank

    def lines(self, form, ids=[]):
        expense_obj = self.pool.get('hr.expense.expense')
        exp_ids = self.localcontext.get('active_ids',[])
        if form:
            exp_ids = expense_obj.search(self.cr, self.uid, [('date','>=',form['date_from']),('date','<=',form['date_to']),('employee_id','=',form['employee_id']),('account_move_id','!=',False)])
        self.result_exp = expense_obj.browse(self.cr, self.uid, exp_ids)
        return self.result_exp

class hrea_report(osv.AbstractModel):
    _name = 'report.l10n_lv_hr_expense_account.hr_expense'
    _inherit = 'report.abstract_report'
    _template = 'l10n_lv_hr_expense_account.hr_expense'
    _wrapped_report_class = report_hr_expense_account

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
