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
from xml.dom.minidom import getDOMImplementation, parseString
from datetime import datetime

class relief_eds_import(osv.osv_memory):
    _name = 'relief.eds.import'

    _columns = {
        'eds_file': fields.binary('XML file from EDS', required=True),
        'eds_fname': fields.char('EDS Filename'),
        'employees_ids': fields.many2many('hr.employee', 'Employees')
    }

    def _get_default_employees(self, cr, uid, context=None):
        if context is None:
            context = {}
        return context.get('active_ids', [])

    _defaults = {
        'employees_ids': _get_default_employees
    }

    def eds_file_parsing(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        data = self.browse(cr, uid, ids)[0]
        record = unicode(base64.decodestring(data.eds_file), 'iso8859-4', 'strict').encode('iso8859-4','strict')
        dom = parseString(record)
        file_employees = dom.getElementsByTagName('gigv')
        if file_employees is None:
            return False
        emp_obj = self.pool.get('hr.employee')
        rel_obj = self.pool.get('hr.employee.relief')
        e_ids = [e.id for e in data.employee_ids]
        for fe in file_employees:
            emp_ids = []
            fe_pc = fe.getElementsByTagName('pers_kods')[0].toxml().replace('<pers_kods>').replace('</pers_kods>')
            fe_name = fe.getElementsByTagName('vards_uzvards')[0].toxml().replace('<vards_uzvards>').replace('</vards_uzvards>')
            if fe_pc:
                cr.execute("SELECT id FROM hr_employee WHERE COALESCE(identification_id, '') != '' AND REPLACE(identification_id, '-', '') = %s AND id in %s", (fe_pc, tuple(e_ids),))
                emp_ids = [r['id'] for r in cr.dictfetchall()]
            if (not e_ids) and fe_name:
                cr.execute("SELECT emp.id FROM hr_employee AS emp LEFT JOIN resource_resource AS res ON emp.resource_id = res.id WHERE UPPER(res.name) = %s AND emp.id in %s", (fe_name, tuple(e_ids),))
                emp_ids = [r['id'] for r in cr.dictfetchall()]
            if emp_ids:
                dep_list = []
                dep_main = fe.getElementsByTagName('apgadajamie')
                if dep_main is not None:
                    deps = dep_main[0].getElementsByTagName('apgadajamais')
                    for dep in deps:
                        dep_name = dep.getElementsByTagName('vards_uzvards')[0].toxml().replace('<vards_uzvards>').replace('</vards_uzvards>')
                        dep_df = dep.getElementsByTagName('datums_no')[0].toxml().replace('<datums_no>').replace('</datums_no>')
                        dep_date_from = datetime.strftime(datetime.strptime(dep_df, '%Y-%m-%dT%H:%M:%S').date(), '%Y-%m-%d')
                        dep_dt = dep.getElementsByTagName('datums_lidz')[0].toxml().replace('<datums_lidz>').replace('</datums_lidz>')
                        dep_date_to = datetime.strftime(datetime.strptime(dep_dt, '%Y-%m-%dT%H:%M:%S').date(), '%Y-%m-%d')
                        dep_list.append({
                            'type': 'dependent',
                            'name': dep_name,
                            'date_from': dep_date_from,
                            'date_to': dep_date_to
                        })
                dis_list = []
                add_main = fe.getElementsByTagName('papildu_atvieglojumi')
                if add_main is not None:
                    adds = add_main[0].getElementsByTagName('papildu_atvieglojums')
                    for add in adds:
                        add_type = add.getElementsByTagName('veids')[0].toxml().replace('<veids>').replace('</veids>')
                        dis_type = False
                        if add_type == '1. grupas invalīds':
                            dis_type = 'disability1'
                        if add_type == '2. grupas invalīds':
                            dis_type = 'disability2'
                        if add_type == '3. grupas invalīds':
                            dis_type = 'disability3'
                        if dis_type:
                            dis_df = dep.getElementsByTagName('datums_no')[0].toxml().replace('<datums_no>').replace('</datums_no>')
                            dis_date_from = datetime.strftime(datetime.strptime(dis_df, '%Y-%m-%dT%H:%M:%S').date(), '%Y-%m-%d')
                            dis_dt = dep.getElementsByTagName('datums_lidz')[0].toxml().replace('<datums_lidz>').replace('</datums_lidz>')
                            dis_date_to = datetime.strftime(datetime.strptime(dis_dt, '%Y-%m-%dT%H:%M:%S').date(), '%Y-%m-%d')
                            dis_list.append({
                                'type': dis_type,
                                'name': add_type,
                                'date_from': dis_date_from,
                                'date_to': dis_date_to
                            })
                umm_list = []
                umm_main = fe.getElementsByTagName('prognozetie_mnm')
                if umm_main is not None:
                    umms = umm_main[0].getElementsByTagName('prognozetais_mnm')
                    for umm in umms:
                        umm_name = umm.getElementsByTagName('veids')[0].toxml().replace('<veids>').replace('</veids>')
                        umm_df = dep.getElementsByTagName('datums_no')[0].toxml().replace('<datums_no>').replace('</datums_no>')
                        umm_date_from = datetime.strftime(datetime.strptime(umm_df, '%Y-%m-%dT%H:%M:%S').date(), '%Y-%m-%d')
                        umm_dt = dep.getElementsByTagName('datums_lidz')[0].toxml().replace('<datums_lidz>').replace('</datums_lidz>')
                        umm_date_to = datetime.strftime(datetime.strptime(umm_dt, '%Y-%m-%dT%H:%M:%S').date(), '%Y-%m-%d')
                        umm_amount = umm.getElementsByTagName('summa')[0].toxml().replace('<summa>').replace('</summa>')
                        umm_list.append({
                            'type': 'untaxed_month',
                            'name': umm_name,
                            'date_from': umm_date_from,
                            'date_to': umm_date_to,
                            'amount': float(umm_amount)
                        })
                for emp_id in emp_ids:
                    for dpl in dep_list:
                        cr.execute("""SELECT id FROM hr_employee_relief WHERE type = 'dependent' AND employee_id = %s AND UPPER(name) = %s""", (emp_id, dpl['name'],))
                        dep_ids = [r['id'] for r in cr.dictfetchall()]
                        if dep_ids:
                            rel_obj.write(cr, uid, dep_ids, {
                                'date_from': dpl['date_from'],
                                'date_to': dpl['date_to']
                            }, context=context)
                        else:
                            dep_data = dpl.copy()
                            dep_data.update({'employee_id': emp_id})
                            rel_obj.create(cr, uid, dep_data, context=context)
                    for dsl in dis_list:
                        dis_ids = rel_obj.search(cr, uid, [
                            ('employee_id','=',emp_id),
                            ('type','=',dsl['type']),
                            ('date_from','=',dsl['date_from']),
                            ('date_to','=',dsl['date_to'])
                        ], context=context)
                        if not_dis_ids:
                            dis_data = dsl.copy()
                            dis_data.update({'employee_id': emp_id})
                            rel_obj.create(cr, uid, dis_data, context=context)
                    for uml in umm_list:
                        umm_ids = rel_obj.search(cr, uid, [
                            ('employee_id','=',emp_id),
                            ('type','=','untaxed_month'),
                            ('date_from','=',uml['date_from']),
                            ('date_to','=',uml['date_to'])
                        ], context=context)
                        if umm_ids:
                            rel_obj.write(cr, uid, umm_ids, {
                                'name': uml['name'],
                                'amount': uml['amount']
                            }, context=context)
                        else:
                            umm_data = uml.copy()
                            umm_data.update({'employee_id': emp_id})
                            rel_obj.create(cr, uid, umm_data, context=context)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: