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
from openerp.report.report_sxw import rml_parse

class ReportHrExpenseAccount(models.AbstractModel):
    _name = 'report.l10n_lv_hr_expense.hr_expense'

    def expense_groups(self, form):
        expense_obj = self.env['hr.expense']
        expenses = expense_obj.browse(self.env.context.get('active_id'))
        if form:
            expenses = expense_obj.search([('date','>=',form['date_from']),('date','<=',form['date_to']),('employee_id','=',form['employee_id'][0]),('account_move_id','!=',False)])
        exp_data = {}
        if expenses:
            for e in expenses:
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
                        if ml not in exp_move_lines:
                            exp_move_lines.append(ml)
            e_dict.update({
                'exp_move_lines': exp_move_lines
            })
            e_groups.append(e_dict)
        return e_groups

    def bank_move_lines(self, form):
        bank_obj = self.env['account.bank.statement.line']
        if form:
            result_bank = bank_obj.browse(form['bank_statement_line_ids'])
        else:
            expense_obj = self.env['hr.expense']
            exp_ids = self.env.context.get('active_id')
            partners = []
            for exp in expense_obj.browse(exp_ids):
                if exp.employee_id.address_home_id:
                    partners.append(exp.employee_id.address_home_id.id)
            result_bank = bank_obj.search([('partner_id','in',partners)])
        line_list = []
        for bsl in result_bank:
            for m in bsl.journal_entry_ids:
                for ml in m.line_ids:
                    if ml not in line_list:
                        line_list.append(ml)
        return line_list

    @api.multi
    def render_html(self, data):
        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_id'))
        docargs = {
            'doc_ids': self.ids,
            'doc_model': self.model,
            'data': data['form'],
            'docs': docs,
            'time': time,
            'formatLang': rml_parse(self._cr, self._uid, '', context=self.env.context).formatLang,
            'expense_groups': self.expense_groups(data.get('form')),
            'bank_move_lines': self.bank_move_lines(data.get('form'))
        }
        return self.env['report'].render('l10n_lv_hr_expense.hr_expense', docargs)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: