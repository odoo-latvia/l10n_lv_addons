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
from dateutil.relativedelta import relativedelta
from openerp.osv import osv, fields
from openerp import SUPERUSER_ID

class account_asset_category(osv.osv):
    _inherit = 'account.asset.category'
    _order = 'name'

    _columns = {
        'next_month': fields.boolean('Compute from Next Month', help='Indicates that the first depreciation entry for this asset has to be done from the start of the next month following the month of the purchase date.'),
        # depreciation for taxes:
        'account_depreciation_tax_id': fields.many2one('account.account', 'Depreciation Account for Taxes', required=True, domain=[('type','=','other')]),
        'method_tax': fields.selection([('linear','Linear'),('degressive','Degressive')], 'Computation Method', required=True, help="Choose the method to use to compute the amount of depreciation lines.\n"\
            "  * Linear: Calculated on basis of: Gross Value / Number of Depreciations\n" \
            "  * Degressive: Calculated on basis of: Residual Value * Degressive Factor"),
        'method_time_tax': fields.selection([('number','Number of Depreciations'),('end','Ending Date')], 'Time Method', required=True,
                                  help="Choose the method to use to compute the dates and number of depreciation lines.\n"\
                                       "  * Number of Depreciations: Fix the number of depreciation lines and the time between 2 depreciations.\n" \
                                       "  * Ending Date: Choose the time between 2 depreciations and the date the depreciations won't go beyond."),
        'prorata_tax':fields.boolean('Prorata Temporis', help='Indicates that the first depreciation entry for this asset have to be done from the purchase date instead of the first January'),
        'next_month_tax': fields.boolean('Compute from Next Month', help='Indicates that the first depreciation entry for this asset has to be done from the start of the next month following the month of the purchase date.'),
        'method_number_tax': fields.integer('Number of Depreciations', help="The number of depreciations needed to depreciate your asset"),
        'method_period_tax': fields.integer('Period Length', help="State here the time between 2 depreciations, in months", required=True),
        'method_progress_factor_tax': fields.float('Degressive Factor'),
        'method_end_tax': fields.date('Ending date'),
        'account_analytic_tax_id': fields.many2one('account.analytic.account', 'Analytic account'),
    }

    _defaults = {
        'method_tax': 'linear',
        'method_number_tax': 5,
        'method_time_tax': 'number',
        'method_period_tax': 12,
        'method_progress_factor_tax': 0.3,
    }

    def onchange_next_month(self, cr, uid, ids, next_month, context=None):
        res = {'value': {}}
        if next_month == True:
            res['value'] = {'prorata': False}
        return res

    def onchange_prorata(self, cr, uid, ids, prorata, context=None):
        res = {'value': {}}
        if prorata == True:
            res['value'] = {'next_month': False}
        return res

    def onchange_next_month_tax(self, cr, uid, ids, next_month_tax, context=None):
        res = {'value': {}}
        if next_month_tax == True:
            res['value'] = {'prorata_tax': False}
        return res

    def onchange_prorata_tax(self, cr, uid, ids, prorata_tax, context=None):
        res = {'value': {}}
        if prorata_tax == True:
            res['value'] = {'next_month_tax': False}
        return res

class account_asset_asset(osv.osv):
    _inherit = 'account.asset.asset'

    def _compute_board_amount(self, cr, uid, asset, i, residual_amount, amount_to_depr, undone_dotation_number, posted_depreciation_line_ids, total_days, depreciation_date, context=None):
        #by default amount = 0
        amount = 0
        if i == undone_dotation_number:
            amount = residual_amount
        else:
            if asset.method == 'linear':
                amount = amount_to_depr / (undone_dotation_number - len(posted_depreciation_line_ids))
                if asset.prorata:
                    amount = amount_to_depr / asset.method_number
                    days = total_days - float(depreciation_date.strftime('%j'))
                    if i == 1:
                        amount = (amount_to_depr / asset.method_number) / total_days * days
                    elif i == undone_dotation_number:
                        amount = (amount_to_depr / asset.method_number) / total_days * (total_days - days)
                # if next_month:
                if asset.next_month and asset.method_period == 12:
                    amount = amount_to_depr / asset.method_number
                    months = 12 - float(depreciation_date.strftime('%m')) + 1
                    if i == 1:
                        amount = (amount_to_depr / (asset.method_period * asset.method_number)) * months
                    elif i == undone_dotation_number:
                        amount = (amount_to_depr / (asset.method_period * asset.method_number)) * 12
            elif asset.method == 'degressive':
                amount = residual_amount * asset.method_progress_factor
                if asset.prorata:
                    days = total_days - float(depreciation_date.strftime('%j'))
                    if i == 1:
                        amount = (residual_amount * asset.method_progress_factor) / total_days * days
                    elif i == undone_dotation_number:
                        amount = (residual_amount * asset.method_progress_factor) / total_days * (total_days - days)
                # if next_month:
                if asset.next_month and asset.method_period == 12:
                    amount = amount_to_depr / asset.method_number
                    months = asset.method_period - float(depreciation_date.strftime('%m')) + 1
                    if i == 1:
                        amount = (amount_to_depr / (asset.method_period * asset.method_number)) * months
                    elif i == undone_dotation_number:
                        amount = (amount_to_depr / (asset.method_period * asset.method_number)) * 12
        return amount

    def _compute_board_undone_dotation_nb(self, cr, uid, asset, depreciation_date, total_days, context=None):
        undone_dotation_number = asset.method_number
        if asset.method_time == 'end':
            end_date = datetime.strptime(asset.method_end, '%Y-%m-%d')
            undone_dotation_number = 0
            while depreciation_date <= end_date:
                depreciation_date = (datetime(depreciation_date.year, depreciation_date.month, depreciation_date.day) + relativedelta(months=+asset.method_period))
                undone_dotation_number += 1
        if asset.prorata or (asset.next_month and asset.method_period == 12): # includes next_month
            undone_dotation_number += 1
        return undone_dotation_number

    def compute_depreciation_board(self, cr, uid, ids, context=None):
        depreciation_lin_obj = self.pool.get('account.asset.depreciation.line')
        currency_obj = self.pool.get('res.currency')
        for asset in self.browse(cr, uid, ids, context=context):
            if asset.value_residual == 0.0:
                continue
            posted_depreciation_line_ids = depreciation_lin_obj.search(cr, uid, [('asset_id', '=', asset.id), ('move_check', '=', True)],order='depreciation_date desc')
            old_depreciation_line_ids = depreciation_lin_obj.search(cr, uid, [('asset_id', '=', asset.id), ('move_id', '=', False)])
            if old_depreciation_line_ids:
                depreciation_lin_obj.unlink(cr, uid, old_depreciation_line_ids, context=context)

            amount_to_depr = residual_amount = asset.value_residual
            if asset.prorata:
                depreciation_date = datetime.strptime(self._get_last_depreciation_date(cr, uid, [asset.id], context)[asset.id], '%Y-%m-%d')
            # if next_month:
            elif asset.next_month:
                if asset.state == 'open':
                    # depreciation_date = 1st of the next month after confirmation month
                    confirmation_date = datetime.strptime(asset.confirmation_date, '%Y-%m-%d')
                    if confirmation_date.month < 12:
                        month = confirmation_date.month + 1
                    if confirmation_date.month == 12:
                        month = 1
                    depreciation_date = datetime(confirmation_date.year, month, 1)
                else:
                    # depreciation_date = 1st of the next month after purchase month
                    purchase_date = datetime.strptime(asset.purchase_date, '%Y-%m-%d')
                    if purchase_date.month < 12:
                        month = purchase_date.month + 1
                    if purchase_date.month == 12:
                        month = 1
                    depreciation_date = datetime(purchase_date.year, month, 1)
            else:
                # depreciation_date = 1st January of purchase year
                purchase_date = datetime.strptime(asset.purchase_date, '%Y-%m-%d')
                #if we already have some previous validated entries, starting date isn't 1st January but last entry + method period
                if (len(posted_depreciation_line_ids)>0):
                    last_depreciation_date = datetime.strptime(depreciation_lin_obj.browse(cr,uid,posted_depreciation_line_ids[0],context=context).depreciation_date, '%Y-%m-%d')
                    depreciation_date = (last_depreciation_date+relativedelta(months=+asset.method_period))
                else:
                    depreciation_date = datetime(purchase_date.year, 1, 1)
            day = depreciation_date.day
            month = depreciation_date.month
            year = depreciation_date.year
            total_days = (year % 4) and 365 or 366

            undone_dotation_number = self._compute_board_undone_dotation_nb(cr, uid, asset, depreciation_date, total_days, context=context)
            for x in range(len(posted_depreciation_line_ids), undone_dotation_number):
                i = x + 1
                amount = self._compute_board_amount(cr, uid, asset, i, residual_amount, amount_to_depr, undone_dotation_number, posted_depreciation_line_ids, total_days, depreciation_date, context=context)
                company_currency = asset.company_id.currency_id.id
                current_currency = asset.currency_id.id
                # compute amount into company currency
                amount = currency_obj.compute(cr, uid, current_currency, company_currency, amount, context=context)
                residual_amount -= amount
                vals = {
                     'amount': amount,
                     'asset_id': asset.id,
                     'sequence': i,
                     'name': str(asset.id) +'/' + str(i),
                     'remaining_value': residual_amount,
                     'depreciated_value': (asset.purchase_value - asset.salvage_value) - (residual_amount + amount),
                     'depreciation_date': depreciation_date.strftime('%Y-%m-%d'),
                }
                depreciation_lin_obj.create(cr, uid, vals, context=context)
                # Considering Depr. Period as months
                depreciation_date = (datetime(year, month, day) + relativedelta(months=+asset.method_period))
                day = depreciation_date.day
                month = depreciation_date.month
                year = depreciation_date.year
        return True

    def validate(self, cr, uid, ids, context={}):
        if context is None:
            context = {}
        return self.write(cr, uid, ids, {
            'state':'open',
            # confirmation_date is set and Depreciation Board re-computed:
            'confirmation_date': time.strftime('%Y-%m-%d'),
        }, context) and self.compute_depreciation_board(cr, uid, ids, context=context)

    def set_to_close(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'close'}, context=context)
        # returns a wizard for close_date setting:
        return {
            'type': 'ir.actions.act_window',
            'name': 'Set Date Closed for Account Asset',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'account.asset.set.close.date',
            'target': 'new',
            'context': context,
            }

    _columns = {
        'next_month': fields.boolean('Compute from Next Month', readonly=True, states={'draft':[('readonly',False)]}, help='Indicates that the first depreciation entry for this asset has to be done from the start of the next month following the month of the purchase date.'),
        'confirmation_date': fields.date('Date Confirmed'),
        'close_date': fields.date('Date Closed'),
        'accumulated_depreciation': fields.float('Accumulated Depreciation', readonly=True, states={'draft':[('readonly',False)]}),
        # depreciation for taxes:
        'method_tax': fields.selection([('linear','Linear'),('degressive','Degressive')], 'Computation Method', required=True, readonly=True, states={'draft':[('readonly',False)]}, help="Choose the method to use to compute the amount of depreciation lines.\n"\
            "  * Linear: Calculated on basis of: Gross Value / Number of Depreciations\n" \
            "  * Degressive: Calculated on basis of: Residual Value * Degressive Factor"),
        'method_time_tax': fields.selection([('number','Number of Depreciations'),('end','Ending Date')], 'Time Method', required=True, readonly=True, states={'draft':[('readonly',False)]},
                                  help="Choose the method to use to compute the dates and number of depreciation lines.\n"\
                                       "  * Number of Depreciations: Fix the number of depreciation lines and the time between 2 depreciations.\n" \
                                       "  * Ending Date: Choose the time between 2 depreciations and the date the depreciations won't go beyond."),
        'prorata_tax':fields.boolean('Prorata Temporis', readonly=True, states={'draft':[('readonly',False)]}, help='Indicates that the first depreciation entry for this asset have to be done from the purchase date instead of the first January'),
        'next_month_tax': fields.boolean('Compute from Next Month', readonly=True, states={'draft':[('readonly',False)]}, help='Indicates that the first depreciation entry for this asset has to be done from the start of the next month following the month of the purchase date.'),
        'method_number_tax': fields.integer('Number of Depreciations', readonly=True, states={'draft':[('readonly',False)]}, help="The number of depreciations needed to depreciate your asset"),
        'method_period_tax': fields.integer('Number of Months in a Period', required=True, readonly=True, states={'draft':[('readonly',False)]}, help="The amount of time between two depreciations, in months"),
        'method_progress_factor_tax': fields.float('Degressive Factor', readonly=True, states={'draft':[('readonly',False)]}),
        'method_end_tax': fields.date('Ending Date', readonly=True, states={'draft':[('readonly',False)]}),
        'accumulated_depreciation_tax': fields.float('Accumulated Depreciation', readonly=True, states={'draft':[('readonly',False)]}),
    }

    _defaults = {
        'method_tax': 'linear',
        'method_number_tax': 5,
        'method_time_tax': 'number',
        'method_period_tax': 12,
        'method_progress_factor_tax': 0.3,
    }

    def onchange_next_month(self, cr, uid, ids, next_month, context=None):
        res = {'value': {}}
        if next_month == True:
            res['value'] = {'prorata': False}
        return res

    def onchange_prorata(self, cr, uid, ids, prorata, context=None):
        res = {'value': {}}
        if prorata == True:
            res['value'] = {'next_month': False}
        return res

    def onchange_next_month_tax(self, cr, uid, ids, next_month_tax, context=None):
        res = {'value': {}}
        if next_month_tax == True:
            res['value'] = {'prorata_tax': False}
        return res

    def onchange_prorata_tax(self, cr, uid, ids, prorata_tax, context=None):
        res = {'value': {}}
        if prorata_tax == True:
            res['value'] = {'next_month_tax': False}
        return res

    def onchange_method_time_tax(self, cr, uid, ids, method_time_tax='number', context=None):
        res = {'value': {}}
        if method_time_tax != 'number':
            res['value'] = {'prorata_tax': False}
        return res

    def onchange_category_id(self, cr, uid, ids, category_id, context=None):
        res = super(account_asset_asset, self).onchange_category_id(cr, uid, ids, category_id, context=context)
        asset_categ_obj = self.pool.get('account.asset.category')
        if category_id:
            category = asset_categ_obj.browse(cr, uid, category_id, context=context)
            res['value'].update({
                'next_month': category.next_month,
                'method_tax': category.method_tax,
                'method_time_tax': category.method_time_tax,
                'prorata_tax': category.prorata_tax,
                'next_month_tax': category.next_month_tax,
                'method_number_tax': category.method_number_tax,
                'method_period_tax': category.method_period_tax,
                'method_progress_factor_tax': category.method_progress_factor_tax,
                'method_end_tax': category.method_end_tax
            })
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
        return super(account_asset_asset, self).search(cr, uid, args, offset=offset, limit=limit, order=order, context=ctx, count=count)

class account_asset_asset_depreciation_line(osv.osv):
    _inherit = 'account.asset.depreciation.line'

    def create_move(self, cr, uid, ids, context=None):
        context = dict(context or {})
        can_close = False
        asset_obj = self.pool.get('account.asset.asset')
        period_obj = self.pool.get('account.period')
        move_obj = self.pool.get('account.move')
        move_line_obj = self.pool.get('account.move.line')
        currency_obj = self.pool.get('res.currency')
        created_move_ids = []
        asset_ids = []
        for line in self.browse(cr, uid, ids, context=context):
            depreciation_date = line.depreciation_date or time.strftime('%Y-%m-%d') # depreciation_date from line
            period_ids = period_obj.find(cr, uid, depreciation_date, context=context)
            company_currency = line.asset_id.company_id.currency_id.id
            current_currency = line.asset_id.currency_id.id
            context.update({'date': depreciation_date})
            amount = currency_obj.compute(cr, uid, current_currency, company_currency, line.amount, context=context)
            sign = line.asset_id.category_id.journal_id.type == 'purchase' and 1 or -1
            asset_name = line.asset_id.name
            reference = line.name
            move_vals = {
                'name': asset_name,
                'date': depreciation_date,
                'ref': reference,
                'period_id': period_ids and period_ids[0] or False,
                'journal_id': line.asset_id.category_id.journal_id.id,
                }
            move_id = move_obj.create(cr, uid, move_vals, context=context)
            journal_id = line.asset_id.category_id.journal_id.id
            partner_id = line.asset_id.partner_id.id
            move_line_obj.create(cr, uid, {
                'name': asset_name,
                'ref': reference,
                'move_id': move_id,
                'account_id': line.asset_id.category_id.account_depreciation_id.id,
                'debit': 0.0,
                'credit': amount,
                'period_id': period_ids and period_ids[0] or False,
                'journal_id': journal_id,
                'partner_id': partner_id,
                'currency_id': company_currency != current_currency and  current_currency or False,
                'amount_currency': company_currency != current_currency and - sign * line.amount or 0.0,
                'date': depreciation_date,
            })
            move_line_obj.create(cr, uid, {
                'name': asset_name,
                'ref': reference,
                'move_id': move_id,
                'account_id': line.asset_id.category_id.account_expense_depreciation_id.id,
                'credit': 0.0,
                'debit': amount,
                'period_id': period_ids and period_ids[0] or False,
                'journal_id': journal_id,
                'partner_id': partner_id,
                'currency_id': company_currency != current_currency and  current_currency or False,
                'amount_currency': company_currency != current_currency and sign * line.amount or 0.0,
                'analytic_account_id': line.asset_id.category_id.account_analytic_id.id,
                'date': depreciation_date,
                'asset_id': line.asset_id.id
            })
            self.write(cr, uid, line.id, {'move_id': move_id}, context=context)
            created_move_ids.append(move_id)
            asset_ids.append(line.asset_id.id)
        asset_close_ids = [] # list of closable asset ids
        # we re-evaluate the assets to determine whether we can close them
        for asset in asset_obj.browse(cr, uid, list(set(asset_ids)), context=context):
            if currency_obj.is_zero(cr, uid, asset.currency_id, asset.value_residual):
                asset.write({'state': 'close'})
                asset_close_ids.append(asset.id) # add asset to closable list
        # returns closing date setting wizard if closable asset ids exist:
        if asset_close_ids:
            ctx = context.copy()
            ctx.update({'active_ids': asset_close_ids})
            return {
                'type': 'ir.actions.act_window',
                'name': 'Set Date Closed for Account Asset',
                'view_mode': 'form',
                'view_type': 'form',
                'res_model': 'account.asset.set.close.date',
                'target': 'new',
                'context': ctx,
            }
        return created_move_ids

class account_asset_history(osv.osv):
    _inherit = 'account.asset.history'

    _columns = {
        'method_time_tax': fields.selection([('number','Number of Depreciations'),('end','Ending Date')], 'Time Method', required=True,
                                  help="The method to use to compute the dates and number of depreciation lines.\n"\
                                       "Number of Depreciations: Fix the number of depreciation lines and the time between 2 depreciations.\n" \
                                       "Ending Date: Choose the time between 2 depreciations and the date the depreciations won't go beyond."),
        'method_number_tax': fields.integer('Number of Depreciations', help="The number of depreciations needed to depreciate your asset"),
        'method_period_tax': fields.integer('Period Length', help="Time in month between two depreciations"),
        'method_end_tax': fields.date('Ending date'),
    }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
