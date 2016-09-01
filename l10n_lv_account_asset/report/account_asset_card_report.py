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
from openerp.osv import osv
from dateutil.relativedelta import relativedelta

class account_asset_card_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(account_asset_card_report, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'cr':cr,
            'uid': uid,
            'get_time_depr_data': self.get_time_depr_data
        })

    def get_time_depr_data(self, o):
        method_number = o.method_number
        asset_obj = self.pool.get('account.asset.asset')
        cur_obj = self.pool.get('res.currency')

        base_date = o.start_date or (o.state == 'open' and o.confirmation_date) or o.purchase_date
        date_val = datetime.strptime(base_date, '%Y-%m-%d')
        if o.next_month:
            month = date_val.month + 1
            year = date_val.year
            if date_val.month == 12:
                month = 1
                year += 1
            date_val = datetime(year, month, 1)
        if (not o.next_month) and (not o.prorata):
            date_val = datetime(date_val.year, date_val.month, 1)
        day = date_val.day
        month = date_val.month
        year = date_val.year
        total_days = (year % 4) and 365 or 366

        undone_dotation_number = asset_obj._compute_board_undone_dotation_nb(self.cr, self.uid, o, date_val, total_days, context=self.localcontext)
        if o.method_time == 'end':
            method_number = undone_dotation_number

        if o.method_time == 'number' and o.accumulated_depreciation != 0.0:
            amount_to_depr = residual_amount = o.purchase_value - o.accumulated_depreciation
            base_amount = 0.0
            for x in range(0, undone_dotation_number):
                i = x + 1
                amount = asset_obj._compute_board_amount(self.cr, self.uid, o, i, residual_amount, amount_to_depr, undone_dotation_number, [], total_days, date_val, context=self.localcontext)
                residual_amount -= amount
                date_val = (datetime(year, month, day) + relativedelta(months=+o.method_period))
                day = date_val.day
                month = date_val.month
                year = date_val.year
                base_amount = amount
                break
            if base_amount != 0.0:
                print '-------------'
                print base_amount
                if o.method == 'linear':
                    method_number += int(o.accumulated_depreciation / base_amount)
                if o.method == 'degressive':
                    test_amount = 0.0
                    residual_amount = base_amount
                    i = 0
                    while (test_amount < o.accumulated_depreciation):
                        test_amount += residual_amount / (o.method_progress_factor * 2)
                        residual_amount += test_amount
                        i += 1
                        if i == 1:
                            residual_amount -= base_amount
                    method_number = i
            print '-----------------------'
            print method_number
        usage_years = (o.method_period * method_number) / 12.0
        usage_months = o.method_period * method_number
        amort_month_val = (o.method_period != 0 and method_number != 0) and (o.purchase_value/(o.method_period*method_number)) or 0.0
        amort_month_perc = (o.purchase_value != 0.0 and o.method_period != 0 and method_number != 0) and (((o.purchase_value/(o.method_period*method_number))*100)/o.purchase_value) or 0.0
        amort_val = (usage_years != 0) and (o.purchase_value/usage_years) or 0.0
        amort_percent = (o.purchase_value != 0.0 and usage_years != 0.0) and (((o.purchase_value/usage_years)*100.0)/o.purchase_value) or 0.0
        return {
            'service_date': o.start_date or (o.state == 'open' and o.confirmation_date) or o.purchase_date,
            'usage_years': usage_years,
            'usage_months': usage_months,
            'amort_month_val': amort_month_val,
            'amort_month_perc': amort_month_perc,
            'amort_val': amort_val,
            'amort_percent': amort_percent
        }

class ac_report(osv.AbstractModel):
    _name = 'report.l10n_lv_account_asset.asset_card_report'
    _inherit = 'report.abstract_report'
    _template = 'l10n_lv_account_asset.asset_card_report'
    _wrapped_report_class = account_asset_card_report

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: