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

from openerp.osv import fields, osv
from openerp.tools.translate import _
import base64

class payslip_eds_export(osv.osv_memory):
    _name = 'payslip.eds.export'

    _columns = {
        'name': fields.char('File Name', size=32),
        'file_save': fields.binary('Save File', filters='*.xml', readonly=True)
    }

    def prepare_data(self, cr, uid, context=None):
        if context is None:
            context = {}

        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        payslip_obj = self.pool.get('hr.payslip')
        result = []
        datas = {}
        for payslip in payslip_obj.browse(cr, uid, context.get('active_ids',[]), context=context):
            company_id = payslip.company_id and payslip.company_id.id or user.company_id.id
            company_reg = payslip.company_id and payslip.company_id.company_registry or user.company_id.company_registry
            company_name = payslip.company_id and payslip.company_id.name or user.company_id.name
            payslips = [payslip]
            if datas.get((company_id)):
                payslips += datas[(company_id)]['payslips']
                datas[(company_id)].clear()
            if not datas.get((company_id)):
                datas[(company_id)] = {
                    'company_reg': company_reg,
                    'company_name': company_name,
                    'payslips': payslips
                }
            result.append(datas[(company_id)])
        company_list = []
        for object in result:
            if object != {}:
                company_list.append(object)

        for c in company_list:
            result1 = []
            datas1 = {}
            for payslip in c['payslips']:
                tab = "1"
                emp_id = payslip.employee_id.id
                emp_name = payslip.employee_id.name
                emp_code = payslip.employee_id.identification_id
                lines = payslip.line_ids
                hours = 0.0
                for wd in payslip.worked_days_line_ids:
                    if wd.code == 'WORK100':
                        hours += wd.number_of_hours
                if payslip.employee_id.disability_group:
                    tab = "2"
                if tab == "1":
                    for pl in payslip.line_ids:
                        if pl.code in ['PABAN','PABBN'] and pl.amount != 0.0:
                            tab == "2"
                if datas1.get((emp_id,tab)):
                    lines += datas1[(emp_id,tab)]['lines']
                    hours += datas1[(emp_id,tab)]['hours']
                    datas1[(emp_id,tab)].clear()
                if not datas1.get((emp_id,tab)):
                    datas1[(emp_id,tab)] = {
                        'tab': tab,
                        'emp_name': emp_name,
                        'emp_code': emp_code,
                        'lines': lines,
                        'hours': hours
                    }
                result1.append(datas1[(emp_id,tab)])
            res1 = []
            for obj in result1:
                if obj != {}:
                    res1.append(obj)

            for r in res1:
                r_list = []
                r_data = {}
                for l in r['lines']:
                    rule_id = l.salary_rule_id.id
                    code = l.code
                    amount = l.total
                    if r_data.get((rule_id)):
                        amount += r_data[(rule_id)]['amount']
                        r_data[(rule_id)].clear()
                    if not r_data.get((rule_id)):
                        r_data[(rule_id)] = {
                            'code': code,
                            'amount': amount
                        }
                    r_list.append(r_data[(rule_id)])
                new_lines = []
                for o in r_list:
                    if o != {}:
                        new_lines.append(o)
                ind = res1.index(r)
                res1[ind]['lines'] = new_lines

            ind_c = company_list.index(c)
            company_list[ind_c].update({'results': res1})
        return company_list

    def create_xml(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        def make_table_dict(t_data):
            t_dict = {}
            for r in t_data['results']:
                if r['tab'] in t_dict:
                    t_dict[r['tab']].append(r)
                if r['tab'] not in t_dict:
                    t_dict.update({r['tab']: [r]})
            return t_dict

        data_exp = self.browse(cr, uid, ids[0])
        data_prep = self.prepare_data(cr, uid, context=context)
        data_of_file = """<?xml version="1.0" encoding="utf-8"?>
<DeclarationFile>
  <Declaration Id="DEC">"""
        for d in data_prep:
            data_of_file += """\n    <DokDDZv1 xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">"""
            table_dict = make_table_dict(d)
            data_of_file += "\n    </DokDDZv1>"
        data_of_file += "\n  </Declaration>"
        data_of_file += "\n</DeclarationFile>"
        data_of_file_real = base64.encodestring(data_of_file.encode('utf8'))
        self.write(cr, uid, ids, {'file_save': data_of_file_real, 'name': data_exp.name}, context=context)

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'payslip.eds.export',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': data_exp.id,
            'views': [(False,'form')],
            'target': 'new',
        }


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: