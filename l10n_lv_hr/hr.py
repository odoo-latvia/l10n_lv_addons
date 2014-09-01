# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012 ITS-1 (<http://www.its1.lv/>)
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

from openerp import addons
import logging
from openerp.osv import fields, osv
from openerp import tools
_logger = logging.getLogger(__name__)
import time
from openerp.tools.translate import _
from openerp import SUPERUSER_ID

class hr_contract(osv.osv):
    _name = 'hr.contract'
    _inherit = 'hr.contract'

    _columns = {
        'main_duties': fields.text('Main Duties'),
        'additional_duties': fields.text('Additional Duties'),
        'other_terms': fields.text('Other Terms'),
        'employee_name': fields.related('employee_id', 'employee_name', type='char', string='Name', store=True),
        'employee_surname': fields.related('employee_id', 'employee_surname', type='char', string='Surname', store=True),
        'active': fields.related('employee_id', 'active', type='boolean', string='Active'),
        'company_id': fields.related('employee_id', 'company_id', type='many2one', relation='res.company', string='Company')
        }

    _sql_constraints = [('contract_name', 'unique(name)', 'Contract Reference must be unique!')]

    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        if context is None:
            context = {}
        ctx = context.copy()
        if ctx.get('my_company_filter',False) == True:
            ctx['my_company_filter'] = False
            for place, item in enumerate(args):
                if item == ['company_id','=',0]:
                    user = self.pool.get('res.users').browse(cr, SUPERUSER_ID, uid, context=context)
                    company_id = user.company_id and user.company_id.id or False
                    args[place] = ['company_id','=',company_id]
        return super(hr_contract, self).search(cr, uid, args, offset=offset, limit=limit, order=order, context=ctx, count=count)
    
hr_contract()

class hr_employee(osv.osv):
    _name = 'hr.employee'
    _description = 'Employee'
    _inherit = 'hr.employee'

    def onchange_employee_name_surname(self, cr, uid, ids, employee_name, employee_surname, context=None):
        if employee_name and employee_surname:
            return {'value': {'name': employee_name + ' ' + employee_surname}}
        if employee_name and not employee_surname:
            return {'value': {'name': employee_name}}
        if employee_surname and not employee_name:
            return {'value': {'name': employee_surname}}
        if not employee_name and not employee_surname:
            return {'value': {'name': False}}
        return {}

    def onchange_name(self, cr, uid, ids, name, context=None):
        if name:
            zz = name.split(' ',1)
            name1 = zz[0]
            if len(zz) > 1:
                surname1 = zz[1]
            else:
                surname1 = ''
            return {'value': {'employee_name': name1, 'employee_surname': surname1}}
        if not name:
            return {'value': {'employee_name': False, 'employee_surname': False}}
        return {}

    _columns = {
        'address_work_id': fields.many2one('res.partner.address', 'Working Address'),
        'address_declared_id': fields.many2one('res.partner.address', 'Declared Address'),
        'address_residence_id': fields.many2one('res.partner.address', 'Residence Address'),
        'employee_name': fields.char('Name', size=32),
        'employee_surname': fields.char('Surname', size=32),
        'cv_text': fields.text('CV'),
        'passport_issue_date': fields.date('Passport Issue Date'),
        'passport_expire_date': fields.date('Passport Expiration Date'),
        'introductory_done': fields.boolean('Introductory Done'),
        'contract_date_end': fields.related('contract_id', 'date_end', type='date', string='Contract End Date'),
        'contract_date_start': fields.related('contract_id', 'date_start', type='date', string='Contract Start Date'),
    }

    _sql_constraints = [('unique_employee_id', 'unique(identification_id)', 'Identification No. must be unique!')]

    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}
        name = vals.get('name',False)
        if name:
            emp_name_ids = self.search(cr, uid, [('name','=',name)], context=context)
            if emp_name_ids:
                raise osv.except_osv(_("Cannot create employee !"), _("An employee with the given name already exists!"))
        return super(hr_employee, self).create(cr, uid, vals, context=context)

    def write(self, cr, uid, ids, vals, context=None):
        if context is None:
            context = {}
        name = vals.get('name',False)
        if name:
            emp_name_ids = self.search(cr, uid, [('name','=',name)], context=context)
            if emp_name_ids:
                raise osv.except_osv(_("Cannot update employee !"), _("An employee with the given name already exists!"))
        return super(hr_employee, self).write(cr, uid, ids, vals, context=context)

    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        if context is None:
            context = {}
        ctx = context.copy()
        if ctx.get('my_company_filter',False) == True:
            ctx['my_company_filter'] = False
            for place, item in enumerate(args):
                if item == ['company_id','=',0]:
                    user = self.pool.get('res.users').browse(cr, SUPERUSER_ID, uid, context=context)
                    company_id = user.company_id and user.company_id.id or False
                    args[place] = ['company_id','=',company_id]
        return super(hr_employee, self).search(cr, uid, args, offset=offset, limit=limit, order=order, context=ctx, count=count)

hr_employee()

class hr_department(osv.osv):
    _inherit = 'hr.department'

    _columns = {
        'code': fields.char('Code', size=16)
    }

    def name_get(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        res = []
        for record in self.browse(cr, uid, ids, context=context):
            code = record.code
            name = record.name
            string = name
            if code:
                string = code
            tit = "%s" % (string)
            res.append((record.id, tit))
        return res

    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        if context is None:
            context = {}
        ctx = context.copy()
        if ctx.get('my_company_filter',False) == True:
            ctx['my_company_filter'] = False
            for place, item in enumerate(args):
                if item == ['company_id','=',0]:
                    user = self.pool.get('res.users').browse(cr, SUPERUSER_ID, uid, context=context)
                    company_id = user.company_id and user.company_id.id or False
                    args[place] = ['company_id','=',company_id]
        return super(hr_department, self).search(cr, uid, args, offset=offset, limit=limit, order=order, context=ctx, count=count)

hr_department()

class hr_job(osv.osv):
    _inherit = "hr.job"

    def _no_of_employee(self, cr, uid, ids, name, args, context=None):
        res = {}
        for job in self.browse(cr, uid, ids, context=context):
            employee_count = 0.0
            for emp in job.employee_ids:
                if emp.active == True:
                    employee_count += 1.0
            res[job.id] = {
                'no_of_employee': employee_count,
                'expected_employees': employee_count + job.no_of_recruitment,
            }
        return res

    def _get_job_position(self, cr, uid, ids, context=None):
        res = []
        for employee in self.pool.get('hr.employee').browse(cr, uid, ids, context=context):
            if employee.job_id:
                res.append(employee.job_id.id)
        return res

    _columns = {
        'expected_employees': fields.function(_no_of_employee, string='Total Forecasted Employees',
            help='Expected number of employees for this job position after new recruitment.',
            store = {
                'hr.job': (lambda self,cr,uid,ids,c=None: ids, ['no_of_recruitment'], 10),
                'hr.employee': (_get_job_position, ['job_id'], 10),
            },
            multi='no_of_employee'),
        'no_of_employee': fields.function(_no_of_employee, string="Current Number of Employees",
            help='Number of employees currently occupying this job position.',
            store = {
                'hr.employee': (_get_job_position, ['job_id'], 10),
            },
            multi='no_of_employee'),
    }

hr_job()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
