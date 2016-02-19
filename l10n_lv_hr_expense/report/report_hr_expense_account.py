# -*- encoding: utf-8 -*-
##############################################################################
#
#    Part of Odoo.
#    Copyright (C) 2016 ITS-1 (<http://www.its1.lv/>)
#                       E-mail: <info@its1.lv>
#                       Address: <Vienibas gatve 109 LV-1058 Riga Latvia>
#                       Phone: +371 67289467
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
from openerp import api, models, _
from openerp.report import report_sxw

class ReportHrExpenseAccount(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(ReportHrExpenseAccount, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'expense_groups': self.expense_groups,
            'dates': self.dates,
            'bank_move_lines': self.bank_move_lines
        })
        self.context = context

    def expense_groups(self, form):
        expense_obj = self.pool.get('hr.expense')
        expense_ids = self.context.get('active_ids', [])
        if form:
            expense_ids = expense_obj.search(self.cr, self.uid, [('date','>=',form['date_from']),('date','<=',form['date_to']),('employee_id','=',form['employee_id'][0]),('account_move_id','!=',False)])
        exp_data = {}
        if expense_ids:
            for e in expense_obj.browse(self.cr, self.uid, expense_ids):
                if (e.employee_id, e.currency_id, e.journal_id) in exp_data:
                    exp_data[(e.employee_id, e.currency_id, e.journal_id)].append(e)
                else:
                    exp_data.update({(e.employee_id, e.currency_id, e.journal_id): [e]})
        e_groups = []
        for key, value in exp_data.iteritems():
            e_dict = {
                'employee': key[0],
                'currency': key[1],
                'journal': key[2],
                'expenses': value
            }
            exp_move_lines = []
            for v in value:
                if v.account_move_id:
                    for ml in v.account_move_id.line_ids:
                        if (not ml.partner_id) or (ml.partner_id and ml.partner_id.id != key[0].address_home_id.id):
                            ml_name = ml.name
                            if (not ml.tax_ids) and (not ml.tax_line_id):
                                ml_name = v.product_id.name
                                if ml.product_id.default_code:
                                    ml_name = '[%s] %s' % (ml.product_id.default_code, ml_name)
                            exp_move_lines.append({
                                'doc_no': v.name,
                                'journ_entr_no': ml.move_id.name,
                                'doc_date': ml.date,
                                'partner': ml.partner_id,
                                'name': ml_name,
                                'account': ml.account_id,
                                'debit': ml.debit,
                                'credit': ml.credit
                            })
            e_dict.update({
                'exp_move_lines': exp_move_lines
            })
            e_groups.append(e_dict)
        return e_groups

    def dates(self, form):
        if form:
            date_from = form['date_from']
            date_to = form['date_to']
        else:
            expense_obj = self.pool.get('hr.expense')
            exp_ids = self.context.get('active_ids',[])
            date_from = False
            date_to = False
            for e in expense_obj.browse(self.cr, self.uid, exp_ids):
                if e.date:
                    if date_from != False and e.date < date_from:
                        date_from = e.date
                    if date_to != False and e.date > date_to:
                        date_to = e.date
                    if date_from == False:
                        date_from = e.date
                    if date_to == False:
                        date_to = e.date
        return {'date_from': date_from, 'date_to': date_to}

    def bank_move_lines(self, form):
        bank_obj = self.pool.get('account.bank.statement.line')
        partners = []
        if form:
            result_bank = bank_obj.browse(self.cr, self.uid, form['bank_statement_line_ids'])
            employee = self.pool.get('hr.employee').browse(self.cr, self.uid, form['employee_id'][0])
            if employee.address_home_id:
                partners.append(employee.address_home_id.id)
        else:
            expense_obj = self.pool.get('hr.expense')
            exp_ids = self.context.get('active_ids', [])
            for exp in expense_obj.browse(self.cr, self.uid, exp_ids):
                if exp.employee_id.address_home_id:
                    partners.append(exp.employee_id.address_home_id.id)
            result_bank = bank_obj.search(self.cr, self.uid, [('partner_id','in',partners)])
        line_list = []
        for bsl in result_bank:
            for m in bsl.journal_entry_ids:
                for ml in m.line_ids:
                    if ml not in line_list and ml.partner_id and ml.partner_id.id in partners:
                        line_list.append(ml)
        return line_list

class HrEAreport(models.AbstractModel):
    _name = 'report.l10n_lv_hr_expense.hr_expense'
    _inherit = 'report.abstract_report'
    _template = 'l10n_lv_hr_expense.hr_expense'
    _wrapped_report_class = ReportHrExpenseAccount

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: