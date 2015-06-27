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

from openerp import api, tools
from openerp.osv import fields, osv
from openerp.tools.translate import _
import datetime
from dateutil.relativedelta import relativedelta
from datetime import timedelta

class hr_holidays_status(osv.osv):
    _inherit = "hr.holidays.status"

    _columns = {
        'code': fields.char('Leave Type Code')
    }

class hr_employee(osv.osv):
    _inherit = "hr.employee"

    _columns = {
        'disability_group': fields.selection([('I','I'), ('II','II'), ('III','III')], 'Disability group')
    }

class hr_payslip(osv.osv):
    _inherit = 'hr.payslip'

    def onchange_employee_id(self, cr, uid, ids, date_from, date_to, employee_id=False, contract_id=False, context=None):
        res = super(hr_payslip, self).onchange_employee_id(cr, uid, ids, date_from, date_to, employee_id=employee_id, contract_id=contract_id, context=context)

        # Average salary for last 6 months computation:
        avg_salary = 0.0
        contract = self.pool.get('hr.contract').browse(cr, uid, contract_id, context=context)
        if date_from and date_to and employee_id:
            # get date 6 months earlier:
            date_to_6 = datetime.datetime.strftime((datetime.datetime.strptime(date_to, '%Y-%m-%d') + relativedelta(months=-6)), '%Y-%m-%d')
            # find all payslips within these 6 months:
            prev_ps_ids = self.search(cr, uid, [('date_to','<=',date_to), ('date_to','>',date_to_6), ('employee_id','=',employee_id), ('contract_id','=',contract_id)], context=context)
            # find payslip for current date range and remove it from previous to avoid unsaved data change ignoring:
            curr_ps_ids = self.search(cr, uid, [('date_from','=',date_from), ('date_to','=',date_to), ('employee_id','=',employee_id), ('contract_id','=',contract_id)], context=context)
            if ids:
                if not isinstance(ids,list):
                    ids = [ids]
                curr_ps_ids += ids
            if curr_ps_ids:
                prev_ps_ids = list(set(prev_ps_ids) - set(curr_ps_ids))
            # set start values:
            worked_days = 0.0
            total_salary = 0.0
            # compute worked days and total salary + premiums from previous payslips:
            if prev_ps_ids:
                for prev_ps in self.browse(cr, uid, prev_ps_ids, context=context):
                    prev_wd = 0.0
                    prev_ts = 0.0
                    # try to get worked days from lines:
                    for wdl in prev_ps.worked_days_line_ids:
                        if wdl.code == 'WORK100':
                            prev_wd += wdl.number_of_days
                    # if there are no worked day lines, compute workdays from dates:
                    if not prev_ps.worked_days_line_ids:
                        oneday = datetime.timedelta(days=1)
                        test_date = datetime.datetime.strptime(prev_ps.date_from, '%Y-%m-%d')
                        while test_date != datetime.datetime.strptime(prev_ps.date_to, '%Y-%m-%d'):
                            if test_date.weekday() in [0, 1, 2, 3, 4]:
                                prev_wd += 1.0
                            test_date += oneday
                    # try to get salary and premiums from computed payslip lines:
                    for l in prev_ps.line_ids:
                        if l.code in ['LD', 'PIEM', '16']:
                            prev_ts += l.total
                    # if there are no computed lines, compute them to get data:
                    if not prev_ps.line_ids:
                        prev_lines = self.get_payslip_lines(cr, uid, [contract_id], prev_ps.id, context)
                        for pl in prev_lines:
                            if pl['code'] in ['LD', 'PIEM', '16']:
                                prev_ts += (float(pl['quantity']) * pl['amount'] * pl['rate'] / 100)
                    # sum this to start values:
                    worked_days += prev_wd
                    total_salary += prev_ts
            # get current worked days:
            wd_lines = self.get_worked_day_lines(cr, uid, [contract_id], date_from, date_to, context=context)
            curr_wd = 0.0
            total_days = 0.0
            for wd in wd_lines:
                if wd['code'] == 'WORK100':
                    curr_wd += wd['number_of_days']
                total_days += wd['number_of_days']
            # if worked days are not provided, get workdays from dates:
            if not wd_lines:
                oneday = datetime.timedelta(days=1)
                test_date = datetime.datetime.strptime(date_from, '%Y-%m-%d')
                while test_date != datetime.datetime.strptime(date_to, '%Y-%m-%d'):
                    if test_date.weekday() in [0, 1, 2, 3, 4]:
                        curr_wd += 1.0
                    test_date += oneday
                total_days = curr_wd
            # define start total:
            curr_ts = 0.0
            # if current payslip ids, get payslip line computed values:
            if curr_ps_ids:
                for c in curr_ps_ids:
                    ps_lines = self.get_payslip_lines(cr, uid, [contract_id], c, context)
                    for p in ps_lines:
                        if p['code'] in ['LD', 'PIEM', '16']:
                            curr_ts += (float(p['quantity']) * p['amount'] * p['rate'] / 100)
            # if no current payslip ids, compute the value:
            if (not curr_ps_ids) and total_days != 0.0:
                curr_ts += contract.wage * curr_wd / total_days
                ip_lines = self.get_inputs(cr, uid, [contract_id], date_from, date_to, context=context)
                if ip_lines:
                    for cil in ip_lines:
                        if cil['code'] in ['PIEM', 'PIEMV']:
                            curr_ts += cil.get('amount',0.0)
            total_salary += curr_ts
            worked_days += curr_wd
            if worked_days != 0.0:
                avg_salary = total_salary / worked_days
        if avg_salary != 0.0:
            res['value']['input_line_ids'].append({
                'name': _("Average day salary for last 6 months"),
                'code': 'VDA6M',
                'amount': avg_salary,
                'contract_id': contract_id
            })

        # Use Leave Type Code instead od Leave Type name in code field:
        if res['value']['worked_days_line_ids']:
            hd_type_obj = self.pool.get('hr.holidays.status')
            for wdl_val in res['value']['worked_days_line_ids']:
                hd_type_ids = hd_type_obj.search(cr, uid, [('name','=',wdl_val['name'])], context=context)
                if hd_type_ids:
                    hd_type = hd_type_obj.browse(cr, uid, hd_type_ids, context=context)
                    if hd_type.code and hd_type.code != wdl_val['code']:
                        ind = res['value']['worked_days_line_ids'].index(wdl_val)
                        res['value']['worked_days_line_ids'][ind]['code'] = hd_type.code

        # Put number of dependents in Other Inputs:
        if res['value']['input_line_ids']:
            emp_obj = self.pool.get('hr.employee')
            employee = emp_obj.browse(cr, uid, employee_id, context=context)
            found = False
            for inp_val in res['value']['input_line_ids']:
                if inp_val['code'] == 'APG':
                    found = True
                    if inp_val.get('amount',0.0) != float(employee.children):
                        ind = res['value']['input_line_ids'].index(inp_val)
                        res['value']['input_line_ids'][ind].update({'amount': float(employee.children)})
            if not found:
                res['value']['input_line_ids'].append({
                    'code': 'APG',
                    'name': _("Dependent persons"),
                    'amount': float(employee.children),
                    'contract_id': contract_id
                })

        # Compute number of calendar days absent:
        if res['value']['input_line_ids']:
            day_from = datetime.datetime.strptime(date_from,"%Y-%m-%d")
            day_to = datetime.datetime.strptime(date_to,"%Y-%m-%d")
            nb_of_days = (day_to - day_from).days + 1
            lt_obj = self.pool.get('hr.holidays.status')
            excl_t_ids = lt_obj.search(cr, uid, [('code','in',['LEGAL','OFFICIAL'])], context=context)
            holiday_obj = self.pool.get('hr.holidays')
            abs_days = 0.0
            for day in range(0, nb_of_days):
                comp_date = day_from + timedelta(days=day)
                comp_day = comp_date.strftime("%Y-%m-%d")
                holiday_ids = holiday_obj.search(cr, uid, [('holiday_status_id','not in',excl_t_ids), ('state','=','validate'),('employee_id','=',employee_id),('type','=','remove'),('date_from','<=',comp_day),('date_to','>=',comp_day)])
                if holiday_ids:
                    abs_days += 1.0
            found = False
            for inp_val in res['value']['input_line_ids']:
                if inp_val['code'] == 'KAL':
                    found = True
                    if inp_val.get('amount',0.0) != abs_days:
                        ind = res['value']['input_line_ids'].index(inp_val)
                        res['value']['input_line_ids'][ind].update({'amount': abs_days})
            if not found:
                res['value']['input_line_ids'].append({
                    'code': 'KAL',
                    'name': _("Number of calendar days absent"),
                    'amount': abs_days,
                    'contract_id': contract_id
                })
        return res

    def reload_inputs(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        if len(ids) == 1:
            payslip = self.browse(cr, uid, ids[0], context=context)
            date_from = payslip.date_from
            date_to = payslip.date_to
            employee_id = payslip.employee_id and payslip.employee_id.id or False
            contract_id = payslip.contract_id and payslip.contract_id.id or False
            vals = self.onchange_employee_id(cr, uid, [], date_from, date_to, employee_id=employee_id, contract_id=contract_id, context=context)['value']
            if vals:
                if 'input_line_ids' in vals and vals['input_line_ids']:
                    input_line_obj = self.pool.get('hr.payslip.input')
                    for l in vals['input_line_ids']:
                        il_ids = input_line_obj.search(cr, uid, [('payslip_id','=',payslip.id), ('code','=',l['code'])], context=context)
                        if il_ids and 'amount' in l and l['amount'] != 0.0:
                            input_line_obj.write(cr, uid, il_ids, {'amount': l['amount']}, context=context)
                        if not il_ids:
                            il_vals = l.copy()
                            il_vals.update({'payslip_id': payslip.id, 'contract_id': contract_id})
                            input_line_obj.create(cr, uid, il_vals, context=context)
                if 'worked_days_line_ids' in vals and vals['worked_days_line_ids']:
                    wd_line_obj = self.pool.get('hr.payslip.worked_days')
                    for wd in vals['worked_days_line_ids']:
                        wd_ids = wd_line_obj.search(cr, uid, [('payslip_id','=',payslip.id), ('code','=',wd['code'])], context=context)
                        if wd_ids:
                            wd_line_obj.write(cr, uid, wd_ids, wd, context=context)
                        else:
                            wd_vals = wd.copy()
                            wd_vals.update({'payslip_id': payslip.id})
                            wd_line_obj.create(cr, uid, wd_vals, context=context)
        return True

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: