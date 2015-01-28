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
from datetime import datetime
from openerp.report import report_sxw
from openerp.osv import osv, fields

class account_asset_list(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(account_asset_list, self).__init__(cr, uid, name, context=context)
        self.result_asset = []
        self.localcontext.update({
            'time': time,
            'cr':cr,
            'uid': uid,
            'lines': self.lines,
        })
        self.context = context

    def lines(self, form, ids=[]):
        asset_obj = self.pool.get('account.asset.asset')
        asset_ids = self.localcontext.get('active_ids',[])
        if form:
            asset_ids = asset_obj.search(self.cr, self.uid, [('confirmation_date','<=',form['date']),('confirmation_date','!=',False),'|',('close_date','=',False),('close_date','>=',form['date']), '|', ('company_id','=',False), ('company_id','child_of',[form['company_id']])], order='category_id')
        assets = asset_obj.browse(self.cr, self.uid, asset_ids)
        result = []
        datas = {}
        for asset in assets:
            account_id = asset.category_id.account_asset_id.id
            account_code = asset.category_id.account_asset_id.code
            account_name = asset.category_id.account_asset_id.name
            book = asset.purchase_value
            depr = 0.0
            for l in asset.depreciation_line_ids:
                if l.move_check == True and ((not form) or l.depreciation_date <= form['date']):
                    depr += l.amount
            left = book - depr
            acc_book = book
            acc_depr = depr
            acc_res = left
            asset_list = [{
                'name': asset.name,
                'book': book,
                'depr': depr,
                'left': left
            }]
            if datas.get((account_id)):
                acc_book += datas[(account_id)]['acc_book']
                acc_depr += datas[(account_id)]['acc_depr']
                acc_res += datas[(account_id)]['acc_res']
                asset_list += datas[(account_id)]['asset_list']
                datas[(account_id)].clear()
            if not datas.get((account_id)):
                datas[(account_id)] = {
                    'account_code': account_code,
                    'account_name': account_name,
                    'acc_book': acc_book,
                    'acc_depr': acc_depr,
                    'acc_res': acc_res,
                    'asset_list': asset_list
                }
            result.append(datas[(account_id)])
        for object in result:
            if object != {}:
                self.result_asset.append(object)
        return self.result_asset

class al_report(osv.AbstractModel):
    _name = 'report.l10n_lv_account_asset.asset_list_report'
    _inherit = 'report.abstract_report'
    _template = 'l10n_lv_account_asset.asset_list_report'
    _wrapped_report_class = account_asset_list

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
