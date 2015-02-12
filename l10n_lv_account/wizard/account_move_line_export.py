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

from openerp.osv import fields, osv
from lxml import etree
from openerp.tools.translate import _
import time
import base64
import StringIO
import csv
import xlwt

class account_move_line_export(osv.osv_memory):
    _name = 'account.move.line.export'
    _description = 'Account Move Line Export'

    def onchange_chart_id(self, cr, uid, ids, chart_account_id=False, context=None):
        res = {}
        if chart_account_id:
            company_id = self.pool.get('account.account').browse(cr, uid, chart_account_id, context=context).company_id.id
            res['value'] = {'company_id': company_id}
        return res

    _columns = {
        'name': fields.char('File Name', size=32),
        'format': fields.selection([('csv', 'CSV'), ('xls', 'XLS')], 'Format', required=True),
        'chart_account_id': fields.many2one('account.account', 'Chart of Account', help='Select Charts of Accounts', required=True, domain = [('parent_id','=',False)]),
        'company_id': fields.related('chart_account_id', 'company_id', type='many2one', relation='res.company', string='Company', readonly=True),
        'fiscalyear_id': fields.many2one('account.fiscalyear', 'Fiscal Year', help='Keep empty for all open fiscal year'),
        'sort_selection': fields.selection([('l.date', 'Date'),
                                            ('am.name', 'Journal Entry Number'),],
                                            'Entries Sorted by', required=True),
        'target_move': fields.selection([('posted', 'All Posted Entries'),
                                         ('all', 'All Entries'),
                                        ], 'Target Moves', required=True),
        'amount_currency': fields.boolean("With Currency", help="Export data with the currency column if the currency differs from the company currency."),
        'period_from': fields.many2one('account.period', 'Start Period'),
        'period_to': fields.many2one('account.period', 'End Period'),
        'file_save': fields.binary('Save File', readonly=True)
    }

    def _get_account(self, cr, uid, context=None):
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        accounts = self.pool.get('account.account').search(cr, uid, [('parent_id', '=', False), ('company_id', '=', user.company_id.id)], limit=1)
        return accounts and accounts[0] or False

    def _get_fiscalyear(self, cr, uid, context=None):
        if context is None:
            context = {}
        now = time.strftime('%Y-%m-%d')
        company_id = False
        ids = context.get('active_ids', [])
        domain = [('date_start', '<', now), ('date_stop', '>', now)]
        if ids and context.get('active_model') == 'account.account':
            company_id = self.pool.get('account.account').browse(cr, uid, ids[0], context=context).company_id.id
            domain += [('company_id', '=', company_id)]
        fiscalyears = self.pool.get('account.fiscalyear').search(cr, uid, domain, limit=1)
        return fiscalyears and fiscalyears[0] or False

    def _get_start_period(self, cr, uid, context=None):
        if context is None:
            context = {}
        period_id = False
        fiscalyear_id = self._get_fiscalyear(cr, uid, context=context)
        if fiscalyear_id:
            fiscalyear = self.pool.get('account.fiscalyear').browse(cr, uid, fiscalyear_id, context=context)
            for period in fiscalyear.period_ids:
                if period.special == False:
                    period_id = period.id
                    break
        return period_id

    def _get_end_period(self, cr, uid, context=None):
        if context is None:
            context = {}
        period_id = False
        now = time.strftime('%Y-%m-%d')
        fiscalyear_id = self._get_fiscalyear(cr, uid, context=context)
        if fiscalyear_id:
            fiscalyear = self.pool.get('account.fiscalyear').browse(cr, uid, fiscalyear_id, context=context)
            for period in fiscalyear.period_ids:
                if (period.date_start < now) and (period.date_stop > now):
                    period_id = period.id
                    break
        return period_id

    _defaults = {
        'name': 'Journal_Items.csv',
        'format': 'csv',
        'chart_account_id': _get_account,
        'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'account.common.report',context=c),
        'fiscalyear_id': _get_fiscalyear,
        'period_from': _get_start_period,
        'period_to': _get_end_period,
        'sort_selection': 'am.name',
        'target_move': 'posted',
    }

    def onchange_format(self, cr, uid, ids, format, context=None):
        if context is None:
            context = {}
        if format == 'csv':
            val = {'name': 'Journal_Items.csv'}
        if format == 'xls':
            val = {'name': 'Journal_Items.xls'}
        return {'value': val}

    def make_csv_data(self, cr, uid, account_move_line_ids, data, context=None):
        if context is None:
            context = {}
        account_move_line_obj = self.pool.get('account.move.line')
        data_of_file = u"Izpildes datums,Periods,Grāmatojuma numurs,Atsauce,Nr.,Partneris,Reģistrācijas Nr.,Konts,Debets,Kredīts,"
        if data['amount_currency'] == True:
            data_of_file += u"Summa valūtā,Valūta,"
        data_of_file += u"Nosaukums\n"
        for item in account_move_line_obj.browse(cr, uid, account_move_line_ids):
            date = item.date or ""
            period = item.period_id.name or ""
            int_seq_nr = item.internal_sequence_number or ""
            ref = item.ref or ""
            move = item.move_id.name or ""
            partner = item.partner_id.name or ""
            partner_vat = item.partner_id.vat or ""
            account = (item.account_id.code + " " + item.account_id.name)
            debit = str(item.debit)
            credit = str(item.credit)
            amount_cur = str(item.amount_currency)
            if (context.get('lang')) and (context['lang'] == 'lv_LV'):
                debit = '"' + (debit.replace(".", ",")) + '"'
                credit = '"' + (credit.replace(".", ",")) + '"'
                amount_cur = '"' + (amount_cur.replace(".",",")) + '"'
            cur = item.currency_id.name or item.journal_id.company_id.currency_id.name
            name = item.name
            data_of_file += (date + "," + period + "," + int_seq_nr + "," + ref + "," + move + "," + partner + "," + partner_vat + "," + account + "," + debit + "," + credit + ",")
            if data['amount_currency'] == True:
                data_of_file += (amount_cur + "," + cur + ",")
            data_of_file += (name + "\n")
        return data_of_file

    def make_xls_data(self, cr, uid, account_move_line_ids, data, context=None):
        if context is None:
            context = {}
        account_move_line_obj = self.pool.get('account.move.line')
        wbk = xlwt.Workbook(encoding='iso8859-4')
        sheet = wbk.add_sheet('Sheet 1')
        sheet.write(0,0,(u"Izpildes datums"))
        sheet.write(0,1,(u"Periods"))
        sheet.write(0,2,(u"Grāmatojuma numurs"))
        sheet.write(0,3,(u"Atsauce"))
        sheet.write(0,4,(u"Nr."))
        sheet.write(0,5,(u"Partneris"))
        sheet.write(0,6,(u"Reģistrācijas Nr."))
        sheet.write(0,7,(u"Konts"))
        sheet.write(0,8,(u"Debets"))
        sheet.write(0,9,(u"Kredīts"))
        if data['amount_currency'] == True:
            sheet.write(0,10,(u"Summa valūtā"))
            sheet.write(0,11,(u"Valūta"))
            sheet.write(0,12,(u"Nosaukums"))
        if data['amount_currency'] == False:
            sheet.write(0,10,(u"Nosaukums"))
        row = 0
        for item in account_move_line_obj.browse(cr, uid, account_move_line_ids):
            row += 1
            date = item.date or ""
            sheet.write(row,0,date)
            period = item.period_id.name or ""
            sheet.write(row,1,period)
            int_seq_nr = item.internal_sequence_number or ""
            sheet.write(row,2,int_seq_nr)
            ref = item.ref or ""
            sheet.write(row,3,ref)
            move = item.move_id.name or ""
            sheet.write(row,4,move)
            partner = item.partner_id.name or ""
            sheet.write(row,5,partner)
            partner_vat = item.partner_id.vat or ""
            sheet.write(row,6,partner_vat)
            account = (item.account_id.code + " " + item.account_id.name)
            sheet.write(row,7,account)
            debit = item.debit
            sheet.write(row,8,debit)
            credit = item.credit
            sheet.write(row,9,credit)
            amount_cur = item.amount_currency
            cur = item.currency_id.name or item.journal_id.company_id.currency_id.name
            name = item.name
            if data['amount_currency'] == True:
                sheet.write(row,10,amount_cur)
                sheet.write(row,11,cur)
                sheet.write(row,12,name)
            if data['amount_currency'] == False:
                sheet.write(row,10,name)
        file_data = StringIO.StringIO()
        wbk.save(file_data)
        file_data.seek(0)
        return file_data.read().decode('iso8859-4')

    def create_file(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        data = self.read(cr, uid, ids)[0]
        sort = 'id'
        if data['sort_selection'] == 'l.date':
            sort = 'date'
        if data['sort_selection'] == 'am.name':
            sort = 'move_id'
        move_states = ['draft','posted']
        if data['target_move'] == 'posted':
            move_states = ['posted']
        period_obj = self.pool.get('account.period')
        periods_list = period_obj.build_ctx_periods(cr, uid, data['period_from'][0], data['period_to'][0])
        account_move_line_obj = self.pool.get('account.move.line')
        account_move_line_ids = account_move_line_obj.search(cr, uid, [('account_id','child_of',data['chart_account_id'][0]), ('company_id','=',data['company_id'][0]), ('move_id.state','in',move_states), ('period_id','in',periods_list)], order=sort, context=context)

        if data['format'] == 'csv':
            file_save = self.make_csv_data(cr, uid, account_move_line_ids, data, context=context)
            file_save_data = base64.encodestring(file_save.encode('utf8'))
            if data['name']:
                file_name_list = data['name'].split('.')
                format = file_name_list[-1]
                if format != 'csv':
                    if len(file_name_list) == 1:
                        file_name_list.append('csv')
                    else:
                        file_name_list[-1] = 'csv'
                file_name = '.'.join(file_name_list)
            else:
                file_name = 'Journal_Items.csv'
            self.write(cr, uid, ids[0], {'name': file_name, 'file_save': file_save_data}, context=context)
        if data['format'] == 'xls':
            file_save = self.make_xls_data(cr, uid, account_move_line_ids, data, context=context)
            file_save_data = base64.encodestring(file_save.encode('iso8859-4'))
            if data['name']:
                file_name_list = data['name'].split('.')
                format = file_name_list[-1]
                if format != 'xls':
                    if len(file_name_list) == 1:
                        file_name_list.append('xls')
                    else:
                        file_name_list[-1] = 'xls'
                file_name = '.'.join(file_name_list)
            else:
                file_name = 'Journal_Items.xls'
            self.write(cr, uid, ids[0], {'name': file_name, 'file_save': file_save_data}, context=context)
        return {
            'name': _('Save document For Journal Items Export'),
            'res_id': ids[0],
            'context': context,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.move.line.export',
            'views': [(False,'form')],
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

account_move_line_export()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
