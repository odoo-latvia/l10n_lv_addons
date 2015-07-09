# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 ITS-1 (<http://www.its1.lv/>)
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

from openerp.osv import osv
from openerp.report import report_sxw

class payslip_summary_report(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        super(payslip_summary_report, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'cr':cr,
            'uid': uid,
            'data_rep': self.data_rep,
            'sum_data_rep': self.sum_data_rep
        })
        self.context = context

    def data_rep(self, doc_ids):
        line_obj = self.pool.get('hr.payslip.line')
        line_ids = line_obj.search(self.cr, self.uid, [('slip_id','in',doc_ids), ('salary_rule_id.appears_on_summary','=',True)], context=self.context)
        result = []
        datas = {}
        for line in line_obj.browse(self.cr, self.uid, line_ids, context=self.context):
            emp_id = line.slip_id.employee_id.id
            emp_name = line.slip_id.employee_id.name
            rule_id = line.salary_rule_id.id
            name = line.salary_rule_id.name
            sequence = line.salary_rule_id.sequence
            amount = line.total
            if datas.get((emp_id,rule_id)):
                amount += datas[(emp_id,rule_id)]['amount']
                datas[(emp_id,rule_id)].clear()
            if not datas.get((emp_id,rule_id)):
                datas[(emp_id,rule_id)] = {
                    'emp_id': emp_id,
                    'rule_id': rule_id,
                    'employee': emp_name,
                    'name': name,
                    'sequence': sequence,
                    'amount': amount
                }
            result.append(datas[(emp_id,rule_id)])
        data_list = []
        for object in result:
            if object != {}:
                data_list.append(object)
        complete_rule_list = []
        for d in data_list:
            if (d['sequence'],d['rule_id'],d['name']) not in complete_rule_list:
                complete_rule_list.append((d['sequence'],d['rule_id'],d['name']))
        sorted_rule_list = sorted(complete_rule_list, key=lambda tup: tup[0])
        emp_list = []
        for d2 in data_list:
            if d2['emp_id'] not in emp_list:
                emp_list.append(d2['emp_id'])
        data_list_real = []
        for e in emp_list:
            e_data = {'employee': '', 'rules': []}
            for rule in sorted_rule_list:
                rule_dict = {rule[2]: 0.0}
                for d3 in data_list:
                    if d3['emp_id'] == e:
                        e_data['employee'] = d3['employee']
                        if d3['rule_id'] == rule[1]:
                            rule_dict.update({rule[2]: d3['amount']})
                e_data['rules'].append(rule_dict)
            data_list_real.append(e_data)
        return data_list_real

    def sum_data_rep(self, data_list):
        rule_list = []
        for d in data_list:
            for r in d['rules']:
                if list(r.keys())[0] not in rule_list:
                    rule_list.append(list(r.keys())[0])
        amt_list = []
        for rule in rule_list:
            r_dict = {rule: 0.0}
            for d in data_list:
                for r2 in d['rules']:
                    if list(r2.keys())[0] == rule:
                        r_dict[list(r2.keys())[0]] += list(r2.values())[0]
            amt_list.append(r_dict)
        return amt_list

class wrapped_report_payslip_summary(osv.AbstractModel):
    _name = 'report.l10n_lv_hr_payroll.report_payslip_summary'
    _inherit = 'report.abstract_report'
    _template = 'l10n_lv_hr_payroll.report_payslip_summary'
    _wrapped_report_class = payslip_summary_report

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: