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

class account_asset_turnover(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(account_asset_turnover, self).__init__(cr, uid, name, context=context)
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
            asset_ids = asset_obj.search(self.cr, self.uid, [('confirmation_date','<=',form['to_date']),('confirmation_date','!=',False),'|',('close_date','=',False),('close_date','>=',form['from_date']), '|', ('company_id','=',False), ('company_id','child_of',[form['company_id']])], order='category_id')
        assets = asset_obj.browse(self.cr, self.uid, asset_ids)

        datas1 = {}
        result1 = []

        for asset in assets:
            account_id = asset.category_id.account_asset_id.id
            account_code = asset.category_id.account_asset_id.code
            account_name = asset.category_id.account_asset_id.name

            # Opening balances:
            purchase1 = 0.0
            if asset.confirmation_date != False and form and asset.confirmation_date < form['from_date']:
                purchase1 = asset.purchase_value
            depr1 = asset.accumulated_depreciation
            for line in asset.depreciation_line_ids:
                if line.move_check == True and (form and line.depreciation_date < form['from_date']):
                    depr1 += line.amount
            salvage1 = 0.0
            if asset.close_date != False and form and asset.close_date < form['from_date']:
                salvage1 = asset.salvage_value
            left1 = purchase1 - depr1 - salvage1

            # Purchase:
            purchase2 = 0.0
            if (not form) or (asset.confirmation_date != False and asset.confirmation_date >= form['from_date'] and asset.confirmation_date <= form['to_date']):
                purchase2 = asset.purchase_value
            depr2 = 0.0
            salvage2 = 0.0
            left2 = purchase2 - depr2 - salvage2

            # Asset depreciation:
            purchase3 = 0.0
            depr3 = 0.0
            for line in asset.depreciation_line_ids:
                if line.move_check == True and ((not form) or (line.depreciation_date >= form['from_date'] and line.depreciation_date <= form['to_date'])):
                    depr3 += line.amount
            salvage3 = 0.0
            left3 = purchase3 - depr3 - salvage3

            # Liquidation:
            purchase4 = 0.0
            depr4 = 0.0
            salvage4 = 0.0
            if asset.close_date != False and ((not form) or (asset.close_date <= form['to_date'] and asset.close_date >= form['from_date'])):
                purchase4 = - asset.purchase_value
                depr4 = - asset.accumulated_depreciation
                for line in asset.depreciation_line_ids:
                    if line.move_check == True:
                        depr4 -= line.amount
                salvage4 = - asset.salvage_value
            left4 = round((- (purchase4 - depr4 - salvage4)), 2) + 0

            # Totals:
            purchase_total1 = purchase2 + purchase3 + purchase4
            depr_total1 = depr2 + depr3 + depr4
            salvage_total1 = salvage2 + salvage3 + salvage4
            left_total1 = round((left2 + left3 + left4), 2) + 0
            purchase_total2 = purchase1 + purchase2 + purchase3 + purchase4
            depr_total2 = depr1 + depr2 + depr3 + depr4
            salvage_total2 = salvage1 + salvage3 + salvage3 + salvage4
            left_total2 = round((left1 + left2 + left3 + left4), 2) + 0
            if datas1.get((account_id)):
                purchase1 += datas1[(account_id)]['purchase1']
                depr1 += datas1[(account_id)]['depr1']
                salvage1 += datas1[(account_id)]['salvage1']
                left1 += datas1[(account_id)]['left1']
                purchase2 += datas1[(account_id)]['purchase2']
                depr2 += datas1[(account_id)]['depr2']
                salvage2 += datas1[(account_id)]['salvage2']
                left2 += datas1[(account_id)]['left2']
                purchase3 += datas1[(account_id)]['purchase3']
                depr3 += datas1[(account_id)]['depr3']
                salvage3 += datas1[(account_id)]['salvage3']
                left3 += datas1[(account_id)]['left3']
                purchase4 += datas1[(account_id)]['purchase4']
                depr4 += datas1[(account_id)]['depr4']
                salvage4 += datas1[(account_id)]['salvage4']
                left4 += datas1[(account_id)]['left4']
                purchase_total1 += datas1[(account_id)]['purchase_total1']
                depr_total1 += datas1[(account_id)]['depr_total1']
                salvage_total1 += datas1[(account_id)]['salvage_total1']
                left_total1 += datas1[(account_id)]['left_total1']
                purchase_total2 += datas1[(account_id)]['purchase_total2']
                depr_total2 += datas1[(account_id)]['depr_total2']
                salvage_total2 += datas1[(account_id)]['salvage_total2']
                left_total2 += datas1[(account_id)]['left_total2']
                datas1[(account_id)].clear()
            if not datas1.get((account_id)):
                datas1[(account_id)] = {
                    'account_id': account_id,
                    'account_code': account_code,
                    'account_name': account_name,
                    'purchase1': purchase1,
                    'depr1': depr1,
                    'salvage1': salvage1,
                    'left1': left1,
                    'purchase2': purchase2,
                    'depr2': depr2,
                    'salvage2': salvage2,
                    'left2': left2,
                    'purchase3': purchase3,
                    'depr3': depr3,
                    'salvage3': salvage3,
                    'left3': left3,
                    'purchase4': purchase4,
                    'depr4': depr4,
                    'salvage4': salvage4,
                    'left4': left4,
                    'purchase_total1': purchase_total1,
                    'depr_total1': depr_total1,
                    'salvage_total1': salvage_total1,
                    'left_total1': left_total1,
                    'purchase_total2': purchase_total2,
                    'depr_total2': depr_total2,
                    'salvage_total2': salvage_total2,
                    'left_total2': left_total2
                }
            result1.append(datas1[(account_id)])
        
        for object in result1:  
            if object != {}:
                self.result_asset.append(object)

        return self.result_asset
        
class at_report(osv.AbstractModel):
    _name = 'report.l10n_lv_account_asset.asset_turnover_report'
    _inherit = 'report.abstract_report'
    _template = 'l10n_lv_account_asset.asset_turnover_report'
    _wrapped_report_class = account_asset_turnover

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
