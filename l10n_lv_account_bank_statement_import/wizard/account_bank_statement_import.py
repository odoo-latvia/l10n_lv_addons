# -*- encoding: utf-8 -*-
##############################################################################
#
#    Part of Odoo.
#    Copyright (C) 2016 ITS-1 (<http://www.its1.lv/>)
#                       E-mail: <info@its1.lv>
#                       Address: <Vienibas gatve 109 LV-1058 Riga Latvia>
#                       Phone: +371 67289467
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

import base64

from openerp import api, fields, models, _
from openerp.exceptions import UserError
from openerp.addons.base.res.res_bank import sanitize_account_number

from xml.dom.minidom import getDOMImplementation, parseString

class AccountBankStatementImported(models.TransientModel):
    _name = 'account.bank.statement.imported'

    @api.model
    def _default_currency(self):
        user = self.env['res.users'].browse(self._uid)
        currency_id = user.company_id.currency_id.id
        return currency_id

    wizard_id = fields.Many2one('account.bank.statement.import', string='Wizard')
    last_statement = fields.Char('Last statements for selected accounts')
    last_balance_end = fields.Monetary('Ending Balance')
    wrong_balance = fields.Boolean('Wrong Balance')
    currency_id = fields.Many2one('res.currency', string='Currency', default=_default_currency)

class AccountBankStatementImporting(models.TransientModel):
    _name = 'account.bank.statement.importing'

    @api.model
    def _default_currency(self):
        user = self.env['res.users'].browse(self._uid)
        currency_id = user.company_id.currency_id.id
        return currency_id

    wizard_id = fields.Many2one('account.bank.statement.import', string='Wizard')
    current_statement = fields.Char('Statements to import')
    current_balance_start = fields.Monetary('Starting Balance')
    wrong_balance = fields.Boolean('Wrong Balance')
    currency_id = fields.Many2one('res.currency', string='Currency', default=_default_currency)

class AccountBankStatementImport(models.TransientModel):
    _inherit = 'account.bank.statement.import'

    @api.model
    def _default_journal(self):
        journals = self.env['account.journal'].search([('type','=','bank')])
        journal_id = journals and journals[0].id or False
        return journal_id

    format = fields.Selection([('ofx','.OFX'), ('fidavista','FiDAViSta')], string='Format', required=True)
    journal_id = fields.Many2one('account.journal', string='Journal', domain=[('type','=','bank')], default=_default_journal)
    currency_id = fields.Many2one('res.currency', string='Currency')
    flag = fields.Boolean('Continue Anyway', help='If checked, continues without comparing balances.', default=False)
    wrong_balance = fields.Boolean('Wrong Balance', default=False)
    imported_statement_ids = fields.One2many('account.bank.statement.imported', 'wizard_id', string='Imported Statements')
    importing_statement_ids = fields.One2many('account.bank.statement.importing', 'wizard_id', string='Statements to Import')

    @api.onchange('format', 'data_file', 'journal_id')
    def _onchange_data_file(self):
        try:
            datafile = self.data_file
        except:
            raise UserError(_('Wizard in incorrect state. Please hit the Cancel button'))
        if self.format == 'fidavista' and datafile:
            # decoding and encoding for string parsing; parseString() method:
            record = unicode(base64.decodestring(datafile), 'iso8859-4', 'strict').encode('iso8859-4','strict')
            dom = parseString(record)

            # getting date values:
            prep_date = dom.getElementsByTagName('PrepDate')[0].toxml().replace('<PrepDate>','').replace('</PrepDate>','')
            start_date = dom.getElementsByTagName('StartDate')[0].toxml().replace('<StartDate>','').replace('</StartDate>','')
            end_date = dom.getElementsByTagName('EndDate')[0].toxml().replace('<EndDate>','').replace('</EndDate>','')

            # getting the accountsets to browse through and giving start values for fields:
            accountsets = dom.getElementsByTagName('AccountSet')
            wrong_balance = False
            result_imported = []
            result_importing = []
            currencies = []
            bank_obj = self.env['res.partner.bank']
            statement_obj = self.env['account.bank.statement']
            cur_obj = self.env['res.currency']
            for company_account in accountsets:
                latest_bank_statement = False
                latest_bank_statement_name = False
                latest_bank_statement_balance_end = False
                latest_bank_statement_currency = False

                # testing, whether the Company's bank account is defined in the system:
                company_acc_no = company_account.getElementsByTagName('AccNo')[0].toxml().replace('<AccNo>','').replace('</AccNo>','')
                company_acc_no_list = list(company_acc_no)
                company_acc_no_list.insert(4,' ')
                company_acc_no_list.insert(9,' ')
                company_acc_no_list.insert(14,' ')
                company_acc_no_list.insert(19,' ')
                company_acc_no_list.insert(24,' ')
                company_acc_no_2 = "".join(company_acc_no_list)
                test_acc_no = bank_obj.search([('acc_number','=',company_acc_no)])
                if not test_acc_no:
                    test_acc_no = bank_obj.search([('acc_number','=',company_acc_no_2)])

                # getting Statement Reference:
                statement_name = company_acc_no + ' ' + start_date+ ':' + end_date

                # getting and checking balances:
                balance_start = company_account.getElementsByTagName('OpenBal')[0].toxml().replace('<OpenBal>','').replace('</OpenBal>','')
                if test_acc_no:
                    bank_statements = statement_obj.search([('bank_account_id', '=', test_acc_no[0].id)], order='date asc')
                    if bank_statements:
                        latest_bank_statement = bank_statements[-1]
                        latest_bank_statement_name = latest_bank_statement.name
                        latest_bank_statement_balance_end = latest_bank_statement.balance_end_real
                        latest_bank_statement_currency = latest_bank_statement.currency_id

                        if latest_bank_statement.balance_end_real != float(balance_start):
                            wrong_balance = True

                # creating values for already imported data:
                if latest_bank_statement:
                    datas_imported = {
                        'last_statement': latest_bank_statement_name,
                        'last_balance_end': latest_bank_statement_balance_end,
                        'wrong_balance': wrong_balance
                    }
                    if latest_bank_statement_currency:
                        datas_imported.update({
                            'currency_id': latest_bank_statement_currency.id
                        })
                    result_imported.append((0, 0, datas_imported))

                datas_importing = {
                    'current_statement': statement_name,
                    'current_balance_start': float(balance_start),
                    'wrong_balance': wrong_balance
                }

                # get importing currency
                currency = company_account.getElementsByTagName('Ccy')[0].toxml().replace('<Ccy>','').replace('</Ccy>','')
                currencies_c = cur_obj.search([('name','=',currency)])
                if not currencies_c:
                    currencies_c = cur_obj.search([('name','=',currency), ('active','=',False)])
                    if currencies_c:
                        currencies_c.write({'active': True})
                if currencies_c:
                    if currencies_c[0] not in currencies:
                        currencies.append(currencies_c[0])
                    datas_importing.update({
                        'currency_id': currencies_c[0].id
                    })

                result_importing.append((0, 0, datas_importing))

            self.imported_statement_ids = result_imported 
            self.importing_statement_ids = result_importing
            self.wrong_balance = wrong_balance

            j_domain = [('type','=','bank')]
            if currencies:
                cur_ids = [c.id for c in currencies]
                j_domain = [('type','=','bank'), '|', '&', ('currency_id','!=',False), ('currency_id','in',cur_ids), '&', ('currency_id','=',False), ('company_id.currency_id','in',cur_ids)]
                self.currency_id = currencies[0].id
                
            j_test_ids = self.env['account.journal'].search(j_domain)
            j_id = self.journal_id.id
            if j_id not in [j.id for j in j_test_ids]:
                j_id = j_test_ids and j_test_ids[0].id or False
                self.journal_id = j_id

            return {'domain': {'journal_id': j_domain}}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: