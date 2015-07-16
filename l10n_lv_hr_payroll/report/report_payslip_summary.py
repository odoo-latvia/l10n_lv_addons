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
from datetime import datetime

class payslip_summary_report(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        super(payslip_summary_report, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'cr':cr,
            'uid': uid,
            'get_company': self.get_company,
            'get_period': self.get_period,
            'get_address': self.get_address,
            'data_rep': self.data_rep,
            'sum_data_rep': self.sum_data_rep,
            'data_accounts': self.data_accounts
        })
        self.context = context

    def get_company(self, doc_ids):
        ps_obj = self.pool.get('hr.payslip')
        def get_parent(company):
            c = company
            if company.parent_id:
                c = get_parent(c)
            return c
        c_list = []
        for p in ps_obj.browse(self.cr, self.uid, doc_ids, context=self.context):
            if p.company_id:
                mc = get_parent(p.company_id)
                if mc not in c_list:
                    c_list.append(mc)
        cp = False
        if c_list:
            cp = c_list[0]
        return cp

    def get_period(self, doc_ids):
        ps_obj = self.pool.get('hr.payslip')
        date_from = False
        date_to = False
        for p in ps_obj.browse(self.cr, self.uid, doc_ids, context=self.context):
            if date_from != False and datetime.strptime(p.date_from, '%Y-%m-%d') < datetime.strptime(date_from, '%Y-%m-%d'):
                date_from = p.date_from
            if date_from == False:
                date_from = p.date_from
            if date_to != False and datetime.strptime(p.date_to, '%Y-%m-%d') > datetime.strptime(date_to, '%Y-%m-%d'):
                date_to = p.date_to
            if date_to == False:
                date_to = p.date_to
        return {'from': date_from, 'to': date_to}

    def get_address(self, company):
        addr = False
        if company:
            addr_list = []
            if company.street:
                addr_list.append(company.street)
            if company.street2:
                addr_list.append(company.street2)
            if company.city:
                addr_list.append(company.city)
            if company.state_id:
                addr_list.append(company.state_id.name)
            if company.zip:
                addr_list.append(company.zip)
            if company.country_id:
                addr_list.append(company.country_id.name)
            if addr_list:
                addr = ", ".join(addr_list)
        return addr

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

    def data_accounts(self, doc_ids):
        line_obj = self.pool.get('hr.payslip.line')
        line_ids = line_obj.search(self.cr, self.uid, [('slip_id','in',doc_ids)], context=self.context)
        result = []
        datas = {}
        for line in line_obj.browse(self.cr, self.uid, line_ids, context=self.context):
            if hasattr(line.salary_rule_id, 'account_debit') and hasattr(line.salary_rule_id, 'account_credit') and (line.salary_rule_id.account_debit or line.salary_rule_id.account_credit):
                rule_id = line.salary_rule_id.id
                acd_id = 0
                debit_code = ''
                acc_id = 0
                credit_code = ''
                if line.salary_rule_id.account_debit:
                    acd_id = line.salary_rule_id.account_debit.id
                    debit_code = line.salary_rule_id.account_debit.code
                if line.salary_rule_id.account_credit:
                    acc_id = line.salary_rule_id.account_credit.id
                    credit_code = line.salary_rule_id.account_credit.code
                if acd_id and (not acc_id):
                    acc_id = line.slip_id.journal_id.default_credit_account_id and line.slip_id.journal_id.default_credit_account_id.id or 0
                    if acc_id:
                        credit_code = line.slip_id.journal_id.default_credit_account_id.code
                if acc_id and (not acd_id):
                    acd_id = line.slip_id.journal_id.default_debit_account_id and line.slip_id.journal_id.default_debit_account_id.id or 0
                    if acd_id:
                        debit_code = line.slip_id.journal_id.default_debit_account_id.code
                sequence = line.salary_rule_id.sequence
                appears = line.salary_rule_id.appears_on_summary
                amount = line.total
                if datas.get((rule_id,acd_id,acc_id)):
                    amount += datas[(rule_id,acd_id,acc_id)]['amount']
                    datas[(rule_id,acd_id,acc_id)].clear()
                if not datas.get((rule_id,acd_id,acc_id)):
                    datas[(rule_id,acd_id,acc_id)] = {
                        'rule_id': rule_id,
                        'acd_id': acd_id,
                        'debit_code': debit_code,
                        'acc_id': acc_id,
                        'credit_code': credit_code,
                        'sequence': sequence,
                        'appears': appears,
                        'amount': amount
                    }
                result.append(datas[(rule_id,acd_id,acc_id)])
        data_list = []
        for object in result:
            if object != {}:
                data_list.append(object)
        if data_list:
            sorted_data_list = sorted(data_list, key=lambda k: k['sequence'])
            res = []
            d = {}
            for sdl in sorted_data_list:
                acd_id = sdl['acd_id']
                acc_id = sdl['acc_id']
                debit_code = sdl['debit_code']
                credit_code = sdl['credit_code']
                amount = sdl['appears'] and sdl['amount'] or 0.0
                if d.get((acd_id,acc_id)):
                    amount += d[(acd_id,acc_id)]['amount']
                    d[(acd_id,acc_id)].clear()
                if not d.get((acd_id,acc_id)):
                    d[(acd_id,acc_id)] = {
                        'debit_code': debit_code,
                        'credit_code': credit_code,
                        'amount': amount
                    }
                res.append(d[(acd_id,acc_id)])
            res2 = []
            for obj in res:
                if obj != {}:
                    res2.append(obj)
            data_list = res2
        return data_list


class wrapped_report_payslip_summary(osv.AbstractModel):
    _name = 'report.l10n_lv_hr_payroll.report_payslip_summary'
    _inherit = 'report.abstract_report'
    _template = 'l10n_lv_hr_payroll.report_payslip_summary'
    _wrapped_report_class = payslip_summary_report

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: