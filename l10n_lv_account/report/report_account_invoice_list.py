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

import time
from openerp.report import report_sxw
from openerp.osv import osv

class report_account_invoice_list(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(report_account_invoice_list, self).__init__(cr, uid, name, context=context)
        self.result_inv = []
        self.localcontext.update({
            'time': time,
            'cr':cr,
            'uid': uid,
            'lines': self.lines,
            'set_company': self.set_company
        })
        self.context = context

    def set_company(self, form):
        return self.pool.get('res.company').browse(self.cr, self.uid, form['company_id'])

    def lines(self, form, ids=[]):
        invoice_obj = self.pool.get('account.invoice')
        inv_ids = self.localcontext.get('active_ids',[])
        if form:
            inv_ids = invoice_obj.search(self.cr, self.uid, [('type','=',form['invoice_type']), '|', ('company_id','=',False), ('company_id','child_of',[form['company_id']])], order='currency_id')
        invoices = invoice_obj.browse(self.cr, self.uid, inv_ids)
        result = []
        datas = {}
        for inv in invoices:
            currency_id = inv.currency_id.id
            currency_name = inv.currency_id.name
            inv_list = [inv]
            amount_total = inv.amount_total
            amount_untaxed = inv.amount_untaxed
            amount_tax = inv.amount_tax
            if datas.get((currency_id)):
                inv_list += datas[(currency_id)]['invoice_list']
                amount_total += datas[(currency_id)]['amount_total']
                amount_untaxed += datas[(currency_id)]['amount_untaxed']
                amount_tax += datas[(currency_id)]['amount_tax']
                datas[(currency_id)].clear()
            if not datas.get((currency_id)):
                datas[(currency_id)] = {
                    'currency_name': currency_name,
                    'invoice_list': inv_list,
                    'amount_total': amount_total,
                    'amount_untaxed': amount_untaxed,
                    'amount_tax': amount_tax
                }
            result.append(datas[(currency_id)])
        for object in result:
            if object != {}:
                self.result_inv.append(object)
        return self.result_inv

class invoice_list(osv.AbstractModel):
    _name = 'report.l10n_lv_account.invoice_list'
    _inherit = 'report.abstract_report'
    _template = 'l10n_lv_account.invoice_list'
    _wrapped_report_class = report_account_invoice_list

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

