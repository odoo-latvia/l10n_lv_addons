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
import xml.etree.cElementTree as ET
import sys
from openerp.tools.translate import _
import base64
import openerp.addons.decimal_precision as dp
from datetime import datetime
from xml.etree import ElementTree
from cStringIO import StringIO
from openerp import SUPERUSER_ID

#import logging
#_logger = logging.getLogger('PVN')

EU_list = ['AT', 'BE', 'BG', 'CY', 'HR', 'CZ', 'DK', 'EE', 'FI', 'FR', 'DE', 'EL', 'HU', 'IE', 'IT', 'LT', 'LU', 'MT', 'NL', 'PL', 'PT', 'RO', 'SK', 'SI', 'ES', 'SE', 'GB']

# method for fiscal position checking:
def check_fpos(fpos, fpos_need):
    result = False
    if fpos:
        fpos_list = fpos.split(' ')
        check1 = False
        check2 = False
        check3 = False
        for fl in fpos_list:
            if ('LR' in fpos_need.split('_') and 'LR' in fl) or ('EU' in fpos_need.split('_') and ('EU' in fl or 'ES' in fl)):
                check1 = True
            if 'VAT' in fpos_need.split('_') and ('PVN' in fl or 'VAT' in fl):
                check2 = True
            if ('payer' in fpos_need.split('_') and ((u'maksātājs' in (u'' + fl) and u'nemaksātājs' not in (u'' + fl)) or ('payer' in fl and 'non-payer' not in fl))) or ('non-payer' in fpos_need.split('_') and (u'nemaksātājs' in (u'' + fl) or 'non-payer' in fl)):
                check3 = True
        if check1 and check2 and check3:
            result = True
    return result

class l10n_lv_vat_declaration(osv.osv_memory):
    """ Vat Declaration """
    _name = "l10n_lv.vat.declaration"
    _description = "Vat Declaration"

    _columns = {
        'name': fields.char('File Name', size=32),
        'period_from': fields.many2one('account.period','Period From', required=True),
        'period_to': fields.many2one('account.period','Period To', required=True),
        'tax_code_id': fields.many2one('account.tax.code', 'Tax Code', domain=[('parent_id', '=', False)], required=True),
        'partner_id': fields.many2one('res.partner', 'Related Partner'),
        'msg': fields.text('File created', size=64, readonly=True),
        'file_save': fields.binary('Save File', filters='*.xml', readonly=True),
        'amount_overpaid': fields.float('Amount Overpaid', digits_compute=dp.get_precision('Account'), readonly=True),
        'transfer': fields.boolean('Transfer'),
        'amount_to_transfer': fields.float('Amount To Transfer', digits_compute=dp.get_precision('Account')),
        'bank_account_id': fields.many2one('res.partner.bank', 'Bank Account'),
        'info_file_name': fields.char('Info File Name'),
        'info_file_save': fields.binary('Save Information File', filters='*.csv', readonly=True, help='This file contains information about the documents used in VAT declaration.')
    }

    def _get_tax_code(self, cr, uid, context=None):
        obj_tax_code = self.pool.get('account.tax.code')
        obj_user = self.pool.get('res.users')
        company_id = obj_user.browse(cr, uid, uid, context=context).company_id.id
        tax_code_ids = obj_tax_code.search(cr, uid, [('company_id', '=', company_id), ('parent_id', '=', False)], context=context)
        return tax_code_ids and tax_code_ids[0] or False

    def _get_partner(self, cr, uid, context=None):
        obj_user = self.pool.get('res.users')
        partner_id = obj_user.browse(cr, uid, uid, context=context).company_id.partner_id.id or False
        return partner_id

    _defaults = {
        'msg': 'Save the File.',
        'name': 'vat_declaration.xml',
        'tax_code_id': _get_tax_code,
        'partner_id': _get_partner,
        'info_file_name': 'info.csv'
    }

    def onchange_tax_code(self, cr, uid, ids, tax_code_id, context=None):
        if context is None:
            context = {}
        tax_code = self.pool.get('account.tax.code').browse(cr, uid, tax_code_id, context=context)
        partner_id = tax_code.company_id.partner_id.id or False
        return {'value': {'partner_id': partner_id}}

    def onchange_period(self, cr, uid, ids, period_from, period_to, tax_code_id, context=None):
        if context is None:
            context = {}
        obj_tax_code = self.pool.get('account.tax.code')
        obj_user = self.pool.get('res.users')
        obj_period = self.pool.get('account.period')
        tax_code = obj_tax_code.browse(cr, uid, tax_code_id, context=context)
        if tax_code_id:
            obj_company = tax_code.company_id
        else:
            obj_company = obj_user.browse(cr, uid, uid, context=context).company_id
        tax_code_ids = obj_tax_code.search(cr, uid, [('parent_id','child_of',tax_code_id), ('company_id','=',obj_company.id)], context=context)
        period_list = []
        if period_from and not period_to:
            period_list.append(period_from)
        if period_to and not period_from:
            period_list.append(period_to)
        if period_from == period_to:
            period_list.append(period_from)
        if (period_from and period_to) and (period_from != period_to):
            period_list = obj_period.build_ctx_periods(cr, uid, period_from, period_to)
        amount = 0.00
        for p in period_list:
            ctx = context.copy()
            ctx['period_id'] = p
            tax_info = obj_tax_code.read(cr, uid, tax_code_ids, ['code','sum_period'], context=ctx)
            for item in tax_info:
                if (item['code'] == '420'):
                    amount += item['sum_period']
                    break
        return {'value': {'amount_overpaid': (amount * (-1)), 'amount_to_transfer': (amount * (-1)), 'transfer': False}}

    def _check_tax_code(self, cr, uid, tax_code_id, context=None):
        if context is None:
            context = {}
        tax_code_obj = self.pool.get('account.tax.code')
        main_tax_code_id = tax_code_obj.search(cr, uid, ['|',('name','in',['APRĒĶINĀTAIS PVN (latos)','PVN SUMMA PAR SAŅEMTAJĀM PRECĒM UN PAKALPOJUMIEM (latos), no tā:']),('code','in',['250','310']),('tax_code','in',[False,'60'])], context=context)
        if main_tax_code_id:
            code_id = tax_code_obj.search(cr, uid, [('id','=',tax_code_id),('id','child_of',main_tax_code_id)], context=context)
            if not code_id:
                code_id = tax_code_obj.search(cr, uid, [('id','=',tax_code_id), ('tax_code','in',['66', '67', '57'])], context=context)
            if code_id:
                return True
        return False

    def _check_tax_base_code(self, cr, uid, tax_base_code_id, context=None):
        if context is None:
            context = {}
        tax_code_obj = self.pool.get('account.tax.code')
        main_tax_base_code_id = tax_code_obj.search(cr, uid, ['|',('name','in',['Priekšnodokļa bāzes','KOPĒJĀ DARĪJUMU VĒRTĪBA (latos), no tās:']),('code','in',['500','100']),('tax_code','in',[False,'40'])], context=context)
        if main_tax_base_code_id:
            base_code_id = tax_code_obj.search(cr, uid, [('id','=',tax_base_code_id),('id','child_of',main_tax_base_code_id)], context=context)
            if base_code_id:
                return True
        return False

    def _check_customs(self, cr, uid, move_id, context=None):
        customs = False
        model_obj = self.pool.get('ir.model')
        customs_exist = model_obj.search(cr, SUPERUSER_ID, [('model','=','account.customs.declaration')], context=context)
        if customs_exist:
            customs_obj = self.pool.get('account.customs.declaration')
            customs_ids = customs_obj.search(cr, SUPERUSER_ID, [('move_id','=',move_id)], context=context)
            if customs_ids:
                customs = True
        return customs

    def _get_amount_data(self, cr, uid, line, amount_tax, partner_country, context=None):
        ctx = context.copy()
        ctx.update({'date': line.move_id.date})
        cur_obj = self.pool.get('res.currency')
        country_obj = self.pool.get('res.country')
        comp_cur = line.move_id.company_id.currency_id
        country_currency = comp_cur.name
        journal_cur = line.move_id.journal_id.currency or line.move_id.journal_id.company_id.currency_id
        line_cur = line.currency_id or journal_cur
        tax_amount = amount_tax
        cur_amount = line.amount_currency
        if cur_amount == 0.0:
            cur_amount = tax_amount
            if journal_cur.id != comp_cur.id and (not line.currency_id):
                line_cur = comp_cur
        country_ids = country_obj.search(cr, uid, [('code','=',partner_country)], context=ctx)
        if country_ids:
            country = country_obj.browse(cr, uid, country_ids[0], context=ctx)
            if country.currency_id:
                country_currency = country.currency_id.name
                if country.currency_id.id != line_cur.id:
                    cur_amount = cur_obj.compute(cr, uid, line_cur.id, country.currency_id.id, cur_amount, context=ctx)
        if line.debit == 0.0 and line.credit == 0.0 and (not self._check_customs(cr, uid, line.move_id.id, context=context)):
            tax_amount = 0.0
            cur_amount = 0.0
        return {
            'tax_amount': tax_amount,
            'cur_amount': cur_amount,
            'country_currency': country_currency
        }

    def _process_line(self, cr, uid, line_id, context=None):
        if context is None:
            context = {}

        partner_data = {}

        journal_type = line_id[0].move_id.journal_id.type
        doc_number = line_id[0].move_id.name
        doc_date = line_id[0].move_id.date
        currency = line_id[0].move_id.journal_id.currency and line_id[0].move_id.journal_id.currency.name or line_id[0].move_id.journal_id.company_id.currency_id.name

        # max amount check:
        limit_val = 1000.0
        if doc_date > datetime.strftime(datetime.strptime('2013-12-31', '%Y-%m-%d'), '%Y-%m-%d'):
            limit_val = 1430.0

        for line in line_id:

            partner_id = line.partner_id and line.partner_id.id or False
            if partner_id not in partner_data:
                partner_data.update({partner_id: {}})
                partner_country = line.partner_id and line.partner_id.country_id and line.partner_id.country_id.code or False
                vat_no = line.partner_id and line.partner_id.vat or False
                partner_vat = False
                if vat_no:
                    vat_no = vat_no.replace(' ','').upper()
                    if vat_no[:2].isalpha():
                        partner_vat = vat_no[2:]
                        partner_country = vat_no[:2]
                    else:
                        partner_vat = vat_no
                if partner_country == 'GR':
                    partner_country = 'EL'
                if line.partner_id and (not partner_vat) and hasattr(line.partner_id, 'company_registry'):
                    partner_vat = line.partner_id.company_registry
                partner_data[partner_id].update({
                    'partner_id': partner_id,
                    'partner_name': line.partner_id and line.partner_id.name or '',
                    'partner_country': partner_country,
                    'partner_vat': partner_vat,
                    'partner_fpos': line.partner_id and line.partner_id.property_account_position and line.partner_id.property_account_position.name or False,
                    'amount_tax': 0.0,
                    'amount_tax_cur': 0.0,
                    'amount_untaxed': 0.0,
                    'amount_untaxed_cur': 0.0,
                    'amount_untaxed_45': 0.0,
                    'amount_untaxed_48.2': 0.0,
                    'amount_taxed': 0.0,
                    'amount_taxed_cur': 0.0,
                    'currency': currency,
                    'limit_val': limit_val,
                    'journal_type': journal_type,
                    'doc_number': doc_number,
                    'doc_date': doc_date,
                    'tax_codes': [],
                    'tax_codes_l': [],
                    'invoices': [],
                    'product_types': [],
                    'tag_name': '',
                    'deal_type': '',
                    'doc_type': '',
                })

            if line.tax_code_id and self._check_tax_code(cr, uid, line.tax_code_id.id, context=context):
                currency_data = self._get_amount_data(cr, uid, line, (line.tax_amount * line.tax_code_id.sign), partner_data[partner_id]['partner_country'], context=context)
                partner_data[partner_id]['amount_tax'] += currency_data['tax_amount']
                partner_data[partner_id]['amount_tax_cur'] += currency_data['cur_amount']
                partner_data[partner_id]['currency'] = currency_data['country_currency']
                if line.tax_code_id.tax_code and line.tax_code_id.tax_code not in partner_data[partner_id]['tax_codes']:
                    partner_data[partner_id]['tax_codes'].append(line.tax_code_id.tax_code)
                    if line.tax_code_id.tax_code == '61' and line.move_id.ref:
                        partner_data[partner_id]['doc_number'] = line.move_id.ref
            if (line.tax_code_id and self._check_tax_base_code(cr, uid, line.tax_code_id.id, context=context)) or ((not line.tax_code_id) and line.tax_amount != 0.0):
                sign = line.tax_code_id and line.tax_code_id.sign or 1.0
                currency_data = self._get_amount_data(cr, uid, line, (line.tax_amount * sign), partner_data[partner_id]['partner_country'], context=context)
                partner_data[partner_id]['amount_untaxed'] += currency_data['tax_amount']
                partner_data[partner_id]['amount_untaxed_cur'] += currency_data['cur_amount']
                partner_data[partner_id]['currency'] = currency_data['country_currency']
                if line.tax_code_id.tax_code:
                    if line.tax_code_id.tax_code == '45':
                        partner_data[partner_id]['amount_untaxed_45'] += currency_data['tax_amount']
                    if line.tax_code_id.tax_code == '48.2':
                        partner_data[partner_id]['amount_untaxed_48.2'] += currency_data['tax_amount']
                    if line.tax_code_id.tax_code not in partner_data[partner_id]['tax_codes_l']:
                        partner_data[partner_id]['tax_codes_l'].append(line.tax_code_id.tax_code)

            if not line.tax_code_id:
                currency_data = self._get_amount_data(cr, uid, line, (line.debit or line.credit), partner_data[partner_id]['partner_country'], context=context)
                partner_data[partner_id]['amount_taxed'] += currency_data['tax_amount']
                partner_data[partner_id]['amount_taxed_cur'] += currency_data['cur_amount']
                partner_data[partner_id]['currency'] = currency_data['country_currency']

            if line.invoice:
                if line.invoice not in partner_data[partner_id]['invoices']:
                    partner_data[partner_id]['invoices'].append(line.invoice)
                if line.invoice.type in ['in_invoice', 'in_refund'] and line.invoice.supplier_invoice_number:
                    partner_data[partner_id]['doc_number'] = line.invoice.supplier_invoice_number

            if line.product_id and line.product_id.type not in partner_data[partner_id]['product_types']:
                partner_data[partner_id]['product_types'].append(line.product_id.type)

        # amount check:
        for key, value in partner_data.iteritems():
            if value['tax_codes'] == [] and value['tax_codes_l'] == [] and value['amount_taxed'] != 0.0:
                partner_data[key]['amount_taxed'] = value['amount_taxed'] * 0.5
                partner_data[key]['amount_taxed_cur'] = value['amount_taxed_cur'] * 0.5
            if '61' in value['tax_codes']:
                partner_data[key]['amount_tax'] = value['amount_tax'] * 0.5
                partner_data[key]['amount_tax_cur'] = value['amount_tax_cur'] * 0.5
            if value['amount_untaxed'] == 0.0 and value['amount_tax'] == 0.0:
                partner_data[key]['amount_untaxed'] = value['amount_taxed']
                partner_data[key]['amount_untaxed_cur'] = value['amount_taxed_cur']
            if value['amount_taxed'] == 0.0:
                partner_data[key]['amount_taxed'] = value['amount_untaxed'] + value['amount_tax']
                partner_data[key]['amount_taxed_cur'] = value['amount_untaxed_cur'] + value['amount_tax_cur']
            if '64' in value['tax_codes'] and (value['partner_fpos'] and (check_fpos(value['partner_fpos'], 'EU_VAT_payer') or check_fpos(value['partner_fpos'], 'EU_VAT_non-payer'))):
#                key2_list = ['amount_untaxed', 'amount_untaxed_cur', 'amount_tax', 'amount_tax_cur', 'amount_taxed', 'amount_taxed_cur']
                key2_list = ['amount_tax', 'amount_tax_cur']
                for key2 in key2_list:
                    partner_data[key][key2] = round((round(partner_data[key][key2], 2) * 0.5), 2)
            if journal_type == 'expense' and value['tax_codes'] == [] and value['tax_codes_l'] == [] and value['amount_taxed'] != 0.0:
                partner_data[key].clear()

        partner_data = {k: v for k,v in partner_data.iteritems() if v}

        # tag names, deal types and doc types:
        for key, value in partner_data.iteritems():

            if (value['amount_untaxed'] >= limit_val):
                if key == False:
                    raise osv.except_osv(_('Insufficient data!'), _('No Partner defined, but Untaxed Amount is greater than %s. Please define a Partner in document %s!') % (limit_val, doc_number))
                if not value['partner_country']:
                    raise osv.except_osv(_('Insufficient data!'), _('No TIN or Country defined for Partner %s, but Untaxed Amount is greater than %s in document %s. Please define either a Country or a TIN to get the Country Code!') % (value['partner_name'], limit_val, doc_number))

            # PVN1-I:
            if (journal_type in ['purchase', 'expense', 'sale_refund']) and  ('64' not in value['tax_codes']) and ((not value['partner_fpos']) or (value['partner_fpos'] and (check_fpos(value['partner_fpos'], 'EU_VAT_payer') or check_fpos(value['partner_fpos'], 'EU_VAT_non-payer') or check_fpos(value['partner_fpos'], 'LR_VAT_payer') or check_fpos(value['partner_fpos'], 'LR_VAT_non-payer'))) or ('61' in value['tax_codes'])):
                # PVN1-I tag:
                partner_data[key]['tag_name'] = 'PVN1-I'

                # PVN1-I deal type:
                deal_type = ""
                if value['partner_vat'] and (value['partner_fpos'] and (check_fpos(value['partner_fpos'], 'LR_VAT_payer') or check_fpos(value['partner_fpos'], 'EU_VAT_payer'))):
                    deal_type = "A"
                if (not value['partner_vat']) and value['partner_fpos'] and (check_fpos(value['partner_fpos'], 'LR_VAT_payer') or check_fpos(value['partner_fpos'], 'EU_VAT_payer')):
                    raise osv.except_osv(_('Insufficient data!'), _('No TIN defined for Partner %s, but this partner is defined as a VAT payer. Please define the TIN!') % (value['partner_name']))
                if (not value['partner_vat']) or check_fpos(value['partner_fpos'], 'LR_VAT_non-payer') or check_fpos(value['partner_fpos'], 'EU_VAT_non-payer'):
                    deal_type = "N"
                if '61' in value['tax_codes']:
                    deal_type = "I"
                if '65' in value['tax_codes']:
                    deal_type = "K"
                if '62' in value['tax_codes'] and '52' in value['tax_codes']:
                    deal_type = "R4"
                    partner_data[key]['limit_val'] = 0.0
                    partner_data[key]['amount_tax'] *= 0.5
                partner_data[key]['deal_type'] = deal_type

                # PVN1-I doc type:
                doc_type = "1"
                if value['invoices'] and journal_type == 'sale_refund':
                    doc_type = "4"
                    partner_data[key]['limit_val'] = 0.0
                    key2_list = ['amount_untaxed', 'amount_untaxed_cur', 'amount_tax', 'amount_tax_cur', 'amount_taxed', 'amount_taxed_cur']
                    for key2 in key2_list:
                        if partner_data[key][key2] < 0.0:
                            partner_data[key][key2] = partner_data[key][key2] * (-1.0)
                if (not value['invoices']) and journal_type != 'expense':
                    doc_type = "5"
                    if '61' in value['tax_codes']:
                        doc_type = "6"
                        partner_data[key]['limit_val'] = 0.0
                partner_data[key]['doc_type'] = doc_type

            # PVN1-II:
            if journal_type in ['purchase', 'purchase_refund', 'expense'] and '64' in value['tax_codes'] and (value['partner_fpos'] and (check_fpos(value['partner_fpos'], 'EU_VAT_payer') or check_fpos(value['partner_fpos'], 'EU_VAT_non-payer'))):
                # PVN1-II tag:
                partner_data[key]['tag_name'] = 'PVN1-II'

                # PVN1-II deal type:
                deal_type = "C"
                if 'service' not in value['product_types']:
                    deal_type = "G"
                if len(value['product_types']) == 1 and 'service' in value['product_types']:
                    deal_type = "P"
                partner_data[key]['deal_type'] = deal_type
                # PVN1-II refunds:
                if journal_type == 'purchase_refund':
                    key2_list = ['amount_untaxed', 'amount_untaxed_cur', 'amount_tax', 'amount_tax_cur', 'amount_taxed', 'amount_taxed_cur']
                    for key2 in key2_list:
                        if partner_data[key][key2] > 0.0:
                            partner_data[key][key2] = partner_data[key][key2] * (-1.0)

            # PVN1-III
#            if journal_type in ['sale', 'purchase_refund'] and (any(x in ['41', '41.1', '42', '43', '44', '48.2'] for x in value['tax_codes_l'])) and ((not value['partner_fpos']) or ((not check_fpos(value['partner_fpos'], 'LR_VAT_payer')) and (not check_fpos(value['partner_fpos'], 'LR_VAT_non-payer')))):
#                _logger.info('----------------------------')
#                _logger.info('%s' % value['partner_name'])
#                _logger.info('%s' % value['partner_fpos'])
#                _logger.info('%s' % value['doc_number'])
            if journal_type in ['sale', 'purchase_refund'] and (any(x in ['41', '41.1', '42', '43', '44', '48.2'] for x in value['tax_codes_l'])) and (value['partner_fpos'] and (check_fpos(value['partner_fpos'], 'LR_VAT_payer') or check_fpos(value['partner_fpos'], 'LR_VAT_non-payer'))):
                # PVN1-III tag:
                partner_data[key]['tag_name'] = 'PVN1-III'

                # PVN1-III deal types:
                deal_type = len(value['tax_codes_l']) == 1 and value['tax_codes_l'][0] or ''
                if not deal_type:
                    if '41' in value['tax_codes_l']:
                        deal_type = '41'
                    if '41.1' in value['tax_codes_l']:
                        deal_type = '41.1'
                    if '42' in value['tax_codes_l']:
                        deal_type = '42'
                    if '43' in value['tax_codes_l']:
                        deal_type = '43'
                    if '44' in value['tax_codes_l']:
                        deal_type = '44'
                    if '48.2' in value['tax_codes_l']:
                        deal_type = '48.2'
                partner_data[key]['deal_type'] = deal_type

                # PVN1-III doc type:
                doc_type = "1"
                if value['invoices'] and journal_type == 'purchase_refund':
                    doc_type = "4"
                    partner_data[key]['limit_val'] = 0.0
                    key2_list = ['amount_untaxed', 'amount_untaxed_cur', 'amount_tax', 'amount_tax_cur', 'amount_taxed', 'amount_taxed_cur']
                    for key2 in key2_list:
                        if partner_data[key][key2] < 0.0:
                            partner_data[key][key2] = partner_data[key][key2] * (-1.0)
                if not value['invoices']:
                    doc_type = "5"
                partner_data[key]['doc_type'] = doc_type

            # PVN2:
            if journal_type in ['sale', 'sale_refund'] and (not partner_data[key]['tag_name']) and value['partner_fpos'] and (check_fpos(value['partner_fpos'], 'EU_VAT_payer') or check_fpos(value['partner_fpos'], 'EU_VAT_non-payer')):
                # PVN2 tag:
                partner_data[key]['tag_name'] = 'PVN2'
                if journal_type == 'sale_refund':
                    key2_list = ['amount_untaxed', 'amount_untaxed_cur', 'amount_untaxed_45', 'amount_untaxed_48.2', 'amount_tax', 'amount_tax_cur', 'amount_taxed', 'amount_taxed_cur']
                    for key2 in key2_list:
                        if partner_data[key][key2] > 0.0:
                            partner_data[key][key2] = partner_data[key][key2] * (-1.0)
        return partner_data

    def _process_r4_move(self, cr, uid, move, context=None):
        if context is None:
            context = {}

        it_obj = self.pool.get('account.invoice.tax')
        data_52 = {}
        data_62 = {}
        invoices = []
        for line in move.line_id:
            if line.tax_code_id:
                it_ids = it_obj.search(cr, uid, [('invoice_id','=',line.invoice.id), ('tax_code_id','=',line.tax_code_id.id)], context=context)
                if it_ids:
                    it = it_obj.browse(cr, uid, it_ids[0], context=context)
                    if line.tax_code_id.tax_code == '52':
                        it = it_obj.browse(cr, uid, it_ids[0], context=context)
                        data_52.update({
                            'line_id': line.id,
                            'amount_untaxed': it.base_amount,
                            'amount_tax': it.tax_amount < 0.0 and it.tax_amount * (-1.0) or it.tax_amount
                        })
                    if line.tax_code_id.tax_code == '62':
                        data_62.update({
                            'line_id': line.id,
                            'amount_untaxed': it.base_amount,
                            'amount_tax': it.tax_amount
                        })
            if line.invoice and line.invoice not in invoices:
                invoices.append(line.invoice)
        if data_62['amount_tax'] == data_52['amount_tax']:
            proc_line = self._process_line(cr, uid, move.line_id, context=context)
            return [v for k,v in proc_line.iteritems()]
        if data_62['amount_tax'] != data_52['amount_tax']:
            data_62['amount_tax'] -= data_52['amount_tax']
            data_62['amount_untaxed'] -= data_52['amount_untaxed']
        data_52.update({'amount_taxed': data_52['amount_untaxed'] + data_52['amount_tax']})
        data_62.update({'amount_taxed': data_62['amount_untaxed'] + data_62['amount_tax']})

        data_list = []
        for inv in invoices:
            partner_country = inv.partner_id and inv.partner_id.country_id and inv.partner_id.country_id.code or False
            vat_no = inv.partner_id and inv.partner_id.vat or False
            partner_vat = False
            if vat_no:
                vat_no = vat_no.replace(' ','').upper()
                if vat_no[:2].isalpha():
                    partner_vat = vat_no[2:]
                    partner_country = vat_no[:2]
                else:
                    partner_vat = vat_no
            if partner_country == 'GR':
                partner_country = 'EL'
            if inv.partner_id and (not partner_vat) and hasattr(inv.partner_id, 'company_registry'):
                partner_vat = inv.partner_id.company_registry
            d = {
                'partner_id': inv.partner_id and inv.partner_id.id or False,
                'partner_name': inv.partner_id and inv.partner_id.name or '',
                'partner_country': partner_country,
                'partner_vat': partner_vat,
                'partner_fpos': inv.partner_id and inv.partner_id.property_account_position and inv.partner_id.property_account_position.name or False,
                'currency': inv.currency_id.name,
                'doc_number': inv.number,
                'doc_date': inv.date_invoice,
                'doc_type': inv.type in ['in_refund', 'out_refund'] and "4" or "1"
            }
            limit_val = 1000.0
            if inv.date_invoice > datetime.strftime(datetime.strptime('2013-12-31', '%Y-%m-%d'), '%Y-%m-%d'):
                limit_val = 1430.0
            d.update({'limit_val': limit_val})
            deal_type = ""
            if d['partner_vat'] and (d['partner_fpos'] and (check_fpos(d['partner_fpos'], 'LR_VAT_payer') or check_fpos(d['partner_fpos'], 'EU_VAT_payer'))):
                deal_type = "A"
            if (not d['partner_vat']) and d['partner_fpos'] and (check_fpos(d['partner_fpos'], 'LR_VAT_payer') or check_fpos(d['partner_fpos'], 'EU_VAT_payer')):
                raise osv.except_osv(_('Insufficient data!'), _('No TIN defined for Partner %s, but this partner is defined as a VAT payer. Please define the TIN!') % (d['partner_name']))
            if (not d['partner_vat']) or check_fpos(d['partner_fpos'], 'LR_VAT_non-payer') or check_fpos(d['partner_fpos'], 'EU_VAT_non-payer'):
                deal_type = "N"
            d.update({'deal_type': deal_type})
            for itax in inv.tax_line:
                data = d.copy()
                if itax.tax_code_id:
                    if itax.tax_code_id.tax_code == '52':
                        data.update(data_52)
                        data.update({
                            'limit_val': 0.0,
                            'deal_type': "R4"
                        })
                        data_list.append(data)
                    elif itax.tax_code_id.tax_code == '62':
                        data.update(data_62)
                        data_list.append(data)
                    else:
                        data.update({
                            'amount_untaxed': itax.base_amount,
                            'amount_tax': itax.tax_amount
                        })
                        data_list.append(data)

        return data_list
                

    def create_xml(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        # defining objects used:
        obj_tax_code = self.pool.get('account.tax.code')
        obj_acc_period = self.pool.get('account.period')
        obj_user = self.pool.get('res.users')
        obj_partner = self.pool.get('res.partner')
        mod_obj = self.pool.get('ir.model.data')
        account_move_obj = self.pool.get('account.move')
        account_move_line_obj = self.pool.get('account.move.line')

        # getting wizard data and company:
        data_tax = self.browse(cr, uid, ids[0])
        if data_tax.tax_code_id:
            obj_company = data_tax.tax_code_id.company_id
        else:
            obj_company = obj_user.browse(cr, uid, uid, context=context).company_id

        # reading data and periods:
        data  = self.read(cr, uid, ids)[0]
        period_from = obj_acc_period.browse(cr, uid, data['period_from'][0], context=context)
        period_to = obj_acc_period.browse(cr, uid, data['period_to'][0], context=context)

        # defining file content:
        data_of_file = """<?xml version="1.0"?>
<DokPVNv4 xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <ParskGads>%(year)s</ParskGads>""" % ({'year': str(period_to.date_stop[:4])})

        # getting info for period tags:
        starting_month = period_from.date_start[5:7]
        ending_month = period_to.date_stop[5:7]
        if starting_month == ending_month:
            data_of_file += "\n    <ParskMen>" + str(int(starting_month)) + "</ParskMen>"
        if starting_month != ending_month:
            if ((int(ending_month) - int(starting_month) + 1) == 3) and (int(starting_month) in [1,4,7,10]):
                quarter = str(((int(starting_month) - 1) / 3) + 1)
                data_of_file += "\n    <ParskCeturksnis>" + quarter + "</ParskCeturksnis>"
            if (int(ending_month) - int(starting_month) + 1) == 6:
                pusg = str((int(ending_month)) / 6)
                data_of_file += "\n    <TaksPusgads>" + pusg + "</TaksPusgads>"

        # getting company VAT number (company registry):
        vat_no = obj_company.partner_id.vat
        if vat_no:
            vat_no = vat_no.replace(' ','').upper()
            if vat_no[:2].isalpha():
                vat = vat_no[2:]
            else:
                vat = vat_no
            data_of_file += "\n    <NmrKods>" + str(vat) + "</NmrKods>"
        if not vat_no:
            vat = obj_company.company_registry
            data_of_file += "\n    <NmrKods>" + str(vat) + "</NmrKods>"
            if not vat:
                raise osv.except_osv(_('Insufficient data!'), _('No TIN or Company Registry number associated with your company.'))

        # getting e-mail and phone:
        default_address = obj_partner.address_get(cr, uid, [obj_company.partner_id.id])
        default_address_id = default_address.get("default", obj_company.partner_id.id)
        address_id = obj_partner.browse(cr, uid, default_address_id, context)
        if address_id.email:
            data_of_file += "\n    <Epasts>" + address_id.email + "</Epasts>"
        if address_id.phone:
            phone = address_id.phone.replace('.','').replace('/','').replace('(','').replace(')','').replace(' ','')
            data_of_file += "\n    <Talrunis>" + phone + "</Talrunis>"

        # getting given periods and tax codes:
        periods = obj_acc_period.build_ctx_periods(cr, uid, data['period_from'][0], data['period_to'][0])
        tax_code_ids = obj_tax_code.search(cr, uid, [('parent_id','child_of',data_tax.tax_code_id.id), ('company_id','=',obj_company.id)], context=context)

        # summing up all values in all given periods:
        result_period = []
        data_period = {}
        for p in periods:
            ctx = context.copy()
            ctx['period_id'] = p
            p_br = obj_acc_period.browse(cr, uid, p, context=context)
            limit_val = 1000.0
            if p_br.date_start > datetime.strftime(datetime.strptime('2013-12-31', '%Y-%m-%d'), '%Y-%m-%d'):
                limit_val = 1430.0
            tax_info = obj_tax_code.read(cr, uid, tax_code_ids, ['tax_code','code','sum_period'], context=ctx)
            for item in tax_info:
                tax_code = item['tax_code']
                code = item['code']
                sum_period = item['sum_period']
                if data_period.get((code)):
                    sum_period += data_period[(code)]['sum_period']
                    data_period[(code)].clear()
                if not data_period.get((code)):
                    data_period[(code)] = {'tax_code': tax_code,'code': code, 'sum_period': sum_period, 'limit_val': limit_val}
                result_period.append(data_period[(code)])
        result_period_real = []
        for object in result_period:
            if object != {}:
                result_period_real.append(object)

        for item in result_period_real:
            if (item['code'] == '420') and (item['sum_period'] <= -item['limit_val']):
                amount_overpaid = (item['sum_period']) * (-1)
                data_of_file += "\n    <SummaParm>" + str(amount_overpaid) + "</SummaParm>"
                break

        transfer = data['transfer']
        data_of_file += "\n    <ParmaksUzKontu>" + str(int(transfer)) + "</ParmaksUzKontu>"
        if transfer:
            amount_transfer = data['amount_to_transfer']
            bank_account_id = data['bank_account_id']
            bank_account = self.pool.get('res.partner.bank').browse(cr, uid, bank_account_id[0], context=context)
            iban = "".join(bank_account.acc_number.split(" "))
            data_of_file += "\n    <ParmaksUzKontuSumma>" + str(amount_transfer) + "</ParmaksUzKontuSumma>"
            data_of_file += "\n    <IbanNumurs>" + iban + "</IbanNumurs>"

        add_pvn = False
        for item in result_period_real:
            if item['sum_period'] != 0.00:
                add_pvn = True
                break

        if add_pvn == True:
            data_of_file += "\n    <PVN>"

            for item in result_period_real:
                if (item['tax_code'] == '41') and (item['sum_period'] != 0.00):
                    data_of_file += ("\n        <R41>" + str(item['sum_period']) + "</R41>")
                if item['tax_code'] == '41.1' and (item['sum_period'] != 0.00):
                    data_of_file += ("\n        <R411>" + str(item['sum_period']) + "</R411>")
                if item['tax_code'] == '42' and (item['sum_period'] != 0.00):
                    data_of_file += ("\n        <R42>" + str(item['sum_period']) + "</R42>")
                if item['tax_code'] == '43' and (item['sum_period'] != 0.00):
                    data_of_file += ("\n        <R43>" + str(item['sum_period']) + "</R43>")
                if item['tax_code'] == '45' and (item['sum_period'] != 0.00):
                    data_of_file += ("\n        <R45>" + str(item['sum_period']) + "</R45>")
                if item['tax_code'] == '46' and (item['sum_period'] != 0.00):
                    data_of_file += ("\n        <R46>" + str(item['sum_period']) + "</R46>")
                if item['tax_code'] == '47' and (item['sum_period'] != 0.00):
                    data_of_file += ("\n        <R47>" + str(item['sum_period']) + "</R47>")
                if item['tax_code'] == '48' and (item['sum_period'] != 0.00):
                    data_of_file += ("\n        <R48>" + str(item['sum_period']) + "</R48>")
                if item['tax_code'] == '48.1' and (item['sum_period'] != 0.00):
                    data_of_file += ("\n        <R481>" + str(item['sum_period']) + "</R481>")
                if item['tax_code'] == '48.2' and (item['sum_period'] != 0.00):
                    data_of_file += ("\n        <R482>" + str(item['sum_period']) + "</R482>")
                if item['tax_code'] == '49' and (item['sum_period'] != 0.00):
                    data_of_file += ("\n        <R49>" + str(item['sum_period']) + "</R49>")
                if item['tax_code'] == '50' and (item['sum_period'] != 0.00):
                    data_of_file += ("\n        <R50>" + str(item['sum_period']) + "</R50>")
                if item['tax_code'] == '51' and (item['sum_period'] != 0.00):
                    data_of_file += ("\n        <R51>" + str(item['sum_period']) + "</R51>")
                if item['tax_code'] == '52' and (item['sum_period'] != 0.00):
                    data_of_file += ("\n        <R52>" + str(item['sum_period']) + "</R52>")
                if item['tax_code'] == '53' and (item['sum_period'] != 0.00):
                    data_of_file += ("\n        <R53>" + str(item['sum_period']) + "</R53>")
                if item['tax_code'] == '54' and (item['sum_period'] != 0.00):
                    data_of_file += ("\n        <R54>" + str(item['sum_period']) + "</R54>")
                if item['tax_code'] == '55' and (item['sum_period'] != 0.00):
                    data_of_file += ("\n        <R55>" + str(item['sum_period']) + "</R55>")
                if item['tax_code'] == '56' and (item['sum_period'] != 0.00):
                    data_of_file += ("\n        <R56>" + str(item['sum_period']) + "</R56>")
                if item['tax_code'] == '61' and (item['sum_period'] != 0.00):
                    data_of_file += ("\n        <R61>" + str(item['sum_period']) + "</R61>")
                if item['tax_code'] == '62' and (item['sum_period'] != 0.00):
                    data_of_file += ("\n        <R62>" + str(item['sum_period']) + "</R62>")
                if item['tax_code'] == '63' and (item['sum_period'] != 0.00):
                    data_of_file += ("\n        <R63>" + str(item['sum_period']) + "</R63>")
                if item['tax_code'] == '64' and (item['sum_period'] != 0.00):
                    data_of_file += ("\n        <R64>" + str(item['sum_period']) + "</R64>")
                if item['tax_code'] == '65' and (item['sum_period'] != 0.00):
                    data_of_file += ("\n        <R65>" + str(item['sum_period']) + "</R65>")
                if item['tax_code'] == '66' and (item['sum_period'] != 0.00):
                    data_of_file += ("\n        <R66>" + str(item['sum_period']) + "</R66>")
                if item['tax_code'] == '67' and (item['sum_period'] != 0.00):
                    data_of_file += ("\n        <R67>" + str(item['sum_period']) + "</R67>")
                if item['tax_code'] == '57' and (item['sum_period'] != 0.00):
                    data_of_file += ("\n        <R57>" + str(item['sum_period']) + "</R57>")

            data_of_file += "\n    </PVN>"

            # making separate data lists for different journal types and tax codes:
            r_purchase = []
            purchase_EU = []
            r_sale = []
            sale_EU = []
            account_move_ids = account_move_obj.search(cr, uid, [('period_id','in',periods), ('state','=','posted'), ('journal_id.type','in',['sale','sale_refund','purchase','purchase_refund','expense'])], context=context)
            for account_move in account_move_obj.browse(cr, uid, account_move_ids, context=context):
                if account_move.line_id:
                    lines = self._process_line(cr, uid, account_move.line_id, context=context)
                    for key, value in lines.iteritems():
                        if value['tag_name'] == 'PVN1-I':
                            if '62' in value['tax_codes'] and '52' in value['tax_codes']:
                                add_r_purchase = self._process_r4_move(cr, uid, account_move, context=context)
                                r_purchase += add_r_purchase
                            else:
                                r_purchase.append(value)
                        if value['tag_name'] == 'PVN1-II':
                            purchase_EU.append(value)
                        if value['tag_name'] == 'PVN1-III':
                            r_sale.append(value)
                        if value['tag_name'] == 'PVN2':
                            sale_EU.append(value)

            info_data = {}

            # processing purchase and purchase_refund journal types:
            d_p_s = {}
            r_p_s = []
            if r_purchase != []:
                info_data.update({'PVN1-I': []}) # info
                data_of_file += "\n    <PVN1I>"
                for p in r_purchase:
                    # getting document types "A", "N" and "I":
                    if (p['amount_untaxed'] >= 0.0 and p['amount_untaxed'] >= p['limit_val']) or (p['amount_untaxed'] < 0.0 and (p['amount_untaxed'] * (-1.0)) >= p['limit_val']):
                        data_of_file += "\n        <R>"
                        if p['deal_type'] != "I":
                            data_of_file += ("\n            <DpValsts>" + unicode(p['partner_country']) + "</DpValsts>")
                        if p['partner_vat'] and p['deal_type'] not in ["I", "N"]:
                            data_of_file += ("\n            <DpNumurs>" + str(p['partner_vat']) + "</DpNumurs>")
                        data_of_file += ("\n            <DpNosaukums>" + unicode(p['partner_name']) + "</DpNosaukums>")
                        data_of_file += ("\n            <DarVeids>" + p['deal_type'] + "</DarVeids>")
                        data_of_file += ("\n            <VertibaBezPvn>" + str(p['amount_untaxed']) + "</VertibaBezPvn>")
                        data_of_file += ("\n            <PvnVertiba>" + str(p['amount_tax']) + "</PvnVertiba>")
                        data_of_file += ("\n            <DokVeids>" + p['doc_type'] + "</DokVeids>")
                        data_of_file += ("\n            <DokNumurs>" + unicode(p['doc_number']) + "</DokNumurs>")
                        data_of_file += ("\n            <DokDatums>" + str(p['doc_date']) + "</DokDatums>")
                        data_of_file += ("\n        </R>")
                        info_data['PVN1-I'].append(p) # info

                    # summing up, what's left for each partner:
                    if ((p['amount_untaxed'] >= 0.0 and p['amount_untaxed'] < p['limit_val']) or (p['amount_untaxed'] < 0.0 and (p['amount_untaxed'] * (-1.0)) < p['limit_val'])) and p['partner_id']:
                        partner_id = p['partner_id']
                        partner_country = p['partner_country']
                        partner_vat = p['partner_vat']
                        partner_name = p['partner_name']
                        amount_untaxed = p['amount_untaxed']
                        amount_tax = p['amount_tax']
                        amount_taxed = p['amount_taxed']
                        if d_p_s.get((partner_id)):
                            amount_untaxed += d_p_s[(partner_id)]['amount_untaxed']
                            amount_tax += d_p_s[(partner_id)]['amount_tax']
                            amount_taxed += d_p_s[(partner_id)]['amount_taxed']
                            d_p_s[(partner_id)].clear()
                        if not d_p_s.get((partner_id)):
                            d_p_s[(partner_id)] = {
                                'partner_id': partner_id,
                                'partner_country': partner_country,
                                'partner_vat': partner_vat,
                                'partner_name': partner_name,
                                'amount_untaxed': amount_untaxed,
                                'amount_tax': amount_tax,
                                'amount_taxed': amount_taxed,
                                'limit_val': p['limit_val']
                            }
                        r_p_s.append(d_p_s[(partner_id)])

                r_p_s_t = []
                for object in r_p_s:
                    if object != {}:
                        r_p_s_t.append(object)

                d_p_a = {}
                amount_untaxed_a = 0.0
                amount_tax_a = 0.0
                amount_taxed_a = 0.0
                for rpst in r_p_s_t:
                    # getting document type "V":
                    if (rpst['amount_untaxed'] >= 0.0 and rpst['amount_untaxed'] >= rpst['limit_val']) or (rpst['amount_untaxed'] < 0.0 and (rpst['amount_untaxed'] * (-1.0)) >= rpst['limit_val']):
                        data_of_file += "\n        <R>"
                        data_of_file += ("\n            <DpValsts>" + unicode(rpst['partner_country']) + "</DpValsts>")
                        if rpst['partner_vat']:
                            data_of_file += ("\n            <DpNumurs>" + str(rpst['partner_vat']) + "</DpNumurs>")
                        data_of_file += ("\n            <DpNosaukums>" + unicode(rpst['partner_name']) + "</DpNosaukums>")
                        data_of_file += ("\n            <DarVeids>" + "V" + "</DarVeids>")
                        data_of_file += ("\n            <VertibaBezPvn>" + str(rpst['amount_untaxed']) + "</VertibaBezPvn>")
                        data_of_file += ("\n            <PvnVertiba>" + str(rpst['amount_tax']) + "</PvnVertiba>")
                        data_of_file += ("\n        </R>")
                        # info:
                        for info_rpv in r_purchase:
                            if info_rpv['partner_id'] == rpst['partner_id'] and (info_rpv['amount_untaxed'] < rpst['limit_val'] or (info_rpv['amount_untaxed'] < 0.0 and (info_rpv['amount_untaxed'] * (-1.0)) < rpst['limit_val'])):
                                irpv = info_rpv.copy()
                                irpv['deal_type'] = 'V'
                                info_data['PVN1-I'].append(irpv)
                            
                    # summing up, what's left:
                    if (rpst['amount_untaxed'] >= 0.0 and rpst['amount_untaxed'] < rpst['limit_val']) or (rpst['amount_untaxed'] < 0.0 and (rpst['amount_untaxed'] * (-1.0)) < rpst['limit_val']):
                        amount_untaxed_a += rpst['amount_untaxed']
                        amount_tax_a += rpst['amount_tax']
                        amount_taxed_a += rpst['amount_taxed']

                # putting in values for document type "T":
                d_p_a = {
                    'amount_untaxed': amount_untaxed_a,
                    'amount_tax': amount_tax_a,
                    'amount_taxed': amount_taxed_a
                }
                if d_p_a['amount_taxed'] != 0.0:
                    data_of_file += "\n        <R>"
                    data_of_file += ("\n            <DarVeids>" + "T" + "</DarVeids>")
                    data_of_file += ("\n            <VertibaBezPvn>" + str(d_p_a['amount_untaxed']) + "</VertibaBezPvn>")
                    data_of_file += ("\n            <PvnVertiba>" + str(d_p_a['amount_tax']) + "</PvnVertiba>")
                    data_of_file += ("\n        </R>")
                    # info:
                    for info_rpt in r_purchase:
                        if info_rpt not in info_data['PVN1-I']:
                            irpt = info_rpt.copy()
                            irpt['deal_type'] = 'T'
                            info_data['PVN1-I'].append(irpt)

                data_of_file += "\n    </PVN1I>"

            # getting purchases from EU:
            if purchase_EU != []:
                info_data.update({'PVN1-II': purchase_EU}) # info
                data_of_file += "\n    <PVN1II>"

                for p_EU in purchase_EU:
                    data_of_file += "\n        <R>"

                    data_of_file += "\n            <DpValsts>" + unicode(p_EU['partner_country']) + "</DpValsts>"
                    data_of_file += "\n            <DpNumurs>" + str(p_EU['partner_vat']) + "</DpNumurs>"
                    data_of_file += "\n            <DpNosaukums>" + unicode(p_EU['partner_name']) + "</DpNosaukums>"
                    data_of_file += "\n            <DarVeids>" + str(p_EU['deal_type']) + "</DarVeids>"
                    data_of_file += "\n            <VertibaBezPvn>" + str(p_EU['amount_untaxed']) + "</VertibaBezPvn>"
                    data_of_file += "\n            <PvnVertiba>" + str(p_EU['amount_tax']) + "</PvnVertiba>"
                    data_of_file += "\n            <ValVertiba>" + str(p_EU['amount_untaxed_cur']) + "</ValVertiba>"
                    data_of_file += "\n            <ValKods>" + str(p_EU['currency']) + "</ValKods>"
                    data_of_file += "\n            <DokNumurs>" + unicode(p_EU['doc_number']) + "</DokNumurs>"
                    data_of_file += "\n            <DokDatums>" + str(p_EU['doc_date']) + "</DokDatums>"

                    data_of_file += "\n        </R>"

                data_of_file += "\n    </PVN1II>"

            # processing sale and sale_refund journal types:
            if r_sale != []:
                info_data.update({'PVN1-III': []})
                data_of_file += "\n    <PVN1III>"

                amount_untaxed_x = 0.0
                amount_tax_x = 0.0
                amount_taxed_x = 0.0
                d_s_s = {}
                r_s_s = []
                for s in r_sale:
                    # getting document types "X" or numbers:
                    if (s['amount_untaxed'] >= 0.0 and s['amount_untaxed'] >= s['limit_val']) or (s['amount_untaxed'] < 0.0 and (s['amount_untaxed'] * (-1.0)) >= s['limit_val']):
                        # number document types:
                        if check_fpos(s['partner_fpos'], 'LR_VAT_payer'):
                            data_of_file += "\n        <R>"
                            data_of_file += ("\n            <DpValsts>" + unicode(s['partner_country']) + "</DpValsts>")
                            data_of_file += ("\n            <DpNumurs>" + str(s['partner_vat']) + "</DpNumurs>")
                            data_of_file += ("\n            <DpNosaukums>" + unicode(s['partner_name']) + "</DpNosaukums>")
                            data_of_file += ("\n            <DarVeids>" + str(s['deal_type']) + "</DarVeids>")
                            data_of_file += ("\n            <VertibaBezPvn>" + str(s['amount_untaxed']) + "</VertibaBezPvn>")
                            data_of_file += ("\n            <PvnVertiba>" + str(s['amount_tax']) + "</PvnVertiba>")
                            data_of_file += ("\n            <DokVeids>" + str(s['doc_type']) + "</DokVeids>")
                            data_of_file += ("\n            <DokNumurs>" + unicode(s['doc_number']) + "</DokNumurs>")
                            data_of_file += ("\n            <DokDatums>" + str(s['doc_date']) + "</DokDatums>")
                            data_of_file += "\n        </R>"
                            info_data['PVN1-III'].append(s) # info
                        # "X" document types:
                        if check_fpos(s['partner_fpos'], 'LR_VAT_non-payer') or (not s['partner_vat']):
                            amount_untaxed_x += s['amount_untaxed']
                            amount_tax_x += s['amount_tax']
                            amount_taxed_x += s['amount_taxed']
                            # info:
                            si = s.copy()
                            si['doc_type'] = 'X'
                            info_data['PVN1-III'].append(si)
                    # summing up values for each partner:
                    if (s['amount_untaxed'] >= 0.0 and s['amount_untaxed'] < s['limit_val']) or (s['amount_untaxed'] < 0.0 and (s['amount_untaxed'] * (-1.0)) < s['limit_val']):
                        partner_id = s['partner_id']
                        partner_country = s['partner_country']
                        partner_vat = s['partner_vat']
                        partner_name = s['partner_name']
                        partner_fpos = s['partner_fpos']
                        amount_untaxed = s['amount_untaxed']
                        amount_tax = s['amount_tax']
                        amount_taxed = s['amount_taxed']
                        if d_s_s.get((partner_id)):
                            amount_untaxed += d_s_s[(partner_id)]['amount_untaxed']
                            amount_tax += d_s_s[(partner_id)]['amount_tax']
                            amount_taxed += d_s_s[(partner_id)]['amount_taxed']
                            d_s_s[(partner_id)].clear()
                        if not d_s_s.get((partner_id)):
                            d_s_s[(partner_id)] = {
                                'partner_id': partner_id,
                                'partner_country': partner_country,
                                'partner_vat': partner_vat,
                                'partner_name': partner_name,
                                'partner_fpos': partner_fpos,
                                'amount_untaxed': amount_untaxed,
                                'amount_tax': amount_tax,
                                'amount_taxed': amount_taxed,
                                'limit_val': s['limit_val']
                            }
                        r_s_s.append(d_s_s[(partner_id)])

                r_s_s_t = []
                for object in r_s_s:
                    if object != {}:
                        r_s_s_t.append(object)

                d_p_a = {}
                amount_untaxed_t = 0.0
                amount_tax_t = 0.0
                amount_taxed_t = 0.0
                for rsst in r_s_s_t:
                    # getting document type "V":
                    if (rsst['amount_untaxed'] >= 0.0 and rsst['amount_untaxed'] >= rsst['limit_val']) or (rsst['amount_untaxed'] < 0.0 and (rsst['amount_untaxed'] * (-1.0)) >= rsst['limit_val']):
                        data_of_file += "\n        <R>"
                        data_of_file += ("\n            <DpValsts>" + unicode(rsst['partner_country']) + "</DpValsts>")
                        data_of_file += ("\n            <DpNumurs>" + str(rsst['partner_vat']) + "</DpNumurs>")
                        data_of_file += ("\n            <DpNosaukums>" + unicode(rsst['partner_name']) + "</DpNosaukums>")
                        data_of_file += ("\n            <VertibaBezPvn>" + str(rsst['amount_untaxed']) + "</VertibaBezPvn>")
                        data_of_file += ("\n            <PvnVertiba>" + str(rsst['amount_tax']) + "</PvnVertiba>")
                        data_of_file += ("\n            <DokVeids>" + "V" + "</DokVeids>")
                        data_of_file += ("\n        </R>")
                        # info:
                        for info_rsv in r_sale:
                            if info_rsv['partner_id'] == rsst['partner_id'] and (info_rsv['amount_untaxed'] < rsst['limit_val'] or (info_rsv['amount_untaxed'] < 0.0 and (info_rsv['amount_untaxed'] * (-1.0)) < rsst['limit_val'])):
                                irsv = info_rsv.copy()
                                irsv['doc_type'] = 'V'
                                info_data['PVN1-III'].append(irsv)
                    # summing up, what's left:
                    if (rsst['amount_untaxed'] >= 0.0 and rsst['amount_untaxed'] < rsst['limit_val']) or (rsst['amount_untaxed'] < 0.0 and (rsst['amount_untaxed'] * (-1.0)) < rsst['limit_val']):
                        amount_untaxed_t += rsst['amount_untaxed']
                        amount_tax_t += rsst['amount_tax']
                        amount_taxed_t += rsst['amount_taxed']

                # putting in values for document type "T":
                d_s_t = {
                    'amount_untaxed': amount_untaxed_t,
                    'amount_tax': amount_tax_t,
                    'amount_taxed': amount_taxed_t
                }
                if d_s_t['amount_taxed'] != 0.0:
                    data_of_file += "\n        <R>"
                    data_of_file += ("\n            <VertibaBezPvn>" + str(d_s_t['amount_untaxed']) + "</VertibaBezPvn>")
                    data_of_file += ("\n            <PvnVertiba>" + str(d_s_t['amount_tax']) + "</PvnVertiba>")
                    data_of_file += ("\n            <DokVeids>" + "T" + "</DokVeids>")
                    data_of_file += ("\n        </R>")

                # putting in values for document type "X":
                d_s_x = {
                    'amount_untaxed': amount_untaxed_x,
                    'amount_tax': amount_tax_x,
                    'amount_taxed': amount_taxed_x
                }
                if d_s_x['amount_taxed'] != 0.0:
                    data_of_file += "\n        <R>"
                    data_of_file += ("\n            <VertibaBezPvn>" + str(d_s_x['amount_untaxed']) + "</VertibaBezPvn>")
                    data_of_file += ("\n            <PvnVertiba>" + str(d_s_x['amount_tax']) + "</PvnVertiba>")
                    data_of_file += ("\n            <DokVeids>" + "X" + "</DokVeids>")
                    data_of_file += ("\n        </R>")
                    # info:
                    for info_rst in r_sale:
                        if info_rst not in info_data['PVN1-III']:
                            irst = info_rst.copy()
                            irst['doc_type'] = 'T'
                            info_data['PVN1-III'].append(irst)

                data_of_file += "\n    </PVN1III>"

            # getting sales from EU:
            if sale_EU != []:
                info_data.update({'PVN2': sale_EU}) # info
                data_of_file += "\n    <PVN2>"

                s_EU_group = []
                s_EU_gd = {}
                for s_EU in sale_EU:
                    partner_id = s_EU['partner_id']
                    partner_country = s_EU['partner_country']
                    partner_vat = s_EU['partner_vat']
                    amount_untaxed_45 = s_EU['amount_untaxed_45']
                    amount_untaxed_48_2 = s_EU['amount_untaxed_48.2']
                    if s_EU_gd.get((partner_id)):
                        amount_untaxed_45 += s_EU_gd[(partner_id)]['amount_untaxed_45']
                        amount_untaxed_48_2 += s_EU_gd[(partner_id)]['amount_untaxed_48.2']
                        s_EU_gd[(partner_id)].clear()
                    if not s_EU_gd.get((partner_id)):
                        s_EU_gd[(partner_id)] = {
                                'partner_id': partner_id,
                                'partner_country': partner_country,
                                'partner_vat': partner_vat,
                                'amount_untaxed_45': amount_untaxed_45,
                                'amount_untaxed_48.2': amount_untaxed_48_2
                            }
                    s_EU_group.append(s_EU_gd[(partner_id)])

                s_EU_group_t = []
                for object in s_EU_group:
                    if object != {}:
                        s_EU_group_t.append(object)

                for s_EU_t in s_EU_group_t:
                    if s_EU_t['amount_untaxed_45'] != 0.0:
                        data_of_file += "\n        <R>"

                        data_of_file += "\n            <Valsts>" + unicode(s_EU_t['partner_country']) + "</Valsts>"
                        data_of_file += "\n            <PVNNumurs>" + str(s_EU_t['partner_vat']) + "</PVNNumurs>"
                        data_of_file += "\n            <Summa>" + str(s_EU_t['amount_untaxed_45']) + "</Summa>"
                        data_of_file += "\n            <Pazime>" + 'G' + "</Pazime>"

                        data_of_file += "\n        </R>"
                    if s_EU_t['amount_untaxed_48.2'] != 0.0:
                        data_of_file += "\n        <R>"

                        data_of_file += "\n            <Valsts>" + unicode(s_EU_t['partner_country']) + "</Valsts>"
                        data_of_file += "\n            <PVNNumurs>" + str(s_EU_t['partner_vat']) + "</PVNNumurs>"
                        data_of_file += "\n            <Summa>" + str(s_EU_t['amount_untaxed_48.2']) + "</Summa>"
                        data_of_file += "\n            <Pazime>" + 'P' + "</Pazime>"

                        data_of_file += "\n        </R>"

                data_of_file += "\n    </PVN2>"

        data_of_file += "\n</DokPVNv4>"

        data_of_file_real = base64.encodestring(data_of_file.encode('utf8'))

        # info:
        info_file_columns = [_("Document Number"), _("Deal Type"), _("Document Type"), _("Partner"), _("Untaxed Amount"), _("Tax Amount")]
        info_file_data = u",".join(info_file_columns)
        info_file_data += u"\n"
        for ikey, ivalue in info_data.iteritems():
            info_file_data += (",,,,,\n")
            info_file_data += (ikey + ",,,,,\n")
            for ival in ivalue:
                info_file_data += ((ival['doc_number'] and ('"' + ival['doc_number'].replace('"', '') + '"') or "") + ",")
                info_file_data += ((ival['deal_type'] and ('"' + ival['deal_type'].replace('"', '') + '"') or "") + ",")
                info_file_data += ((ival['doc_type'] and ('"' + ival['doc_type'].replace('"', '') + '"') or "") + ",")
                info_file_data += ((ival['partner_name'] and ('"' + ival['partner_name'].replace('"', '') + '"') or "") + ",")
                info_file_data += ((ival['amount_untaxed'] and str(ival['amount_untaxed']) or "") + ",")
                info_file_data += ((ival['amount_tax'] and str(ival['amount_tax']) or "") + "\n")
        info_file_data_real = base64.encodestring(info_file_data.encode('utf8'))

        self.write(cr, uid, ids, {
            'file_save': data_of_file_real,
            'name': data_tax.name,
            'info_file_name': data_tax.info_file_name,
            'info_file_save': info_file_data_real
        }, context=context)

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'l10n_lv.vat.declaration',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': data_tax.id,
            'views': [(False,'form')],
            'target': 'new',
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
