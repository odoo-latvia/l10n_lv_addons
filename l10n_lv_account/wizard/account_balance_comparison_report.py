# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2016 ITS-1 (<http://www.its1.lv/>)
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

from openerp.osv import fields, osv

class account_balance_comparison_report(osv.osv_memory):
    _name = "account.balance.comparison.report"
    _description = "Partner Balance Comparison"

    _columns = {
        'date': fields.date('Date', required=True),
        'accountant_id': fields.many2one('hr.employee', 'Accountant', required=True),
        'format': fields.selection([('pdf','PDF'), ('xls','XLS')], string='Format', required=True)
    }

    def _get_default_accountant(self, cr, uid, context=None):
        emp_obj = self.pool.get('hr.employee')
        emp_ids = emp_obj.search(cr, uid, [('job_id.name','in',['Accountant', 'accountant', 'Bookkeeper', 'bookkeeper'])], context=context)
        if not emp_ids:
            emp_ids = emp_obj.search(cr, uid, ['|', ('job_id.name','ilike','accountant'), ('job_id.name','ilike','bookkeeper')], context=context)
        return emp_ids and emp_ids[0] or False

    _defaults = {
        'date': fields.date.context_today,
        'accountant_id': _get_default_accountant,
        'format': 'pdf'
    }

    def _build_contexts(self, cr, uid, ids, data, context=None):
        if context is None:
            context = {}
        result = {}
        result['date'] = 'date' in data['form'] and data['form']['date'] or False
        result['accountant_id'] = 'accountant_id' in data['form'] and data['form']['accountant_id'] or False
        result['format'] = 'format' in data['form'] and data['form']['format'] or False
        return result

    def open_report(self, cr, uid, ids, context=None):
        data = {}
        data['ids'] = context.get('active_ids',[])
        data['model'] = 'res.partner'
        data['form'] = self.read(cr, uid, ids, ['date', 'accountant_id', 'format'], context=context)[0]
        for field in ['date', 'accountant_id', 'format']:
            if isinstance(data['form'][field], tuple):
                data['form'][field] = data['form'][field][0]
        used_context = self._build_contexts(cr, uid, ids, data, context=context)
        data['form']['used_context'] = used_context
        if data['form']['format'] == 'pdf':
            return {
                'type': 'ir.actions.report.xml',
                'report_name': 'l10n_lv_account.balance_comparison',
                'datas': data,
                'context': {
                    'active_ids': context.get('active_ids',[]),
                    'active_model': 'res.partner'
                }
            }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: