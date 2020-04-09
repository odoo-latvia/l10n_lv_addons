# -*- encoding: utf-8 -*-
##############################################################################
#
#    Part of Odoo.
#    Copyright (C) 2020 Allegro IT (<http://www.its1.lv/>)
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

from odoo import api, fields, models, _
import datetime
from dateutil.relativedelta import relativedelta
from datetime import timedelta

class HolidaysType(models.Model):
    _inherit = "hr.holidays.status"

    code = fields.Char(string='Code')
    reduces_tax_relief = fields.Boolean(string='Reduces Tax Relief')


class Employee(models.Model):
    _inherit = "hr.employee"

    holiday_ids = fields.One2many('hr.holidays', 'employee_id', string='Leaves')
    relief_ids = fields.One2many('hr.employee.relief', 'employee_id', string='Tax Relief')


class EmployeeRelief(models.Model):
    _name = "hr.employee.relief"
    _description = "Employee Tax Relief"
    _order = "date_from desc"

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, ondelete='cascade')
    type = fields.Selection([
        ('untaxed_month', 'Untaxed Minimum for Month'),
        ('dependent', 'Dependent Person'),
        ('disability1', 'Group 1 Disability'),
        ('disability2', 'Group 2 Disability'),
        ('disability3', 'Group 3 Disability')
    ], string='Type', required=True)
    name = fields.Char(string='Name', required=True)
    date_from = fields.Date(string='Date From')
    date_to = fields.Date(string='Date To')
    amount = fields.Monetary(string='Amount')
    currency_id = fields.Many2one('res.currency', string='Currency', related="employee_id.resource_id.company_id.currency_id")


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'
    _order = 'date_from desc, write_date desc'

    @api.model
    def _get_month(self, date_from, date_to):
        from_dt = datetime.datetime.strptime(date_from, '%Y-%m-%d')
        month_from = tools.ustr(from_dt.strftime('%B-%Y'))
        to_dt = datetime.datetime.strptime(date_to, '%Y-%m-%d')
        month_to = tools.ustr(from_dt.strftime('%B-%Y'))
        if month_from == month_to:
            month = month_from
        else:
            month = month_from + '-' + month_to
        return month

    @api.model
    def _month_selection(self):
        self._cr.execute("""SELECT date_from, date_to FROM hr_payslip;""")
        all_ps_data = self._cr.dictfetchall()
        month_list = []
        for ps in all_ps_data:
            month = self._get_month(ps.date_from, ps.date_to)
            if (month,month) not in month_list:
                month_list.append((month,month))
        return month_list

    @api.depends('date_from', 'date_to')
    def _compute_payslip_month(self):
        for payslip in self:
            payslip.month = self._get_month(payslip.date_from, payslip.date_to)

    month = fields.Selection(selection=_month_selection, string='Month', compute="_compute_payslip_month", store=True)

    @api.onchange('date_from', 'date_to', 'employee_id', 'contract_id')
    def onchange_dates(self):
        avg_salary = 0.0
        if self.employee_id and self.contract_id and self.date_from and self.date_to:
            date_to_6 = datetime.datetime.strftime((datetime.datetime.strptime(self.date_to, '%Y-%m-%d') + relativedelta(months=-7)), '%Y-%m-%d')
            # find payslip for current date range and remove it from previous to avoid unsaved data change ignoring:
            curr_pss = self.search([('date_from','=',self.date_from), ('date_to','=',self.date_to), ('employee_id','=',self.employee_id.id), ('contract_id','=',self.contract_id.id)])
            curr_ps_ids = [cps.id for cps in curr_pss]
            if isinstance(self.id, int) and self.id not in curr_ps_ids:
                curr_ps_ids.append(self.id)
            # find all payslips within these 6 months:
            prev_pss = self.search([('date_from','<=',self.date_to), ('date_to','>',date_to_6), ('employee_id','=',self.employee_id.id), ('contract_id','=',self.contract_id.id), ('id','not in',curr_ps_ids)])
            # set start values:
            worked_days = 0.0
            total_salary = 0.0
            # compute worked days and total salary + premiums from previous payslips:
            for prev_ps in prev_pss:
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
                    prev_lines = self._get_payslip_lines([self.contract_id.id], prev_ps.id)
                    for pl in prev_lines:
                        if pl['code'] in ['LD', 'PIEM', '16']:
                            prev_ts += (float(pl['quantity']) * pl['amount'] * pl['rate'] / 100)
                # sum this to start values:
                worked_days += prev_wd
                total_salary += prev_ts
            # if there are no previous payslips, compute from current:
            if not prev_pss:
                # get current worked days:
                wd_lines = self.get_worked_day_lines(self.contract_id], self.date_from, self.date_to)
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
                        ps_lines = self._get_payslip_lines([self.contract_id.id], c)
                        for p in ps_lines:
                            if p['code'] in ['LD', 'PIEM', '16']:
                                curr_ts += (float(p['quantity']) * p['amount'] * p['rate'] / 100)
                # if no current payslip ids, compute the value:
                if (not curr_ps_ids) and total_days != 0.0:
                    curr_ts += self.contract_id.wage * curr_wd / total_days
#                    if self.contract_id.prem_deduct_ids:
#                        prem_amount = 0.0
#                        for pd in self.contract_id.prem_deduct_ids:
#                            if pd.code == 'PIEM':
#                                date_from_pd = date_from
#                                date_to_pd = date_to
#                                if pd.date_from and pd.date_from > date_from and pd.date_from <= date_to:
#                                    date_from_pd = pd.date_from
#                                if pd.date_to and pd.date_to < date_to and pd.date_to >= date_from:
#                                    date_to_pd = pd.date_to
#                                if date_from and date_to:
#                                    dmy = compute_dmy(date_from, date_to)
#                                    pd_amount = (dmy['years'] != 0 and pd.amount * 12.0 or 0.0) + (dmy['months'] != 0 and pd.amount * dmy['months'] or 0.0) + ((pd.amount / dmy['tm_days']) * dmy['days'])
#                                    prem_amount += pd_amount
#                        if prem_amount != 0.0:
#                            premium = total_days and ((prem_amount * curr_wd) / total_days) or 0.0
#                            if total_days == 0.0:
#                               premium = prem_amount
#                            curr_ts += premium
                    ip_lines = self.get_inputs(self.contract_id, self.date_from, self.date_to)
                    if ip_lines:
                        for cil in ip_lines:
                            if cil['code'] == 'PIEMV':
                                curr_ts += cil.get('amount',0.0)
                total_salary += curr_ts
                worked_days += curr_wd
            if worked_days != 0.0:
                avg_salary = total_salary / worked_days
        if avg_salary != 0.0:
            found = False
            inp_vals = []
            for il in self.input_line_ids:
                if il.code != 'VDA6M':
                    inp_vals.append((4, il.id))
                else:
                    inp_vals.append((1, il.id, {'amount': float(avg_salary)}))
                    found = True
            if not found:
                inp_vals.append((0, 0, {
                    'name': _("Average day salary for last 6 months"),
                    'code': 'VDA6M',
                    'amount': avg_salary,
                    'contract_id': self.contract_id.id
                }))


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: