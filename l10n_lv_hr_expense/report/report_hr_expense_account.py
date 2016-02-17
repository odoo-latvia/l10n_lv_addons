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

class ReportHrExpenseAccount(models.AbstractModel):
    _name = 'report.l10n_lv_hr_expense.hr_expense'

    def lines(self, form):
        expense_obj = self.env['hr.expense']
        expenses = expense_obj.browse(self.env.context.get('active_id'))
        if form:
            expenses = expense_obj.search([('date','>=',form['date_from']),('date','<=',form['date_to']),('employee_id','=',form['employee_id']),('account_move_id','!=',False)])
        return expenses

    @api.multi
    def render_html(self, data):
        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_id'))
        r_lines = self.lines(data.get('form'))
        docargs = {
            'doc_ids': self.ids,
            'doc_model': self.model,
            'data': data['form'],
            'docs': docs,
            'time': time,
            'lines': r_lines,
        }
        return self.env['report'].render('l10n_lv_hr_expense.hr_expense', docargs)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: