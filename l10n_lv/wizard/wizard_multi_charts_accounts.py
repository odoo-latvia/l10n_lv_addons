# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 ITS-1 (<http://www.its1.lv/>)
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

import openerp.tools
from openerp.osv import  osv, fields
import openerp.addons
import os
from openerp.tools.translate import _

class wizard_multi_charts_accounts(osv.osv_memory):
    _inherit = 'wizard.multi.charts.accounts'

    def onchange_chart_template_id(self, cr, uid, ids, chart_template_id=False, context=None):
        res = super(wizard_multi_charts_accounts, self).onchange_chart_template_id(cr, uid, ids, chart_template_id=chart_template_id, context=context)
        obj_data = self.pool.get('ir.model.data')
        lv_chart_template = obj_data.get_object_reference(cr, uid, 'l10n_lv', 'lv_2012_chart_1')
        lv_chart_template = lv_chart_template and lv_chart_template[1] or False
        if chart_template_id == lv_chart_template:
            lv_sale_tax = obj_data.get_object_reference(cr, uid, 'l10n_lv', 'lv_tax_PVN-SR')
            res['value']['sale_tax'] = lv_sale_tax and lv_sale_tax[1] or False
            lv_purchase_tax = obj_data.get_object_reference(cr, uid, 'l10n_lv', 'lv_tax_Pr-SR')
            res['value']['purchase_tax'] = lv_purchase_tax and lv_purchase_tax[1] or False
            res['value'].update({'purchase_tax_rate': 21.0, 'sale_tax_rate': 21.0})
        return res

    def _remove_unnecessary_account_fiscal_position_tax_templates(self, cr, uid, ids, context=None):
        acc_fpos_tax_tmp_obj = self.pool.get('account.fiscal.position.tax.template')
        data_obj = self.pool.get('ir.model.data')
        rem_ids = []
        rem_list = [
            'fiscal_position_normal_taxes',
            'fiscal_position_tax_exempt'
        ]
        for item in rem_list:
            rem_ids.append(data_obj.get_object(cr, uid, 'account', item).id)
        res = {}
        if rem_ids:
            res = acc_fpos_tax_tmp_obj.unlink(cr, uid, rem_ids)
        return res

    def _remove_unnecessary_account_fiscal_position_templates(self, cr, uid, ids, context=None):
        acc_fpos_tmp_obj = self.pool.get('account.fiscal.position.template')
        data_obj = self.pool.get('ir.model.data')
        rem_ids = []
        rem_list = [
            'fiscal_position_normal_taxes_template1',
            'fiscal_position_tax_exempt_template2'
        ]
        for item in rem_list:
            rem_ids.append(data_obj.get_object(cr, uid, 'account', item).id)
        res = {}
        if rem_ids:
            res = acc_fpos_tmp_obj.unlink(cr, uid, rem_ids)
        return res

    def _remove_unnecessary_account_tax_templates(self, cr, uid, ids, context=None):
        acc_tax_tmp_obj = self.pool.get('account.tax.template')
        data_obj = self.pool.get('ir.model.data')
        rem_ids = []
        rem_list = [
            'otaxs',
            'otaxr',
            'otaxx',
            'otaxo',
            'itaxs',
            'itaxr',
            'itaxx',
            'itaxo'
        ]
        for item in rem_list:
            rem_ids.append(data_obj.get_object(cr, uid, 'account', item).id)
        res = {}
        if rem_ids:
            res = acc_tax_tmp_obj.unlink(cr, uid, rem_ids)
        return res

    def _remove_unnecessary_account_tax_code_templates(self, cr, uid, ids, context=None):
        acc_tax_code_tmp_obj = self.pool.get('account.tax.code.template')
        data_obj = self.pool.get('ir.model.data')
        rem_ids = []
        rem_list = [
            'tax_code_chart_root',
            'tax_code_balance_net',
            'tax_code_input',
            'tax_code_input_S',
            'tax_code_input_R',
            'tax_code_input_X',
            'tax_code_input_O',
            'tax_code_output',
            'tax_code_output_S',
            'tax_code_output_R',
            'tax_code_output_X',
            'tax_code_output_O',
            'tax_code_base_net',
            'tax_code_base_purchases',
            'tax_code_purch_S',
            'tax_code_purch_R',
            'tax_code_purch_X',
            'tax_code_purch_O',
            'tax_code_base_sales',
            'tax_code_sales_S',
            'tax_code_sales_R',
            'tax_code_sales_X',
            'tax_code_sales_O'
        ]
        for item in rem_list:
            rem_ids.append(data_obj.get_object(cr, uid, 'account', item).id)
        res = {}
        if rem_ids:
            res = acc_tax_code_tmp_obj.unlink(cr, uid, rem_ids)
        return res

    def _remove_unnecessary_account_templates(self, cr, uid, ids, context=None):
        acc_template_obj = self.pool.get('account.account.template')
        data_obj = self.pool.get('ir.model.data')
        rem_ids = []
        rem_list = [
            'conf_chart0',
            'conf_bal',
            'conf_fas',
            'conf_xfa',
            'conf_nca',
            'conf_cas',
            'conf_stk',
            'conf_a_recv',
            'conf_ova',
            'conf_bnk',
            'conf_o_income',
            'conf_cli',
            'conf_a_pay',
            'conf_iva',
            'conf_a_reserve_and_surplus',
            'conf_o_expense',
            'conf_gpf',
            'conf_rev',
            'conf_a_sale',
            'conf_cos',
            'conf_cog',
            'conf_ovr',
            'conf_a_expense',
            'conf_a_salary_expense',
            'conf_a_sale',
            'conf_a_expense'
        ]
        for item in rem_list:
            rem_ids.append(data_obj.get_object(cr, uid, 'account', item).id)
        res = {}
        if rem_ids:
            res = acc_template_obj.unlink(cr, uid, rem_ids)
        return res

    def _remove_unnecessary_account_charts(self, cr, uid, ids, context=None):
        acc_chart_tmp_obj = self.pool.get('account.chart.template')
        data_obj = self.pool.get('ir.model.data')
        chart_tmp_id = data_obj.get_object(cr, uid, 'account', 'configurable_chart_template').id
        res = acc_chart_tmp_obj.unlink(cr, uid, chart_tmp_id)
        return res

    def _remove_unnecessary_account_types(self, cr, uid, ids, context=None):
        acc_type_obj = self.pool.get('account.account.type')
        data_obj = self.pool.get('ir.model.data')
        rem_ids = []
        rem_list = [
            'data_account_type_receivable',
            'data_account_type_payable',
            'data_account_type_bank',
            'data_account_type_cash',
            'data_account_type_asset',
            'account_type_asset_view1',
            'data_account_type_liability',
            'account_type_liability_view1',
            'data_account_type_income',
            'account_type_income_view1',
            'data_account_type_expense',
            'account_type_expense_view1',
#            'account_type_cash_equity',
            'conf_account_type_equity',
            'conf_account_type_tax',
            'conf_account_type_chk',
        ]
        for item in rem_list:
            rem_ids.append(data_obj.get_object(cr, uid, 'account', item).id)

        res = {}
        mod_obj = self.pool.get('ir.module.module')
        acc_mod_ids = mod_obj.search(cr, uid, [('name','=','account')])
        allow = True
        if acc_mod_ids:
            acc_mod = mod_obj.browse(cr, uid, acc_mod_ids[0])
            if acc_mod.demo == True:
                allow = False
        if rem_ids and allow == True:
            res = acc_type_obj.unlink(cr, uid, rem_ids)
        return res

    def execute(self, cr, uid, ids, context=None):
        self._remove_unnecessary_account_fiscal_position_tax_templates(cr, uid, ids, context=context)
        self._remove_unnecessary_account_fiscal_position_templates(cr, uid, ids, context=context)
        self._remove_unnecessary_account_tax_templates(cr, uid, ids, context=context)
        self._remove_unnecessary_account_tax_code_templates(cr, uid, ids, context=context)
        self._remove_unnecessary_account_templates(cr, uid, ids, context=context)
        self._remove_unnecessary_account_charts(cr, uid, ids, context=context)
        self._remove_unnecessary_account_types(cr, uid, ids, context=context)
        return super(wizard_multi_charts_accounts, self).execute(cr, uid, ids, context=context)

    def _prepare_bank_account(self, cr, uid, line, new_code, acc_template_ref, ref_acc_bank, company_id, context=None):
        res = super(wizard_multi_charts_accounts, self)._prepare_bank_account(cr, uid, line=line, new_code=new_code, acc_template_ref=acc_template_ref, ref_acc_bank=ref_acc_bank, company_id=company_id, context=context)
        obj_data = self.pool.get('ir.model.data')
        lv_bank_acc = obj_data.get_object_reference(cr, uid, 'l10n_lv', 'lv_2012_account_262')
        lv_bank_acc = lv_bank_acc and lv_bank_acc[1] or False
        lv_cash_acc = obj_data.get_object_reference(cr, uid, 'l10n_lv', 'lv_2012_account_261')
        lv_cash_acc = lv_cash_acc and lv_cash_acc[1] or False
        if ref_acc_bank.id in [lv_bank_acc, lv_cash_acc]:
            res['type'] = 'other'
            tmp = obj_data.get_object_reference(cr, uid, 'l10n_lv', 'account_type_2012_2_5')
            tmp_type = tmp and tmp[1] or False
            res['user_type'] = tmp_type
        return res

    def _create_bank_journals_from_o2m(self, cr, uid, obj_wizard, company_id, acc_template_ref, context=None):
        '''
        This function creates bank journals and its accounts for each line encoded in the field bank_accounts_id of the
        wizard.

        :param obj_wizard: the current wizard that generates the COA from the templates.
        :param company_id: the id of the company for which the wizard is running.
        :param acc_template_ref: the dictionary containing the mapping between the ids of account templates and the ids
            of the accounts that have been generated from them.
        :return: True
        '''
        obj_acc = self.pool.get('account.account')
        obj_journal = self.pool.get('account.journal')
        code_digits = obj_wizard.code_digits

        # Build a list with all the data to process
        journal_data = []
        if obj_wizard.bank_accounts_id:
            for acc in obj_wizard.bank_accounts_id:
                vals = {
                    'acc_name': acc.acc_name,
                    'account_type': acc.account_type,
                    'currency_id': acc.currency_id.id,
                }
                journal_data.append(vals)
        obj_data = self.pool.get('ir.model.data')
        # --> New: lv_chart_template for testing
        lv_chart_template = obj_data.get_object_reference(cr, uid, 'l10n_lv', 'lv_2012_chart_1')
        lv_chart_template = lv_chart_template and lv_chart_template[1] or False
        ref_acc_bank = obj_wizard.chart_template_id.bank_account_view_id
        ref_acc_cash = obj_wizard.chart_template_id.cash_account_view_id # --> New: Cash Account
        if journal_data and not ref_acc_bank.code:
            raise osv.except_osv(_('Configuration Error !'), _('The bank account defined on the selected chart of accounts hasn\'t a code.'))
        # --> New: Cash Account
        if (obj_wizard.chart_template_id.id == lv_chart_template) and (journal_data and not ref_acc_cash.code):
            raise osv.except_osv(_('Configuration Error !'), _('The cash account defined on the selected chart of accounts hasn\'t a code.'))

        current_num = 1
        current_num_bank = 1 # --> New: Bank Account
        current_num_cash = 1 # --> New: Cash Account
        for line in journal_data:
            # --> New: Check if LV Chart Template
            if (obj_wizard.chart_template_id.id == lv_chart_template):
                if line['account_type'] == 'bank':
                    # Seek the next available number for the account code
                    while True:
                        new_code_bank = str(ref_acc_bank.code.ljust(code_digits-len(str(current_num_bank)), '0')) + str(current_num_bank)
                        ids = obj_acc.search(cr, uid, [('code', '=', new_code_bank), ('company_id', '=', company_id)])
                        if not ids:
                            break
                        else:
                            current_num_bank += 1
                    # Create the default debit/credit accounts for this bank journal
                    vals_bank = self._prepare_bank_account(cr, uid, line, new_code_bank, acc_template_ref, ref_acc_bank, company_id, context=context)
                    default_bank_account_id  = obj_acc.create(cr, uid, vals_bank, context=context)
                    #create the bank journal
                    vals_journal_bank = self._prepare_bank_journal(cr, uid, line, current_num_bank, default_bank_account_id, company_id, context=context)
                    obj_journal.create(cr, uid, vals_journal_bank)
                    current_num_bank += 1
                if line['account_type'] == 'cash':
                    # Seek the next available number for the account code
                    while True:
                        new_code_cash = str(ref_acc_cash.code.ljust(code_digits-len(str(current_num_cash)), '0')) + str(current_num_cash)
                        ids = obj_acc.search(cr, uid, [('code', '=', new_code_cash), ('company_id', '=', company_id)])
                        if not ids:
                            break
                        else:
                            current_num_cash += 1
                    # Create the default debit/credit accounts for this bank journal
                    vals_cash = self._prepare_bank_account(cr, uid, line, new_code_cash, acc_template_ref, ref_acc_cash, company_id, context=context)
                    default_cash_account_id  = obj_acc.create(cr, uid, vals_cash, context=context)
                    #create the bank journal
                    vals_journal_cash = self._prepare_bank_journal(cr, uid, line, current_num_cash, default_cash_account_id, company_id, context=context)
                    obj_journal.create(cr, uid, vals_journal_cash)
                    current_num_cash += 1
            else:
                # Seek the next available number for the account code
                while True:
                    new_code = str(ref_acc_bank.code.ljust(code_digits-len(str(current_num)), '0')) + str(current_num)
                    ids = obj_acc.search(cr, uid, [('code', '=', new_code), ('company_id', '=', company_id)])
                    if not ids:
                        break
                    else:
                        current_num += 1
                # Create the default debit/credit accounts for this bank journal
                vals = self._prepare_bank_account(cr, uid, line, new_code, acc_template_ref, ref_acc_bank, company_id, context=context)
                default_account_id  = obj_acc.create(cr, uid, vals, context=context)

                #create the bank journal
                vals_journal = self._prepare_bank_journal(cr, uid, line, current_num, default_account_id, company_id, context=context)
                obj_journal.create(cr, uid, vals_journal)
                current_num += 1
        return True

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

