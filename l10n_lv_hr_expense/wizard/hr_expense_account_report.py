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

from openerp import api, fields, models, _

class HrExpenseAccountReport(models.TransientModel):
    _name = "hr.expense.account.report"
    _description = "HR Expenses Report"

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    date_from = fields.Date('Date Form', required=True)
    date_to = fields.Date('Date To', required=True, default=fields.Date.today())
    bank_statement_line_ids = fields.Many2many('account.bank.statement.line', 'bank_statement_line_rel', 'report_id', 'statement_line_id', string='Bank Statement Lines')

    @api.onchange('employee_id', 'date_from', 'date_to')
    def _onchange_data(self):
        bank_statement_lines = self.env['account.bank.statement.line'].search([('partner_id','=',self.employee_id.address_home_id.id), ('date','>=',self.date_from), ('date','<=',self.date_to)])
        self.bank_statement_line_ids = [(6, 0, [b.id for b in bank_statement_lines])]

    def _build_contexts(self, data):
        result = {}
        result['employee_id'] = 'employee_id' in data['form'] and data['form']['employee_id'] or False
        result['date_from'] = 'date_from' in data['form'] and data['form']['date_from'] or False
        result['date_to'] = 'date_to' in data['form'] and data['form']['date_to'] or False
        result['bank_statement_line_ids'] = 'bank_statement_line_ids' in data['form'] and data['form']['bank_statement_line_ids'] or False
        return result

    @api.multi
    def print_report(self):
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['employee_id','date_from','date_to', 'bank_statement_line_ids'])[0]
        used_context = self._build_contexts(data)
        data['form']['used_context'] = dict(used_context, lang=self.env.context.get('lang', 'en_US'))
        return self.env['report'].with_context().get_action(self, 'l10n_lv_hr_expense.hr_expense', data=data)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: