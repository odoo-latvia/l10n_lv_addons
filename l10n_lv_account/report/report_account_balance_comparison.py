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

import time
from openerp.report import report_sxw
from openerp.osv import osv

class report_account_balance_comparison(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(report_account_balance_comparison, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'cr':cr,
            'uid': uid,
            'form_address': self.form_address,
            'get_accountant': self.get_accountant,
            'get_line_data': self.get_line_data
        })
        self.context = context

    def form_address(self, o):
        addr_list = []
        if o.street:
            addr_list.append(o.street)
        if o.street2:
            addr_list.append(o.street2)
        if o.city:
            addr_list.append(o.city)
        if o.state_id:
            addr_list.append(o.state_id.name)
        if o.zip:
            addr_list.append(o.zip)
        if o.country_id:
            addr_list.append(o.country_id.name)
        return addr_list and ", ".join(addr_list) or ''

    def get_accountant(self, a_id):
        return self.pool.get('hr.employee').browse(self.cr, self.uid, a_id, context=self.context).name

    def get_line_data(self, date, type, partner):
        res = {
            'lines': [],
            'total_debit': 0.0,
            'total_credit': 0.0
        }
        type_list = ['receivable','payable']
        if type:
            type_list = [type]
        ml_obj = self.pool.get('account.move.line')
        # ['&', ('reconcile_id', '=', False), '&', 
#                            ('account_id.active','=', True), '&', ('account_id.type', '=', 'receivable'), ('state', '!=', 'draft')]
        ml_ids = ml_obj.search(self.cr, self.uid, [('partner_id','=',partner.id), ('account_id.active','=',True), ('account_id.type','in',type_list), ('state','!=','draft'), ('date','<=',date), '|', ('reconcile_id','=',False), ('reconcile_id.create_date','>',date)], context=self.context)
        for ml in ml_obj.browse(self.cr, self.uid, ml_ids, context=self.context):
            res['lines'].append({
                'debit': ml.debit,
                'credit': ml.credit,
                'name': ml.move_id and ml.move_id.name or ml.name
            })
            res['total_debit'] += ml.debit
            res['total_credit'] += ml.credit
            if ml.reconcile_partial_id and ml.reconcile_partial_id.create_date <= date:
                for pml in ml.reconcile_partial_id.line_partial_ids:
                    if pml.id not in ml_ids:
                        res['lines'].append({
                            'debit': pml.debit,
                            'credit': pml.credit,
                            'name': ml.move_id and ml.move_id.name or ml.name
                        })
                        res['total_debit'] += pml.debit
                        res['total_credit'] += pml.credit
        return res

class balance_comparison(osv.AbstractModel):
    _name = 'report.l10n_lv_account.balance_comparison'
    _inherit = 'report.abstract_report'
    _template = 'l10n_lv_account.balance_comparison'
    _wrapped_report_class = report_account_balance_comparison

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: