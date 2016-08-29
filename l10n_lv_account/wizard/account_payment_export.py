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

from openerp import api, fields, models, _
from datetime import datetime
from openerp.exceptions import UserError
import base64

class AccountPaymentExport(models.TransientModel):
    _name = 'account.payment.export'

    format = fields.Selection([('ofx','.OFX'), ('fidavista','FiDAViSta'), ('iso20022', 'ISO 20022')], string='Format', required=True)
    name = fields.Char('File Name', default='export.xml')
    data_file = fields.Binary(string='Save File', readonly=True)

    @api.onchange('format')
    def _onchange_format(self):
        if self.format:
            format_str = dict(self.fields_get(allfields=['format'])['format']['selection'])[self.format]
            self.name = format_str.replace(' ', '_').replace('.','') + '_export.xml'

    @api.multi
    def export_file(self):
        self.ensure_one()
        data_file = False
        active_ids = self._context.get('active_ids', [])
        if active_ids:
            if self.format == 'fidavista':
                data_file = self.form_fidavista_data(active_ids)
            if self.format == 'iso20022':
                data_file = self.form_iso20022_data(active_ids)
        self.write({
            'data_file': data_file,
            'name': self.name
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment.export',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': self.id,
            'views': [(False, 'form')],
            'target': 'new'
        }

    def _get_company(self, active_ids):
        companies = []
        for payment in self.env['account.payment'].browse(active_ids):
            if payment.company_id not in companies:
                companies.append(payment.company_id)
        company = False
        if len(companies) == 1 and False not in companies:
            company = companies[0]
        if not company:
            company = self.env.user.company_id
        return company

    def form_fidavista_data(self, active_ids):
        def format_string(strval):
            return strval.replace('&', '&amp;').replace('>', '&gt;').replace('<', '&lt;').replace("'", "&apos;").replace('"', '&quot;')
        bank_acc_obj = self.env['res.partner.bank']
        data_of_file = """<?xml version="1.0" encoding="UTF-8" ?>
<FIDAVISTA xmlns="http://bankasoc.lv/fidavista/fidavista0101.xsd">"""
        data_of_file += "\n    <Header>"
        data_of_file += ("\n        <Timestamp>" + datetime.now().strftime('%Y%m%d%H%M%S%f')[:-3] + "</Timestamp>")
        company = self._get_company(active_ids)
        data_of_file += ("\n        <From>" + format_string(company.name) + "</From>")
        data_of_file += "\n    </Header>"
        payments = self.env['account.payment'].search([('id','in',active_ids), ('payment_type','in',['outbound', 'transfer'])])
        for payment in payments:
            data_of_file += "\n    <Payment>"
            payment_name = len(payment.name) > 10 and payment.name[-10:] or payment.name
            data_of_file += ("\n        <DocNo>" + payment_name + "</DocNo>")
            payment_date = len(payment.payment_date) > 10 and payment.payment_date[0:10] or payment.payment_date
            data_of_file += ("\n        <RegDate>" + payment_date + "</RegDate>")
            data_of_file += ("\n        <TaxPmtFlg>" + "N" + "</TaxPmtFlg>")
            data_of_file += ("\n        <Ccy>" + payment.currency_id.name + "</Ccy>")
            if payment.communication:
                payment_communication = len(payment.communication) > 140 and payment.communication[0:140] or payment.communication
                data_of_file += ("\n        <PmtInfo>" + payment_communication + "</PmtInfo>")
            src_bank_account = payment.journal_id.bank_account_id
            if not src_bank_account:
                raise UserError(_('Please define bank data for journal %s!') % payment.journal_id.name)
            pay_legal = False
            if src_bank_account.partner_id:
                if hasattr(src_bank_account.partner_id, 'company_registry') and src_bank_account.partner_id.company_registry:
                    pay_legal = src_bank_account.partner_id.company_registry
                if (not pay_legal) and hasattr(src_bank_account.partner_id, 'vat') and src_bank_account.partner_id.vat:
                    pay_legal = ((src_bank_account.partner_id.vat).replace(' ', '').upper())[2:]
                if (not pay_legal) and hasattr(src_bank_account.partner_id, 'identification_id') and src_bank_account.partner_id.is_company == False and src_bank_account.partner_id.identification_id:
                    pay_legal = src_bank_account.partner_id.identification_id
            if pay_legal:
                pay_legal = len(pay_legal) > 20 and pay_legal[0:20] or pay_legal
                data_of_file += ("\n        <PayLegalId>" + pay_legal + "</PayLegalId>")
            pay_acc = src_bank_account.acc_number.replace(' ', '').upper()
            data_of_file += ("\n        <PayAccNo>" + pay_acc + "</PayAccNo>")
            if payment.company_id:
                data_of_file += ("\n        <DebitCcy>" + payment.company_id.currency_id.name + "</DebitCcy>")
            data_of_file += ("\n        <BenSet>")
            data_of_file += ("\n            <Priority>" + "N" + "</Priority>")
            data_of_file += ("\n            <Comm>" + "SHA" + "</Comm>")
            payment_amount = str(payment.amount)
            payment_amount = len(payment_amount) > 12 and payment_amount[-12:] or payment_amount
            data_of_file += ("\n            <Amt>") + payment_amount + ("</Amt>")
            dst_bank_account = False
            dst_partner = False
            if payment.payment_type == 'outbound':
                dst_partner = payment.partner_id
                partner_bnk_accs = bank_acc_obj.search([('partner_id','=',payment.partner_id.id)])
                if not partner_bnk_accs:
                    raise UserError(_('Please define bank account for partner %s!') % payment.partner_id.name)
                if src_bank_account.bank_id:
                    dst_bank_account = bank_acc_obj.search([('id','in',[pb.id for pb in partner_bnk_accs]), ('bank_id','=',src_bank_account.bank_id.id)], limit=1)
                if not dst_bank_account:
                    dst_bank_account = [pb for pb in partner_bnk_accs][0]
            if payment.payment_type == 'transfer':
                dst_bank_account = payment.destination_journal_id.bank_account_id
                if not dst_bank_account:
                    raise UserError(_('Please define bank data for journal %s!') % payment.destination_journal_id.name)
                dst_partner = dst_bank_account.partner_id
            partner_acc = (dst_bank_account.acc_number).replace(' ','').upper()
            partner_acc = len(partner_acc) > 34 and partner_acc[0:34] or partner_acc
            data_of_file += ("\n            <BenAccNo>" + partner_acc + "</BenAccNo>")
            flg = "N"
            if dst_bank_account.acc_type == 'iban':
                flg = "Y"
            data_of_file += ("\n            <BenAccIbanFlg>" + flg + "</BenAccIbanFlg>")
            payment_partner_name = format_string(dst_partner.name)
            payment_partner_name = len(payment_partner_name) > 105 and payment_partner_name[0:105] or payment_partner_name
            data_of_file += ("\n            <BenName>" + payment_partner_name + "</BenName>")
            ben_legal = hasattr(dst_partner,'company_registry') and dst_partner.company_registry or False
            if (not ben_legal) and hasattr(dst_partner, 'vat') and dst_partner.vat:
                ben_legal = ((dst_partner.vat).replace(" ","").upper())[2:]
            if (not ben_legal) and hasattr(dst_partner, 'identification_id') and dst_partner.is_company == False:
                ben_legal = dst_partner.identification_id
            if ben_legal:
                ben_legal = len(ben_legal) > 35 and ben_legal[0:35] or ben_legal
                data_of_file += ("\n            <BenLegalId>" + ben_legal + "</BenLegalId>")
            address_list = []
            if dst_partner.street:
                address_list.append(dst_partner.street)
            if dst_partner.street2:
                address_list.append(dst_partner.street2)
            if dst_partner.city:
                address_list.append(dst_partner.city)
            if dst_partner.state_id:
                address_list.append(dst_partner.state_id.name)
            if dst_partner.zip:
                address_list.append(dst_partner.zip)
            if dst_partner.country_id:
                address_list.append(dst_partner.country_id.name)
            if address_list:
                address = format_string(", ".join(address_list))
                address = len(address) > 70 and address[0:70] or address
                data_of_file += ("\n            <BenAddress>" + address + "</BenAddress>")
            country_code = False
            if dst_partner.country_id:
                country_code = dst_partner.country_id.code
                if (not country_code) and hasattr(dst_partner, 'vat') and dst_partner.vat:
                    country_code = (dst_partner.vat).upper()[:2]
            if country_code:
                data_of_file += ("\n            <BenCountry>" + country_code + "</BenCountry>")
            if not country_code:
                raise UserError(_('Partner %s has no Country or VAT number defined, but the country code is a mandatory parameter of payment file.') % dst_partner.name)
            bank_name = dst_bank_account.bank_id and dst_bank_account.bank_id.name or dst_bank_account.bank_name
            if bank_name:
                bank_name = format_string(bank_name)
                bank_name = len(bank_name) > 35 and bank_name[0:35] or bank_name
                data_of_file += ("\n            <BBName>" + bank_name + "</BBName>")
            if dst_bank_account.bank_id:
                bank_address_list = []
                if dst_bank_account.bank_id.street:
                    bank_address_list.append(dst_bank_account.bank_id.street)
                if dst_bank_account.bank_id.street2:
                    bank_address_list.append(dst_bank_account.bank_id.street2)
                if dst_bank_account.bank_id.city:
                    bank_address_list.append(dst_bank_account.bank_id.city)
                if dst_bank_account.bank_id.state:
                    bank_address_list.append(dst_bank_account.bank_id.state.name)
                if dst_bank_account.bank_id.zip:
                    bank_address_list.append(dst_bank_account.bank_id.zip)
                if dst_bank_account.bank_id.country:
                    bank_address_list.append(dst_bank_account.bank_id.country.name)
                if bank_address_list:
                    bank_address = format_string(", ".join(bank_address_list))
                    bank_address = len(bank_address) > 70 and bank_address[0:70] or bank_address
                    data_of_file += ("\n            <BBAddress>" + bank_address + "</BBAddress>")
            swift = dst_bank_account.bank_id and dst_bank_account.bank_id.bic or dst_bank_account.bank_bic
            if swift:
                swift = len(swift) > 11 and swift[0:11] or swift
                data_of_file += ("\n            <BBSwift>" + swift + "</BBSwift>")
            data_of_file += "\n        </BenSet>"
            data_of_file += "\n    </Payment>"
        data_of_file += "\n</FIDAVISTA>"
        return base64.encodestring(data_of_file.encode('utf8'))

    def form_iso20022_data(self, active_ids):
        return False

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: