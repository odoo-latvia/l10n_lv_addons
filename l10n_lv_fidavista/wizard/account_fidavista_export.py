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

from openerp.osv import fields, osv
import sys
from openerp.tools.translate import _
import base64
import openerp.addons.decimal_precision as dp
import time
from datetime import datetime
import string

class account_fidavista_export(osv.osv_memory):
    _name = 'account.fidavista.export'
    _description = 'Export FiDAViSta File'

    _columns = {
        'name': fields.char('File Name', size=32),
        'file_save': fields.binary('Save File', filters='*.xml', readonly=True),
        'payment_order_id': fields.many2one('payment.order', 'Payment Order', required=True),
    }

    def _get_payment_order(self, cr, uid, context=None):
        if context is None:
            context = {}
        return context.get('payment_order_id',False)

    _defaults = {
        'name': 'FiDAViSta_export.xml',
        'payment_order_id': _get_payment_order
    }

    def onchange_payment_order_id(self, cr, uid, ids, payment_order_id, context=None):
        if context is None:
            context = {}
        res = {}
        if payment_order_id:
            payment = self.pool.get('payment.order').browse(cr, uid, payment_order_id, context=context)
            res = {'value': {'name': '%s.xml' % payment.reference}}
        return res

    def create_xml(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        def format_string(strval):
            return strval.replace('&', '&amp;').replace('>', '&gt;').replace('<', '&lt;').replace("'", "&apos;").replace('"', '&quot;')
        data_exp = self.browse(cr, uid, ids[0], context=context)
        if context.get('payment_order_id',False):
            payment_order = self.pool.get('payment.order').browse(cr, uid, context['payment_order_id'], context=context)
        else:
            payment_order = data_exp.payment_order_id
        data_of_file = """<?xml version="1.0" encoding="UTF-8" ?>
<FIDAVISTA xmlns="http://bankasoc.lv/fidavista/fidavista0101.xsd">"""
        data_of_file += "\n    <Header>"
        data_of_file += ("\n        <Timestamp>" + datetime.now().strftime('%Y%m%d%H%M%S%f')[:-3] + "</Timestamp>")
        company = payment_order.company_id
        if not company:
            company = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id
        data_of_file += ("\n        <From>" + format_string(company.name) + "</From>")
        data_of_file += "\n    </Header>"
        pay_acc = payment_order.mode.bank_id.acc_number.replace(' ', '').upper()
        pay_legal = False
        if hasattr(payment_order.mode.bank_id.partner_id, 'company_registry'):
            pay_legal = payment_order.mode.bank_id.partner_id.company_registry
        if (not pay_legal) and hasattr(payment_order.mode.bank_id.partner_id, 'vat') and payment_order.mode.bank_id.partner_id.vat:
            pay_legal = ((payment_order.mode.bank_id.partner_id.vat).replace(' ', '').upper())[2:]
        if (not pay_legal) and hasattr(payment_order.mode.bank_id.partner_id, 'identification_id') and payment_order.mode.bank_id.partner_id.is_company == False:
            pay_legal = payment_order.mode.bank_id.partner_id.identification_id
        data_obj = self.pool.get('ir.model.data')
        for payment in payment_order.line_ids:
            data_of_file += "\n    <Payment>"
#            ext_ids = data_obj.search(cr, uid, [('model','=','payment.line'), ('res_id','=',payment.id)], context=context)
#            if ext_ids:
#                extid = data_obj.browse(cr, uid, ext_ids[0], context=context).complete_name
#                extid = len(extid) > 10 and extid[-10:] or extid
#                data_of_file += ("\n        <ExtId>" + extid + "</ExtId>")
            payment_name = len(payment.name) > 10 and payment.name[0:10] or payment.name
            data_of_file += ("\n        <DocNo>" + payment_name + "</DocNo>")
            if payment.date:
                payment_date = len(payment.date) > 10 and payment.date[0:10] or payment.date
                data_of_file += ("\n        <RegDate>" + payment_date + "</RegDate>")
            data_of_file += ("\n        <TaxPmtFlg>" + "N" + "</TaxPmtFlg>")
            data_of_file += ("\n        <Ccy>" + payment.currency.name + "</Ccy>")
            payment_communication = len(payment.communication) > 140 and payment.communication[0:140] or payment.communication
            data_of_file += ("\n        <PmtInfo>" + payment_communication + "</PmtInfo>")
            if pay_legal:
                pay_legal = len(pay_legal) > 20 and pay_legal[0:20] or pay_legal
                data_of_file += ("\n        <PayLegalId>" + pay_legal + "</PayLegalId>")
            pay_acc = len(pay_acc) > 34 and pay_acc[0:34] or pay_acc
            data_of_file += ("\n        <PayAccNo>" + pay_acc + "</PayAccNo>")
            data_of_file += ("\n        <DebitCcy>" + payment.company_currency.name + "</DebitCcy>")
            data_of_file += ("\n        <BenSet>")
#            ben_ext_ids = data_obj.search(cr, uid, [('model','=','res.partner'), ('res_id','=',payment.partner_id.id)], context=context)
#            if ben_ext_ids:
#                benextid = data_obj.browse(cr, uid, ben_ext_ids[0], context=context).complete_name
#                benextid = len(benextid) > 5 and benextid[-5:] and benextid
#                data_of_file += ("\n            <BenExtId>" + benextid + "</BenExtId>")
            data_of_file += ("\n            <Priority>" + "N" + "</Priority>")
            if not payment.bank_id:
                raise osv.except_osv(_('Not enough Data Error !'), _('Destination Bank account not defined for payment %s!' % payment.name))
            commission = "SHA"
            if payment.bank_id.state != 'iban':
                commission = "OUR"
            data_of_file += ("\n            <Comm>" + commission + "</Comm>")
            payment_amount_currency = str(payment.amount_currency)
            payment_amount_currency = len(payment_amount_currency) > 12 and payment_amount_currency[-12:] or payment_amount_currency
            data_of_file += ("\n            <Amt>") + payment_amount_currency + ("</Amt>")
            payment_bank_acc_number = (payment.bank_id.acc_number).replace(' ','').upper()
            payment_bank_acc_number = len(payment_bank_acc_number) > 34 and payment_bank_acc_number[0:34] or payment_bank_acc_number
            data_of_file += ("\n            <BenAccNo>" + payment_bank_acc_number + "</BenAccNo>")
            flg = "N"
            if payment.bank_id.state == 'iban':
                flg = "Y"
            data_of_file += ("\n            <BenAccIbanFlg>" + flg + "</BenAccIbanFlg>")
            payment_partner_name = format_string(payment.partner_id.name)
            payment_partner_name = len(payment_partner_name) > 105 and payment_partner_name[0:105] or payment_partner_name
            data_of_file += ("\n            <BenName>" + payment_partner_name + "</BenName>")
            ben_legal = hasattr(payment.partner_id,'company_registry') and payment.partner_id.company_registry or False
            if (not ben_legal) and hasattr(payment.partner_id, 'vat') and (payment.partner_id.vat):
                ben_legal = ((payment.partner_id.vat).replace(" ","").upper())[2:]
            if (not ben_legal) and hasattr(payment.partner_id, 'identification_id') and payment.partner_id.is_company == False:
                ben_legal = payment.partner_id.identification_id
            if ben_legal:
                ben_legal = len(ben_legal) > 35 and ben_legal[0:35] or ben_legal
                data_of_file += ("\n            <BenLegalId>" + ben_legal + "</BenLegalId>")
            address_list = []
            if payment.partner_id.street:
                address_list.append(payment.partner_id.street)
            if payment.partner_id.street2:
                address_list.append(payment.partner_id.street2)
            if payment.partner_id.city:
                address_list.append(payment.partner_id.city)
            if payment.partner_id.state_id:
                address_list.append(payment.partner_id.state_id.name)
            if payment.partner_id.zip:
                address_list.append(payment.partner_id.zip)
            if payment.partner_id.country_id:
                address_list.append(payment.partner_id.country_id.name)
            if address_list:
                address = format_string(", ".join(address_list))
                address = len(address) > 70 and address[0:70] or address
                data_of_file += ("\n            <BenAddress>" + address + "</BenAddress>")
            country_code = False
            if payment.partner_id.country_id:
                country_code = payment.partner_id.country_id.code
                if (not country_code) and hasattr(payment.partner_id, 'vat') and payment.partner_id.vat:
                    country_code = (payment.partner_id.vat).upper()[:2]
            if country_code:
                data_of_file += ("\n            <BenCountry>" + country_code + "</BenCountry>")
            if not country_code:
                raise osv.except_osv(_('Insufficient data!'), _('No Country or VAT defined for Partner %s, but the Country Code is a mandatory tag. Please define either a Country or a VAT to get the Country Code!') % (payment.partner_id.name))
            bank_name = payment.bank_id.bank and payment.bank_id.bank.name or payment.bank_id.bank_name
            if bank_name:
                bank_name = format_string(bank_name)
                bank_name = len(bank_name) > 35 and bank_name[0:35] or bank_name
                data_of_file += ("\n            <BBName>" + bank_name + "</BBName>")
            if payment.bank_id.bank:
                bank_address_list = []
                if payment.bank_id.bank.street:
                    bank_address_list.append(payment.bank_id.bank.street)
                if payment.bank_id.bank.street2:
                    bank_address_list.append(payment.bank_id.bank.street2)
                if payment.bank_id.bank.city:
                    bank_address_list.append(payment.bank_id.bank.city)
                if payment.bank_id.bank.state:
                    bank_address_list.append(payment.bank_id.bank.state.name)
                if payment.bank_id.bank.zip:
                    bank_address_list.append(payment.bank_id.bank.zip)
                if payment.bank_id.bank.country:
                    bank_address_list.append(payment.bank_id.bank.country.name)
                if bank_address_list:
                    bank_address = format_string(", ".join(bank_address_list))
                    bank_address = len(bank_address) > 70 and bank_address[0:70] or bank_address
                    data_of_file += ("\n            <BBAddress>" + bank_address + "</BBAddress>")
            swift = payment.bank_id.bank and payment.bank_id.bank.bic or payment.bank_id.bank_bic
            if swift:
                swift = len(swift) > 11 and swift[0:11] or swift
                data_of_file += ("\n            <BBSwift>" + swift + "</BBSwift>")
            data_of_file += ("\n        </BenSet>")
            data_of_file += "\n    </Payment>"

        data_of_file += "\n</FIDAVISTA>"

        data_of_file_real = base64.encodestring(data_of_file.encode('utf8'))
        self.write(cr, uid, ids, {
            'file_save': data_of_file_real,
            'name': data_exp.name
        }, context=context)

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.fidavista.export',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': data_exp.id,
            'views': [(False,'form')],
            'target': 'new',
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: