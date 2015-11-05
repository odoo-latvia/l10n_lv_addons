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
from datetime import date, datetime, timedelta
import pytz
from openerp import SUPERUSER_ID

class payslip_eds_export(osv.osv_memory):
    _name = 'payslip.eds.export'

    _columns = {
        'name': fields.char('File Name', size=32, required=True),
        'file_save': fields.binary('Save File', filters='*.xml', readonly=True),
        'responsible_id': fields.many2one('hr.employee', 'Responsible', required=True),
        'date_pay': fields.date('Payment Date', required=True)
    }

    def get_year_month(self, cr, uid, context=None):
        if context is None:
            context = {}
        payslip_obj = self.pool.get('hr.payslip')
        year_list = []
        month_list = []
        for payslip in payslip_obj.browse(cr, uid, context.get('active_ids',[]), context=context):
            date_from = datetime.strptime(payslip.date_from, '%Y-%m-%d')
            date_to = datetime.strptime(payslip.date_to, '%Y-%m-%d')
            month_from = int(datetime.strftime(date_from, '%m'))
            month_to = int(datetime.strftime(date_to, '%m'))
            year_from = int(datetime.strftime(date_from, '%Y'))
            year_to = int(datetime.strftime(date_to, '%Y'))
            if month_from not in month_list:
                month_list.append(month_from)
            if month_to not in month_list:
                month_list.append(month_to)
            if year_from not in year_list:
                year_list.append(year_from)
            if year_to not in year_list:
                year_list.append(year_to)
        return year_list, month_list

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
                emp_stat = "DN"
                lines = payslip.line_ids
                hours = 0.0
                for wd in payslip.worked_days_line_ids:
                    if wd.code == 'WORK100':
                        hours += wd.number_of_hours
                if payslip.employee_id.disability_group:
                    tab = "2"
                    if payslip.employee_id.disability_group in ["I", "II"]:
                        emp_stat = "DI"
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
                        'emp_stat': emp_stat,
                        'lines': lines,
                        'hours': hours
                    }
                result1.append(datas1[(emp_id,tab)])
            res1 = []
            for obj in result1:
                if obj != {}:
                    res1.append(obj)

            ind_c = company_list.index(c)
            company_list[ind_c].update({'results': res1})
        return company_list

    def _get_default_name(self, cr, uid, context=None):
        if context is None:
            context = {}
        company_list = self.prepare_data(cr, uid, context=context)
        name = "_".join([c['company_name'] for c in company_list]).replace(' ','_').replace('"','').replace("'","")
        year, month = self.get_year_month(cr, uid, context=context)
        if len(year) == 1 and len(month) == 1:
            name += ('_' + str(year[0]) + '-' + "%02d" % (month[0]))
        name += '.xml'
        return name

    def _get_default_date_pay(self, cr, uid, context=None):
        if context is None:
            context = {}
        date_pay = date.today().strftime('%Y-%m-%d')
        year, month = self.get_year_month(cr, uid, context=context)
        if len(year) == 1 and len(month) == 1:
            day_def = self.pool.get('ir.values').get_default(cr, SUPERUSER_ID, 'payslip.eds.export', 'date_pay_day')
            if day_def:
                day = int(day_def)
                date_pay = datetime.strftime(date(year[0], month[0], day), '%Y-%m-%d')
            if not day_def:
                m = month[0]
                if month[0] != 12:
                    m += 1
                y = year[0]
                if month[0] == 12:
                    m = 1
                    y += 1
                date_pay = datetime.strftime((date(y, m, 1) - timedelta(days=1)), '%Y-%m-%d')
        return date_pay

    _defaults = {
        'name': _get_default_name,
        'date_pay': _get_default_date_pay
    }

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
        year, month = self.get_year_month(cr, uid, context=context)
        data_of_file = """<?xml version="1.0" encoding="utf-8"?>
<DeclarationFile>
  <Declaration Id="DEC">"""
        for d in data_prep:
            data_of_file += """\n    <DokDDZv1 xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">"""

            # top section:
            if len(year) == 1:
                data_of_file += ("\n      <TaksGads>" + str(year[0]) + "</TaksGads>")
            if len(year) != 1:
                data_of_file += "\n      <TaksGads/>"
            if len(month) == 1:
                data_of_file += ("\n      <TaksMenesis>" + str(month[0]) + "</TaksMenesis>")
            if len(month) != 1:
                data_of_file += "\n      <TaksMenesis/>"
            if d['company_reg']:
                data_of_file += ("\n      <NmrKods>" + d['company_reg'] + "</NmrKods>")
            if not d['company_reg']:
                data_of_file += ("\n      <NmrKods/>")
            company_name = d['company_name'].replace('&','&amp;').replace('<','&lt;').replace('>','&gt;').replace("'","&apos;").replace('"','&quot;')
            data_of_file += ("\n      <NmNosaukums>" + company_name + "</NmNosaukums>")
            date_pay = str(int(datetime.strftime((datetime.strptime(data_exp.date_pay, '%Y-%m-%d')), '%d')))
            data_of_file += ("\n      <IzmaksasDatums>" + date_pay + "</IzmaksasDatums>")
            data_of_file += ("\n      <AtbildPers>" + data_exp.responsible_id.name + "</AtbildPers>")
            if data_exp.responsible_id.work_phone:
                data_of_file += ("\n      <Talrunis>" + data_exp.responsible_id.work_phone + "</Talrunis>")
            if not data_exp.responsible_id.work_phone:
                if data_exp.responsible_id.work_mobile:
                    data_of_file += ("\n      <Talrunis>" + data_exp.responsible_id.work_mobile + "</Talrunis>")
                if not data_exp.responsible_id.work_mobile:
                    data_of_file += ("\n      <Talrunis/>")
            date_prep = datetime.strftime(datetime.now(pytz.timezone(context.get('tz','Europe/Riga'))), '%Y-%m-%dT%H:%M:%S')
            data_of_file += ("\n      <DatumsAizp>" + date_prep + "</DatumsAizp>")

            # tab section:
            table_dict = make_table_dict(d)
            tot_ienakumi = 0.0
            tot_iemaksas = 0.0
            tot_iin = 0.0
            tot_rn = 0.0
            for key, value in table_dict.iteritems():
                data_of_file += ("\n      <Tab%s>" % key)
                data_of_file += "\n        <Rs>"
                n = 0
                tab_tot_ienakumi = 0.0
                tab_tot_iemaksas = 0.0
                tab_tot_iin = 0.0
                tab_tot_rn = 0.0
                for v in value:
                    data_of_file += "\n          <R>"
                    n += 1
                    data_of_file += ("\n            <Npk>" + str(n) + "</Npk>")
                    if v['emp_code']:
                        data_of_file += ("\n            <PersonasKods>" + v['emp_code'] + "</PersonasKods>")
                    if not v['emp_code']:
                        data_of_file += "\n            <PersonasKods/>"
                    data_of_file += ("\n            <VardsUzvards>" + v['emp_name'] + "</VardsUzvards>")
                    data_of_file += ("\n            <SamStat>" + v['emp_stat'] + "</SamStat>")
                    ienakumi = 0.0
                    iemaksas = 0.0
                    iin = 0.0
                    rn = 0.0
                    for l in v['lines']:
                        if l.salary_rule_id.category_id.code == 'BRUTOnLV':
                            ienakumi += l.total
                        if l.salary_rule_id.category_id.code == 'VSAOILV':
                            iemaksas += l.total
                        if l.code == 'IIN':
                            iin += l.total
                        if l.code == 'RN':
                            rn += l.total
                    data_of_file += ("\n            <Ienakumi>" + str(ienakumi) + "</Ienakumi>")
                    data_of_file += ("\n            <Iemaksas>" + str(iemaksas) + "</Iemaksas>")
                    data_of_file += ("\n            <PrecizetieIenakumi>" + str(0.0) + "<PrecizetieIenakumi/>")
                    data_of_file += ("\n            <PrecizetasIemaksas>" + str(0.0) + "<PrecizetasIemaksas/>")
                    data_of_file += ("\n            <IetIedzNodoklis>" + str(iin) + "</IetIedzNodoklis>")
                    wt = "1"
                    data_of_file += ("\n            <DarbaVeids>" + wt + "</DarbaVeids>")
                    data_of_file += ("\n            <RiskaNodPazime>" + (rn > 0.0 and "true" or "false") + "</RiskaNodPazime>")
                    data_of_file += ("\n            <RiskaNod>" + str(rn) + "</RiskaNod>")
#                    data_of_file += ("\n            <IemaksuDatums/>")
                    data_of_file += ("\n            <Stundas>" + str(int(v['hours'])) + "</Stundas>")
                    data_of_file += "\n          </R>"
                    tab_tot_ienakumi += ienakumi
                    tab_tot_iemaksas += iemaksas
                    tab_tot_iin += iin
                    tab_tot_rn += rn
                data_of_file += "\n        </Rs>"
                data_of_file += ("\n          <Ienakumi>" + str(tab_tot_ienakumi) + "</Ienakumi>")
                data_of_file += ("\n          <Iemaksas>" + str(tab_tot_iemaksas) + "</Iemaksas>")
                data_of_file += ("\n          <PrecizetieIenakumi>" + str(0.0) + "</PrecizetieIenakumi>")
                data_of_file += ("\n          <PrecizetasIemaksas>" + str(0.0) + "</PrecizetasIemaksas>")
                data_of_file += ("\n          <IetIedzNodoklis>" + str(tab_tot_iin) + "</IetIedzNodoklis>")
                data_of_file += ("\n          <RiskaNod>" + str(tab_tot_rn) + "</RiskaNod>")
                data_of_file += ("\n      </Tab%s>" % key)
                tot_ienakumi += tab_tot_ienakumi
                tot_iemaksas += tab_tot_iemaksas
                tot_iin += tab_tot_iin
                tot_rn += tab_tot_rn

            data_of_file += ("\n      <Ienakumi>" + str(tot_ienakumi) + "</Ienakumi>")
            data_of_file += ("\n      <Iemaksas>" + str(tot_iemaksas) + "</Iemaksas>")
            data_of_file += ("\n      <PrecizetieIenakumi>" + str(0) + "</PrecizetieIenakumi>")
            data_of_file += ("\n      <PrecizetasIemaksas>" + str(0) + "</PrecizetasIemaksas>")
            data_of_file += ("\n      <IetIedzNodoklis>" + str(tot_iin) + "</IetIedzNodoklis>")
            data_of_file += ("\n      <RiskaNod>" + str(tot_rn) + "</RiskaNod>")
            data_of_file += "\n    </DokDDZv1>"

        data_of_file += "\n  </Declaration>"
        data_of_file += "\n</DeclarationFile>"
        data_of_file_real = base64.encodestring(data_of_file.encode('utf8'))
        self.write(cr, uid, ids, {'file_save': data_of_file_real, 'name': data_exp.name}, context=context)

        vals_obj = self.pool.get('ir.values')
        def_resp_id = vals_obj.get_default(cr, SUPERUSER_ID, 'payslip.eds.export', 'responsible_id')
        if (not def_resp_id) or def_resp_id != data_exp.responsible_id.id:
            vals_obj.set_default(cr, SUPERUSER_ID, 'payslip.eds.export', 'responsible_id', data_exp.responsible_id.id)
        def_date_pay_day = vals_obj.get_default(cr, SUPERUSER_ID, 'payslip.eds.export', 'date_pay_day')
        exp_date_pay_day = datetime.strftime(datetime.strptime(data_exp.date_pay, '%Y-%m-%d'), '%d')
        if (not def_date_pay_day) or def_date_pay_day != exp_date_pay_day:
            vals_obj.set_default(cr, SUPERUSER_ID, 'payslip.eds.export', 'date_pay_day', exp_date_pay_day)

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