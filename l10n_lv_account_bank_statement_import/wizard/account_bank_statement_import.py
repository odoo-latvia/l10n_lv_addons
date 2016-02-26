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

    @api.multi
    def fidavista_parsing(self):
        self.ensure_one()
        try:
            datafile = self.data_file
        except:
            raise UserError(_('Wizard in incorrect state. Please hit the Cancel button'))

        # decoding and encoding for string parsing; parseString() method:
        record = unicode(base64.decodestring(datafile), 'iso8859-4', 'strict').encode('iso8859-4','strict')
        dom = parseString(record)

        # getting start values:
        prep_date = dom.getElementsByTagName('PrepDate')[0].toxml().replace('<PrepDate>','').replace('</PrepDate>','')
        start_date = dom.getElementsByTagName('StartDate')[0].toxml().replace('<StartDate>','').replace('</StartDate>','')
        end_date = dom.getElementsByTagName('EndDate')[0].toxml().replace('<EndDate>','').replace('</EndDate>','')

        # going through information about the accounts:
        bank_obj = self.env['res.partner.bank']
        bank_statement_obj = self.env['account.bank.statement']
        bank_statement_line_obj = self.env['account.bank.statement.line']
        partner_obj = self.env['res.partner']
        cur_obj = self.env['res.currency']
        accountsets = dom.getElementsByTagName('AccountSet')
        for company_account in accountsets:

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
                if not test_acc_no:
                    raise UserError(_("There is no bank account with number '%s' defined in the system. Please define such account and try again!") %(company_acc_no))

            # getting Statement Reference and Date:
            statement_name = company_acc_no + ' ' + start_date+ ':' + end_date
            statement_date = end_date

            # getting currency:
            currency = company_account.getElementsByTagName('Ccy')[0].toxml().replace('<Ccy>','').replace('</Ccy>','')

            # getting and checking balances:
            balance_start = company_account.getElementsByTagName('OpenBal')[0].toxml().replace('<OpenBal>','').replace('</OpenBal>','')
            balance_end_real = company_account.getElementsByTagName('CloseBal')[0].toxml().replace('<CloseBal>','').replace('</CloseBal>','')
            bank_statements = bank_statement_obj.search([('bank_account_id', '=', test_acc_no[0].id)], order='date asc')
            if bank_statements and bank_statements[-1].balance_end_real != float(balance_start) and self.flag == False:
                raise UserError(_("The Ending Balance of the last Bank Statement (by date) imported for the Bank Account '%s' is not equal to the Starting Balance of this document. If this is OK with you, check the 'Continue Anyway' box and try to import again.") %(company_acc_no))

            # creating account.bank.statement
            statement = bank_statement_obj.create({
                'name': statement_name,
                'date': statement_date,
                'journal_id': self.journal_id.id,
                'balance_start': balance_start,
                'balance_end_real': balance_end_real,
                'bank_account_id': test_acc_no[0].id
            })

            # getting elements for account.bank.statement.line and creating the lines:
            statement_lines = company_account.getElementsByTagName('TrxSet')
            count = 0
            for line in statement_lines:

                # getting and testing the dates:
                count += 1
                line_date = line.getElementsByTagName('BookDate')[0].toxml().replace('<BookDate>','').replace('</BookDate>','')
                if count == 1:
                    statement_lines = statement_line_obj.search([('statement_id.bank_account_id','=',test_acc_no[0].id)])
                    if statement_lines and (statement_lines[-1].date > line_date):
                        raise UserError(_("The Date of the last Bank Statment Line posted for this Bank Account should not come after the date of the first transaction described in the FiDAViSta file!"))

                # getting OBI:
                pmt_info = line.getElementsByTagName('PmtInfo')
                if pmt_info:
                    line_name = pmt_info[0].toxml().replace('<PmtInfo>','').replace('</PmtInfo>','')
                if not pmt_info:
                    line_name = line.getElementsByTagName('TypeName')[0].toxml().replace('<TypeName>','').replace('</TypeName>','')

                # getting Reference:
                line_ref = line.getElementsByTagName('BankRef')[0].toxml().replace('<BankRef>','').replace('</BankRef>','')

                # getting Amount:
                cord = line.getElementsByTagName('CorD')[0].toxml().replace('<CorD>','').replace('</CorD>','')
                if cord == 'C':
                    line_amount = line.getElementsByTagName('AccAmt')[0].toxml().replace('<AccAmt>','').replace('</AccAmt>','')
                if cord == 'D':
                    line_amount = float(line.getElementsByTagName('AccAmt')[0].toxml().replace('<AccAmt>','').replace('</AccAmt>','')) * (-1)

                # getting Partner info:
                account_id = False
                bank_account_id = False
                line_cur = False
                line_amount_cur = False
                cPartySet = line.getElementsByTagName('CPartySet')
                if cPartySet:
                    partner_name_tag = cPartySet[0].getElementsByTagName('Name')
                    if partner_name_tag:
                        partner_name = partner_name_tag[0].toxml().replace('<Name>','').replace('</Name>','').replace('<Name/>','').replace("&quot;","'")
                    if not partner_name_tag:
                        partner_name = False
                    partner_reg_id_tag = cPartySet[0].getElementsByTagName('LegalId')
                    if partner_reg_id_tag:
                        partner_reg_id = partner_reg_id_tag[0].toxml().replace('<LegalId>','').replace('</LegalId>','').replace('<LegalId/>','')
                    if not partner_reg_id_tag:
                        partner_reg_id = False
                    partner_bank_account_tag = cPartySet[0].getElementsByTagName('AccNo')
                    if partner_bank_account_tag:
                        partner_bank_account = partner_bank_account_tag[0].toxml().replace('<AccNo>','').replace('</AccNo>','').replace('<AccNo/>','')
                    if not partner_bank_account_tag:
                        partner_bank_account = False

                    # testing, whether it's possible to get partner_id (also type and account) from the system:
                    partner_id = False
                    bank_account = bank_obj.search([('acc_number','=',partner_bank_account)])
                    if (not bank_account) and partner_bank_account:
                        partner_bank_account_list = list(partner_bank_account)
                        partner_bank_account_list.insert(4,' ')
                        partner_bank_account_list.insert(9,' ')
                        partner_bank_account_list.insert(14,' ')
                        partner_bank_account_list.insert(19,' ')
                        partner_bank_account_list.insert(24,' ')
                        partner_bank_account_2 = "".join(partner_bank_account_list)
                        bank_account = bank_obj.search([('acc_number','=',partner_bank_account_2)])
                    if bank_account:
                        bank_account_id = bank_account[0]
                        bank_acc_1 = bank_account_obj.browse(cr, uid, bank_account[0])
                        partner_id = bank_account[0].partner_id.id
                        if cord == 'C':
                            account_id = bank_account[0].partner_id.property_account_receivable.id
                        if cord == 'D':
                            account_id = bank_account[0].partner_id.property_account_payable.id
                    if (not bank_account) and (partner_reg_id):
                        partners = partner_obj.search([('vat','ilike',partner_reg_id)])
                        if len(partners) == 1:
                            if cord == 'C':
                                account_id = partners[0].property_account_receivable.id
                            if cord == 'D':
                                account_id = partners[0].property_account_payable.id
                    line_cur_tag = cPartySet[0].getElementsByTagName('Ccy')
                    if line_cur_tag:
                        line_cur_txt = line_cur_tag[0].toxml().replace('<Ccy>','').replace('</Ccy>','').replace('<Ccy/>','')
                        if line_cur_txt:
                            line_curs = cur_obj.search([('name','=',line_cur_txt)])
                            if line_curs:
                                line_cur = line_curs[0].id
                    line_amount_cur_tag = cPartySet[0].getElementsByTagName('Amt')
                    if line_amount_cur_tag:
                        line_amount_cur = line_amount_cur_tag[0].toxml().replace('<Amt>','').replace('</Amt>','').replace('<Amt/>','')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: