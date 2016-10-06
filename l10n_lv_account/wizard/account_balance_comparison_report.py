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
from openerp.tools.translate import _
import base64
import StringIO
import xlwt

class account_balance_comparison_report(osv.osv_memory):
    _name = "account.balance.comparison.report"
    _description = "Partner Balance Comparison"

    _columns = {
        'date': fields.date('Date', required=True),
        'type': fields.selection([('receivable', 'Receivable'), ('payable', 'Payable')], string='Type', required=True),
        'accountant_id': fields.many2one('hr.employee', 'Accountant', required=True),
        'format': fields.selection([('pdf','PDF')], string='Format', required=True),
        'file_name': fields.char('File Name'),
        'file_save': fields.binary('Save File', readonly=True)
    }

    def _get_default_accountant(self, cr, uid, context=None):
        emp_obj = self.pool.get('hr.employee')
        emp_ids = emp_obj.search(cr, uid, [('job_id.name','in',['Accountant', 'accountant', 'Bookkeeper', 'bookkeeper'])], context=context)
        if not emp_ids:
            emp_ids = emp_obj.search(cr, uid, ['|', ('job_id.name','ilike','accountant'), ('job_id.name','ilike','bookkeeper')], context=context)
        return emp_ids and emp_ids[0] or False

    def _get_default_type(self, cr, uid, context=None):
        if context is None:
            context = {}
        type = False
        if context.get('search_default_customer',False):
            type = 'receivable'
        if context.get('search_default_supplier',False):
            type = 'payable'
        if not type:
            types = []
            p_ids = context.get('active_ids',[])
            for p in self.pool.get('res.partner').browse(cr, uid, p_ids, context=context):
                if p.customer == True and 'receivable' not in types:
                    types.append('receivable')
                if p.supplier == True and 'payable' not in types:
                    types.append('payable')
            if len(types) == 1:
                type = types[0]
        return type

    _defaults = {
        'date': fields.date.context_today,
        'type': _get_default_type,
        'accountant_id': _get_default_accountant,
        'format': 'pdf',
        'file_name': 'Payment_Comparison.xls'
    }

    def _build_contexts(self, cr, uid, ids, data, context=None):
        if context is None:
            context = {}
        result = {}
        result['date'] = 'date' in data['form'] and data['form']['date'] or False
        result['type'] = 'date' in data['form'] and data['form']['type'] or False
        result['accountant_id'] = 'accountant_id' in data['form'] and data['form']['accountant_id'] or False
        result['format'] = 'format' in data['form'] and data['form']['format'] or False
        result['file_name'] = 'format' in data['form'] and data['form']['file_name'] or False
        return result

    def get_transl(self, cr, uid, string, lang, context=None):
        if context is None:
            context = {}
        lang = lang or context.get('lang',False)
        data_obj = self.pool.get('ir.model.data')
        report = data_obj.get_object(cr, uid, 'l10n_lv_account', 'balance_comparison_document', context=context)
        transl_obj = self.pool.get('ir.translation')
        transl_ids = transl_obj.search(cr, uid, [('name','=','website'), ('module','=','l10n_lv_account'), ('type','=','view'), ('res_id','=',report.id), ('src','=',string), ('lang','=',lang)], context=context)
        if transl_ids:
            transl = transl_obj.browse(cr, uid, transl_ids[0], context=context)
            return transl.value
        return string

#    def make_xls_data(self, cr, uid, partner_ids, data, context=None):
#        if context is None:
#            context = {}
#        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
#        user_company = user.company_id
#        partner_obj = self.pool.get('res.partner')
#        wbk = xlwt.Workbook(encoding='iso8859-4')
#        for partner in partner_obj.browse(cr, uid, partner_ids, context=context):
#            sheet = wbk.add_sheet(partner.name)
            # font heigth = size*20
            # cell width = int((1+len(text)*256)
            # cell height = px*20

#            h2_str = self.get_transl(cr, uid, "Mutual payment comparison statement", partner.lang, context=context)
#            style_h2 = xlwt.easyxf("font: bold 1, height 360; align: horiz center, vert center;")
#            sheet.write_merge(r1=0, c1=0, r2=0, c2=5, label=h2_str, style=style_h2)
#            sheet.row(0).height = 1960
#            for i in range(6):
#                sheet.col(i).width = 5000

#            t1r1c1_str1 = self.get_transl(cr, uid, "Company:", partner.lang, context=context) + ' '
#            t1r1c1_str2 = partner.company_id and partner.company_id.name or user_company.name
#            style_t1r1c1_r = xlwt.easyxf("font: height 280;")
#            style_t1r1c1_b = xlwt.easyxf("font: bold 1, height 280;")
#            sheet.write_rich_text(

#        file_data = StringIO.StringIO()
#        wbk.save(file_data)
#        file_data.seek(0)
#        return file_data.read().decode('iso8859-4')

    def open_report(self, cr, uid, ids, context=None):
        data = {}
        data['ids'] = context.get('active_ids',[])
        data['model'] = 'res.partner'
        data['form'] = self.read(cr, uid, ids, ['date', 'type', 'accountant_id', 'format', 'file_name'], context=context)[0]
        for field in ['date', 'type', 'accountant_id', 'format', 'file_name']:
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
#        if data['form']['format'] == 'xls':
#            file_save = self.make_xls_data(cr, uid, context.get('active_ids',[]), data, context=context)
#            file_save_data = base64.encodestring(file_save.encode('iso8859-4'))
#            if data['form']['file_name']:
#                file_name_list = data['form']['file_name'].split('.')
#                format = file_name_list[-1]
#                if format != 'xls':
#                    if len(file_name_list) == 1:
#                        file_name_list.append('xls')
#                    else:
#                        file_name_list[-1] = 'xls'
#                file_name = '.'.join(file_name_list)
#            else:
#                file_name = 'Payment_Comparison.xls'
#            self.write(cr, uid, ids[0], {
#                'file_name': file_name,
#                'file_save': file_save_data
#            }, context=context)
#            return {
#                'name': _('Save document For Payment Comparison'),
#                'res_id': ids[0],
#                'context': context,
#                'view_type': 'form',
#                'view_mode': 'form',
#                'res_model': 'account.balance.comparison.report',
#                'views': [(False,'form')],
#                'type': 'ir.actions.act_window',
#                'target': 'new',
#            }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: