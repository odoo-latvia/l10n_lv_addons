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

from odoo import api, fields, models, _
import base64
import odoo.addons.decimal_precision as dp
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError

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

class L10nLvVatDeclaration(models.TransientModel):
    _name = "l10n_lv.vat.declaration"
    _inherit = "account.common.journal.report"
    _description = "VAT Declaration"

    @api.model
    def _default_partner(self):
        return self.env['res.users'].browse(self.env.uid).company_id.partner_id.id

    @api.model
    def _default_period(self):
        company = self.env['res.users'].browse(self.env.uid).company_id
        fy_last_day = company.fiscalyear_last_day
        fy_last_month = company.fiscalyear_last_month
        now = datetime.now()
        fy = now.year
        end_date = datetime(fy, fy_last_month, fy_last_day)
        start_date = end_date - relativedelta(years=1) + relativedelta(days=1)
        return {
            'date_from': start_date,
            'date_to': end_date
        }

    @api.model
    def _default_date_from(self):
        return self._default_period()['date_from'].strftime('%Y-%m-%d')

    @api.model
    def _default_date_to(self):
        return self._default_period()['date_to'].strftime('%Y-%m-%d')

    name = fields.Char(string='File Name', default='vat_declaration.xml')
    date_from = fields.Date(string='Date From', required=True, default=_default_date_from)
    date_to = fields.Date(string='Date To', required=True, default=_default_date_to)
    partner_id = fields.Many2one('res.partner', string='Related Partner', default=_default_partner)
    msg = fields.Text(string='File Created', readonly=True, default=_('Save the File.'))
    file_save = fields.Binary(string='Save File', filters='*.xml', readonly=True)
    amount_overpaid = fields.Float(string='Amount Overpaid', digits=dp.get_precision('Account'), readonly=True)
    transfer = fields.Boolean(string='Transfer')
    amount_to_transfer = fields.Float(string='Amount To Transfer', digits=dp.get_precision('Account'))
    bank_account_id = fields.Many2one('res.partner.bank', string='Bank Account')
    info_file_name = fields.Char(string='Info File Name', default='info.csv')
    info_file_save = fields.Binary('Save Information File', filters='*.csv', readonly=True, help='This file contains information about the documents used in VAT declaration.')

    @api.model
    def compute_tax_amount(self, tax, base):
        amount = 0.0
        child_taxes = []
        if tax:
            tax_amt = tax.compute_all(base)['taxes']
            for ta in tax_amt:
                if ta['id'] == tax.id:
                    t_amount = ta['amount']
                    if str(ta['amount'])[::-1].find('.') > 2:
                        t_amount = round(ta['amount'], 2)
                    amount += t_amount
                for c in tax.children_tax_ids:
                    if c.id == ta['id']:
                        c_amount = ta['amount']
                        if str(ta['amount'])[::-1].find('.') > 2:
                            c_amount = round(ta['amount'], 2)
                        child_taxes.append({
                            'tax': c, 
                            'amount': c_amount
                        })
        return amount, child_taxes

    @api.model
    def process_moves(self, moves):
        md = {
            '41': 0.0,
            '41.1': 0.0,
            '42': 0.0,
            '43': 0.0,
            '45': 0.0,
            '46': 0.0,
            '47': 0.0,
            '48': 0.0,
            '48.1': 0.0,
            '48.2': 0.0,
            '49': 0.0,
            '50': 0.0,
            '51': 0.0,
            '52': 0.0,
            '53': 0.0,
            '54': 0.0,
            '55': 0.0,
            '56': 0.0,
            '61': 0.0,
            '62': 0.0,
            '63': 0.0,
            '64': 0.0,
            '65': 0.0,
            '66': 0.0,
            '67': 0.0,
            '57': 0.0,
            'PVN1-I': [],
            'PVN1-II': [],
            'PVN1-III': [],
            'PVN2': []
        }
        ml_obj = self.env['account.move.line']
        for m in moves:
            if m.journal_id.type not in ['sale', 'purchase', 'expense']:
                continue
            tax_amt_data = []
            for line in m.line_ids:
                if line.tax_ids:
                    refund = False
                    if (m.journal_id.type in ['purchase', 'expense'] and line.credit not in [0.0, False]) or (m.journal_id.type == 'sale' and line.debit not in [0.0,False]):
                        refund = True
                    for tax in line.tax_ids:
                        if tax.amount_type == 'group':
                            tax_dict = {
                                'tax': tax,
                                'move': m,
                                'prod_type': line.product_id and line.product_id.type or False,
                                'base': line.debit or line.credit,
                                'base_cur': line.amount_currency and line.amount_currency or line.debit or line.credit,
                                'currency': line.currency_id and line.currency_id or line.move_id.journal_id.company_id.currency_id,
                                'refund': refund,
                                'partner': line.partner_id,
                                'child_taxes': []
                            }
                            for ctax in tax.children_tax_ids:
                                tax_mls = ml_obj.search([('move_id','=',m.id), ('tax_line_id','=',ctax.id)])
                                tax_amount = 0.0
                                for tm in tax_mls:
                                    tax_amount += (tm.debit or tm.credit)
                                tax_dict['child_taxes'].append({
                                    'tax': ctax,
                                    'amount': tax_amount
                                })
                            tax_amt_data.append(tax_dict)
                        else:
                            tax_mls = ml_obj.search([('move_id','=',m.id), ('tax_line_id','=',tax.id)])
                            tax_amount = 0.0
                            for tm in tax_mls:
                                tax_amount += (tm.debit or tm.credit)
                            tax_amt_data.append({
                                'tax': tax,
                                'move': m,
                                'prod_type': line.product_id and line.product_id.type or False,
                                'base': line.debit or line.credit,
                                'base_cur': line.amount_currency,
                                'currency': line.currency_id,
                                'refund': refund,
                                'partner': line.partner_id,
                                'amount': tax_amount
                            })

            tax_result = []
            tax_datas = {}
            for ta in tax_amt_data:
                tax = ta['tax']
                move = ta['move']
                prod_type = ta['prod_type']
                base = ta['base']
                base_cur = ta['base_cur']
                currency = ta['currency']
                refund = ta['refund']
                partner = ta['partner']
                amount = 'amount' in ta and ta['amount'] or 0.0
                child_taxes = 'child_taxes' in ta and ta['child_taxes'] or []
                prod_type_amt = {prod_type: {
                    'base': base,
                    'base_cur': base_cur,
                }}
                if tax_datas.get((tax.id)):
                    base += tax_datas[(tax.id)]['base']
                    base_cur += tax_datas[(tax.id)]['base_cur']
                    if prod_type in tax_datas[(tax.id)]['prod_type_amt']:
                        prod_type_amt[prod_type]['base'] += tax_datas[(tax.id)]['prod_type_amt'][prod_type]['base']
                        prod_type_amt[prod_type]['base_cur'] += tax_datas[(tax.id)]['prod_type_amt'][prod_type]['base_cur']
                    if prod_type not in tax_datas[(tax.id)]['prod_type_amt'] and tax_datas[(tax.id)]['prod_type_amt']:
                        prod_type_amt.update(tax_datas[(tax.id)]['prod_type_amt'])
                    tax_datas[(tax.id)].clear()
                if not tax_datas.get((tax.id)):
                    tax_datas[(tax.id)] = {
                        'tax': tax,
                        'move': move,
                        'base': base,
                        'base_cur': base_cur,
                        'currency': currency,
                        'refund': refund,
                        'partner': partner,
                        'amount': amount,
                        'child_taxes': child_taxes,
                        'prod_type': prod_type,
                        'prod_type_amt': prod_type_amt
                    }
                tax_result.append(tax_datas[(tax.id)])
            tax_result = [t for t in tax_result if t != {}]

            for tr in tax_result:
                sect_tags = [t.name for t in tr['tax'].tag_ids if t.name in ['PVN1-I', 'PVN1-II', 'PVN1-III', 'PVN2']]
                row_tags = []
                if not tr['child_taxes']:
                    row_tags = [t.name for t in tr['tax'].tag_ids if t.name not in ['PVN1-I', 'PVN1-II', 'PVN1-III', 'PVN2']]
                if not tr['refund']:
                    if 'PVN1-I' in sect_tags and tr['move'].journal_id.type == 'purchase':
                        md['PVN1-I'].append(tr)
                        if (not tr['child_taxes']) and '62' in row_tags:
                            md['62'] += tr['amount']
                        if tr['child_taxes']:
                            for ct in tr['child_taxes']:
                                row_tags = [t.name for t in ct['tax'].tag_ids if t.name not in ['PVN1-I', 'PVN1-II', 'PVN1-III', 'PVN2']]
                                if '62' in row_tags:
                                    md['62'] += ct['amount']
                                if '52' in row_tags:
                                    md['52'] += ct['amount']
                    if 'PVN1-II' in sect_tags:
                        if len(tr['prod_type_amt'].keys()) > 1:
                            for key, value in tr['prod_type_amt'].items():
                                p_amount, p_child_taxes = self.compute_tax_amount(tr['tax'], value['base'])
                                md['PVN1-II'].append({
                                    'tax': tr['tax'],
                                    'move': tr['move'],
                                    'base': value['base'],
                                    'base_cur': value['base_cur'],
                                    'currency': tr['currency'],
                                    'refund': tr['refund'],
                                    'partner': tr['partner'],
                                    'amount': p_amount,
                                    'child_taxes': p_child_taxes,
                                    'prod_type': key
                                })
                        else:
                            md['PVN1-II'].append(tr)
                        if tr['child_taxes']:
                            for ct in tr['child_taxes']:
                                row_tags = [t.name for t in ct['tax'].tag_ids if t.name not in ['PVN1-I', 'PVN1-II', 'PVN1-III', 'PVN2']]
                                if '64' in row_tags:
                                    md['64'] += ct['amount']
                                if '55' in row_tags:
                                    md['55'] += ct['amount']
                                if '50' in row_tags:
                                    md['50'] += tr['base']
                                if '56' in row_tags:
                                    md['56'] += ct['amount']
                                if '51' in row_tags:
                                    md['51'] += tr['base']
                    if 'PVN1-III' in sect_tags and tr['move'].journal_id.type == 'sale':
                        md['PVN1-III'].append(tr)
                        if not tr['child_taxes']:
                            if '52' in row_tags:
                                md['52'] += tr['amount']
                            if '41' in row_tags:
                                md['41'] += tr['base']
                            if '53' in row_tags:
                                md['53'] += tr['amount']
                            if '42' in row_tags:
                                md['42'] += tr['base']
                    if 'PVN2' in sect_tags:
                        if len(tr['prod_type_amt'].keys()) > 1:
                            for key, value in tr['prod_type_amt'].items():
                                p_amount, p_child_taxes = self.compute_tax_amount(tr['tax'], value['base'])
                                md['PVN2'].append({
                                    'tax': tr['tax'],
                                    'move': tr['move'],
                                    'base': value['base'],
                                    'base_cur': value['base_cur'],
                                    'currency': tr['currency'],
                                    'refund': tr['refund'],
                                    'partner': tr['partner'],
                                    'amount': p_amount,
                                    'child_taxes': p_child_taxes,
                                    'prod_type': key
                                })
                                if not tr['child_taxes']:
                                    if '45' in row_tags and key != 'service':
                                        md['45'] += value['base']
                                    if '48.2' in row_tags and key == 'service':
                                        md['48.2'] += value['base']
                        else:
                            md['PVN2'].append(tr)
                            if not tr['child_taxes']:
                                if '45' in row_tags and tr['prod_type'] != 'service':
                                    md['45'] += tr['base']
                                if '48.2' in row_tags and tr['prod_type'] == 'service':
                                    md['48.2'] += tr['base']
                if tr['refund']:
                    if 'PVN1-I' in sect_tags and tr['move'].journal_id.type == 'sale':
                        md['PVN1-I'].append(tr)
                        if (not tr['child_taxes']) and '67' in row_tags:
                            md['67'] += tr['amount']
                    if 'PVN1-II' in sect_tags:
                        if len(tr['prod_type_amt'].keys()) > 1:
                            for key, value in tr['prod_type_amt'].items():
                                p_amount, p_child_taxes = self.compute_tax_amount(tr['tax'], value['base'])
                                md['PVN1-II'].append({
                                    'tax': tr['tax'],
                                    'move': tr['move'],
                                    'base': value['base'],
                                    'base_cur': value['base_cur'],
                                    'currency': tr['currency'],
                                    'refund': tr['refund'],
                                    'partner': tr['partner'],
                                    'amount': p_amount,
                                    'child_taxes': p_child_taxes,
                                    'prod_type': key
                                })
                        else:
                            md['PVN1-II'].append(tr)
                        if tr['child_taxes']:
                            for ct in tr['child_taxes']:
                                row_tags = [t.name for t in ct['tax'].tag_ids if t.name not in ['PVN1-I', 'PVN1-II', 'PVN1-III', 'PVN2']]
                                if '64' in row_tags:
                                    md['64'] -= ct['amount']
                                if '55' in row_tags:
                                    md['55'] -= ct['amount']
                                if '50' in row_tags:
                                    md['50'] -= tr['base']
                                if '56' in row_tags:
                                    md['56'] -= ct['amount']
                                if '51' in row_tags:
                                    md['51'] -= tr['base']
                    if 'PVN1-III' in sect_tags and tr['move'].journal_id.type == 'purchase':
                        md['PVN1-III'].append(tr)
                        if (not tr['child_taxes']) and '57' in row_tags:
                            md['57'] += tr['amount']
                        if tr['child_taxes']:
                            for ct in tr['child_taxes']:
                                row_tags = [t.name for t in ct['tax'].tag_ids if t.name not in ['PVN1-I', 'PVN1-II', 'PVN1-III', 'PVN2']]
                                if '62' in row_tags:
                                    md['62'] -= ct['amount']
                                if '52' in row_tags:
                                    md['52'] -= ct['amount']
                    if 'PVN2' in sect_tags:
                        if len(tr['prod_type_amt'].keys()) > 1:
                            for key, value in tr['prod_type_amt'].items():
                                p_amount, p_child_taxes = self.compute_tax_amount(tr['tax'], value['base'])
                                md['PVN2'].append({
                                    'tax': tr['tax'],
                                    'move': tr['move'],
                                    'base': value['base'],
                                    'base_cur': value['base_cur'],
                                    'currency': tr['currency'],
                                    'refund': tr['refund'],
                                    'partner': tr['partner'],
                                    'amount': p_amount,
                                    'child_taxes': p_child_taxes,
                                    'prod_type': key
                                })
                                if not tr['child_taxes']:
                                    if '45' in row_tags and key != 'service':
                                        md['45'] -= value['base']
                                    if '48.2' in row_tags and key == 'service':
                                         md['48.2'] -= value['base']
                        else:
                            md['PVN2'].append(tr)
                            if not tr['child_taxes']:
                                if '45' in row_tags and tr['prod_type'] != 'service':
                                    md['45'] -= tr['base']
                                if '48.2' in row_tags and tr['prod_type'] == 'service':
                                    md['48.2'] -= tr['base']

        return md

    @api.model
    def form_partner_data(self, partner):
        country = partner and partner.country_id and partner.country_id.code or False
        vat_no = partner and partner.vat or False
        vat = False
        if vat_no:
            vat_no = vat_no.replace(' ','').upper()
            if vat_no[:2].isalpha():
                vat = vat_no[2:]
                country = vat_no[:2]
            else:
                vat = vat_no
        if country == 'GR':
            country = 'EL'
        if partner and (not vat) and hasattr(partner, 'company_registry'):
            vat = partner.company_registry
        return {
            'country': country,
            'vat': vat,
            'id': partner and partner.id or False,
            'name': partner and partner.name or False,
            'fpos': partner and partner.property_account_position_id and partner.property_account_position_id.name or False
        }

    @api.model
    def form_pvn1i_data(self, data, data_of_file, info_data):
        partner_data = {}
        info_data.update({'PVN1-I': []})
        move_data = {}
        for d in data:
            limit_val = 1430.0
            if d['move'].date <= fields.Date.from_string('2013-12-31'):
                limit_val = 1000.0
            if d['move'].date <= fields.Date.from_string('2017-12-31'):
                limit_val = 150.0
            partner = self.form_partner_data(d['partner'])
            deal_type = ""
            doc_type = "1"
            if partner['vat'] and partner['fpos'] and (check_fpos(partner['fpos'], 'LR_VAT_payer') or check_fpos(partner['fpos'], 'EU_VAT_payer')):
                deal_type = "A"
            if (not partner['vat']) and partner['fpos'] and (check_fpos(partner['fpos'], 'LR_VAT_payer') or check_fpos(partner['fpos'], 'EU_VAT_payer')):
                raise UserError(_('No TIN defined for Partner %s, but this partner is defined as a VAT payer. Please define the TIN!') % (partner['name']))
            if (not partner['vat']) or check_fpos(partner['fpos'], 'LR_VAT_non-payer') or check_fpos(partner['fpos'], 'EU_VAT_non-payer'):
                deal_type = "N"
            row_tags = [tag.name for tag in d['tax'].tag_ids if tag.name not in ['PVN1-I', 'PVN1-II', 'PVN1-III', 'PVN2']]
            if not row_tags:
                row_tags = [tag.name for child in d['child_taxes'] for tag in child['tax'].tag_ids]
            if '61' in row_tags:
                deal_type = "I"
                doc_type = "6"
                limit_val = 0.0
            if '65' in row_tags:
                deal_type = "K"
            if '62' in row_tags and '52' in row_tags:
                deal_type = "R4"
                limit_val = 0.0
            if d['refund']:
                doc_type = "4"
                limit_val = 0.0
            if doc_type != "6" and (not len(self.env['account.move'].search([('id','=',d['move'].id)]))) and d['move'].journal_id.type != 'expense':
                doc_type = "5"
            # getting tax amount:
            if not d['child_taxes']:
                tax_amount = d['amount']
            else:
                for c in d['child_taxes']:
                    c_tags = [t.name for t in c['tax'].tag_ids]
                    if '62' in c_tags or '67' in c_tags:
                        tax_amount = c['amount']
            base = d['refund'] and d['base'] * (-1.0) or d['base']
            tax_amount = d['refund'] and tax_amount * (-1.0) or tax_amount
            # getting document types "A", "N" and "I":
            if d['base'] >= limit_val:
                data_of_file += "\n        <R>"
                if deal_type != "I" and partner['country']:
                    data_of_file += ("\n            <DpValsts>" + partner['country'] + "</DpValsts>")
                if partner['vat'] and deal_type not in ["I", "N"]:
                    data_of_file += ("\n            <DpNumurs>" + str(partner['vat']) + "</DpNumurs>")
                data_of_file += ("\n            <DpNosaukums>" + partner['name'] + "</DpNosaukums>")
                data_of_file += ("\n            <DarVeids>" + deal_type + "</DarVeids>")
                data_of_file += ("\n            <VertibaBezPvn>" + str(base) + "</VertibaBezPvn>")
                data_of_file += ("\n            <PvnVertiba>" + str(tax_amount) + "</PvnVertiba>")
                data_of_file += ("\n            <DokVeids>" + doc_type + "</DokVeids>")
                data_of_file += ("\n            <DokNumurs>" + d['move'].name + "</DokNumurs>")
                data_of_file += ("\n            <DokDatums>" + d['move'].date + "</DokDatums>")
                data_of_file += ("\n        </R>")
                # updating document information:
                info_data['PVN1-I'].append({
                    'doc_number': d['move'].name,
                    'deal_type': deal_type,
                    'doc_type': doc_type,
                    'partner_name': partner['name'],
                    'base': base,
                    'tax_amount': tax_amount
                })
            if d['base'] < limit_val:
                # getting data for document information:
                if d['move'].id in move_data:
                    move_data[d['move'].id]['base'] += base
                    move_data[d['move'].id]['tax_amount'] += tax_amount
                if d['move'].id not in move_data:
                    move_data.update({d['move'].id: d})
                    move_data[d['move'].id].update({
                        'base': base,
                        'tax_amount': tax_amount
                    })
                # summing up, what's left for each partner:
                if d['partner'] in partner_data:
                    partner_data[d['partner']]['base'] += base
                    partner_data[d['partner']]['tax_amount'] += tax_amount
                    if d['move'] not in partner_data[d['partner']]['moves']:
                        partner_data[d['partner']]['moves'].append(d['move'])
                if d['partner'] not in partner_data:
                    partner_data.update({d['partner']: {
                        'limit_val': limit_val,
                        'base': base,
                        'tax_amount': tax_amount,
                        'moves': [d['move']]
                    }})
        other_data = {}
        for p, p_data in partner_data.items():
            partner = self.form_partner_data(p)
            if p_data['base'] >= p_data['limit_val']:
                # getting document type "V":
                data_of_file += "\n        <R>"
                data_of_file += ("\n            <DpValsts>" + partner['country'] + "</DpValsts>")
                if partner['vat']:
                     data_of_file += ("\n            <DpNumurs>" + str(partner['vat']) + "</DpNumurs>")
                data_of_file += ("\n            <DpNosaukums>" + partner['name'] + "</DpNosaukums>")
                data_of_file += ("\n            <DarVeids>" + "V" + "</DarVeids>")
                data_of_file += ("\n            <VertibaBezPvn>" + str(p_data['base']) + "</VertibaBezPvn>")
                data_of_file += ("\n            <PvnVertiba>" + str(p_data['tax_amount']) + "</PvnVertiba>")
                data_of_file += ("\n        </R>")
                # updating document information:
                for move in p_data['moves']:
                    if move.id in move_data:
                        info_data['PVN1-I'].append({
                            'doc_number': move_data[move.id]['move'].name,
                            'deal_type': "V",
                            'doc_type': '',
                            'partner_name': partner['name'],
                            'base': move_data[move.id]['base'],
                            'tax_amount': move_data[move.id]['tax_amount']
                        })
            if p_data['base'] < p_data['limit_val']:
                # summing up, what's left:
                if 'base' in other_data:
                    other_data['base'] += p_data['base']
                if 'base' not in other_data:
                    other_data.update({'base': p_data['base']})
                if 'tax_amount' in other_data:
                    other_data['tax_amount'] += p_data['tax_amount']
                if 'tax_amount' not in other_data:
                    other_data.update({'tax_amount': p_data['tax_amount']})
                if 'moves' in other_data:
                    other_data['moves'] += p_data['moves']
                if 'moves' not in other_data:
                    other_data.update({'moves': p_data['moves']})
        if other_data:
            # putting in values for document type "T":
            data_of_file += "\n        <R>"
            data_of_file += ("\n            <DarVeids>" + "T" + "</DarVeids>")
            data_of_file += ("\n            <VertibaBezPvn>" + str(other_data['base']) + "</VertibaBezPvn>")
            data_of_file += ("\n            <PvnVertiba>" + str(other_data['tax_amount']) + "</PvnVertiba>")
            data_of_file += ("\n        </R>")
            # updating document information:
            for move in other_data['moves']:
                if move.id in move_data:
                    partner = self.form_partner_data(move_data[move.id]['partner'])
                    info_data['PVN1-I'].append({
                        'doc_number': move_data[move.id]['move'].name,
                        'deal_type': "T",
                        'doc_type': '',
                        'partner_name': partner['name'],
                        'base': move_data[move.id]['base'],
                        'tax_amount': move_data[move.id]['tax_amount']
                    })
        return data_of_file, info_data

    @api.model
    def form_pvn1ii_data(self, data, data_of_file, info_data):
        info_data.update({'PVN1-II': []})
        for d in data:
            deal_type = d['prod_type'] in ['service', False] and 'P' or 'G'
            partner = self.form_partner_data(d['partner'])
            # getting tax amount:
            if not d['child_taxes']:
                tax_amount = d['amount']
            else:
                for c in d['child_taxes']:
                    c_tags = [t.name for t in c['tax'].tag_ids]
                    if '64' in c_tags:
                        tax_amount = c['amount']
            base = d['refund'] and d['base'] * (-1.0) or d['base']
            base_cur = d['refund'] and d['base_cur'] * (-1.0) or d['base_cur']
            tax_amount = d['refund'] and tax_amount * (-1.0) or tax_amount
            data_of_file += "\n        <R>"
            data_of_file += "\n            <DpValsts>" + partner['country'] + "</DpValsts>"
            data_of_file += "\n            <DpNumurs>" + str(partner['vat']) + "</DpNumurs>"
            data_of_file += "\n            <DpNosaukums>" + partner['name'] + "</DpNosaukums>"
            data_of_file += "\n            <DarVeids>" + deal_type + "</DarVeids>"
            data_of_file += "\n            <VertibaBezPvn>" + str(base) + "</VertibaBezPvn>"
            data_of_file += "\n            <PvnVertiba>" + str(tax_amount) + "</PvnVertiba>"
            data_of_file += "\n            <ValVertiba>" + str(base_cur) + "</ValVertiba>"
            data_of_file += "\n            <ValKods>" + str(d['currency'].name) + "</ValKods>"
            data_of_file += "\n            <DokNumurs>" + d['move'].name + "</DokNumurs>"
            data_of_file += "\n            <DokDatums>" + str(d['move'].date) + "</DokDatums>"
            data_of_file += "\n        </R>"
            # updating document information:
            info_data['PVN1-II'].append({
                'doc_number': d['move'].name,
                'deal_type': deal_type,
                'doc_type': '',
                'partner_name': partner['name'],
                'base': base,
                'tax_amount': tax_amount
            })
        return data_of_file, info_data

    @api.model
    def form_pvn1iii_data(self, data, data_of_file, info_data):
        x_data = {}
        partner_data = {}
        info_data.update({'PVN1-III': []})
        move_data = {}
        for d in data:
            limit_val = 1430.0
            if d['move'].date <= fields.Date.from_string('2013-12-31'):
                limit_val = 1000.0
            if d['move'].date <= fields.Date.from_string('2017-12-31'):
                limit_val = 150.0
            partner = self.form_partner_data(d['partner'])
            # getting tax amount and deal type:
            row_codes = [tag.name for tag in d['tax'].tag_ids if tag.name not in ['PVN1-I', 'PVN1-II', 'PVN1-III', 'PVN2']]
            if not d['child_taxes']:
                tax_amount = d['amount']
            else:
                for c in d['child_taxes']:
                    c_tags = [t.name for t in c['tax'].tag_ids]
                    if '52' in c_tags or '53' in c_tags or '57' in c_tags:
                        tax_amount = c['amount'] < 0.0 and c['amount'] * (-1.0) or c['amount']
                    row_codes += c_tags
            row_codes = list(set(row_codes))
            deal_type = len(row_codes) == 1 and row_codes[0] or ''
            if not deal_type:
                if '41' in row_codes:
                    deal_type = '41'
                if '41.1' in row_codes:
                    deal_type = '41.1'
                if '42' in row_codes:
                    deal_type = '42'
                if '43' in row_codes:
                    deal_type = '43'
                if '44' in row_codes:
                    deal_type = '44'
                if '48.2' in row_codes:
                    deal_type = '48.2'
            # getting doc type:
            doc_type = "5"
            invoices = [l.invoice_id.id for m in d['move'] for l in m.line_ids if l.invoice_id]
            if invoices:
                doc_type = "1"
                if d['refund']:
                    doc_type = "4"
                    limit_val = 0.0
            # getting amounts:
            base = d['refund'] and d['base'] * (-1.0) or d['base']
            tax_amount = d['refund'] and tax_amount * (-1.0) or tax_amount
            # getting document types "X" or numbers:
            if base >= limit_val:
                # number document types:
                if check_fpos(partner['fpos'], 'LR_VAT_payer'):
                    data_of_file += "\n        <R>"
                    data_of_file += ("\n            <DpValsts>" + partner['country'] + "</DpValsts>")
                    data_of_file += ("\n            <DpNumurs>" + str(partner['vat']) + "</DpNumurs>")
                    data_of_file += ("\n            <DpNosaukums>" + partner['name'] + "</DpNosaukums>")
                    data_of_file += ("\n            <DarVeids>" + str(deal_type) + "</DarVeids>")
                    data_of_file += ("\n            <VertibaBezPvn>" + str(base) + "</VertibaBezPvn>")
                    data_of_file += ("\n            <PvnVertiba>" + str(tax_amount) + "</PvnVertiba>")
                    data_of_file += ("\n            <DokVeids>" + str(doc_type) + "</DokVeids>")
                    data_of_file += ("\n            <DokNumurs>" + d['move'].name + "</DokNumurs>")
                    data_of_file += ("\n            <DokDatums>" + str(d['move'].date) + "</DokDatums>")
                    data_of_file += "\n        </R>"
                    # updating document information:
                    info_data['PVN1-III'].append({
                        'doc_number': d['move'].name,
                        'deal_type': deal_type,
                        'doc_type': doc_type,
                        'partner_name': partner['name'],
                        'base': base,
                        'tax_amount': tax_amount
                    })
                # "X" document types:
                if check_fpos(partner['fpos'], 'LR_VAT_non-payer') or (not partner['vat']):
                    if 'base' in x_data:
                        x_data['base'] += base
                    if base not in x_data:
                        x_data.update({'base': base})
                    if 'tax_amount' in x_data:
                        x_data['tax_amount'] += tax_amount
                    if 'tax_amount' not in x_data:
                        x_data.update({'tax_amount': tax_amount})
                    # updating document information:
                    info_data['PVN1-III'].append({
                        'doc_number': d['move'].name,
                        'deal_type': '',
                        'doc_type': "X",
                        'partner_name': partner['name'],
                        'base': base,
                        'tax_amount': tax_amount
                    })
            if d['base'] < limit_val:
                # getting data for document information:
                if d['move'].id in move_data:
                    move_data[d['move'].id]['base'] += base
                    move_data[d['move'].id]['tax_amount'] += tax_amount
                if d['move'].id not in move_data:
                    move_data.update({d['move'].id: d})
                    move_data[d['move'].id].update({
                        'base': base,
                        'tax_amount': tax_amount
                    })
                # summing up, what's left for each partner:
                if d['partner'] in partner_data:
                    partner_data[d['partner']]['base'] += base
                    partner_data[d['partner']]['tax_amount'] += tax_amount
                    if d['move'] not in partner_data[d['partner']]['moves']:
                        partner_data[d['partner']]['moves'].append(d['move'])
                if d['partner'] not in partner_data:
                    partner_data.update({d['partner']: {
                        'limit_val': limit_val,
                        'base': base,
                        'tax_amount': tax_amount,
                        'moves': [d['move']]
                    }})
        other_data = {}
        for p, p_data in partner_data.items():
            partner = self.form_partner_data(p)
            # getting document type "V":
            if p_data['base'] >= p_data['limit_val']:
                data_of_file += "\n        <R>"
                data_of_file += ("\n            <DpValsts>" + partner['country'] + "</DpValsts>")
                data_of_file += ("\n            <DpNumurs>" + str(partner['vat']) + "</DpNumurs>")
                data_of_file += ("\n            <DpNosaukums>" + partner['name'] + "</DpNosaukums>")
                data_of_file += ("\n            <VertibaBezPvn>" + str(p_data['base']) + "</VertibaBezPvn>")
                data_of_file += ("\n            <PvnVertiba>" + str(p_data['tax_amount']) + "</PvnVertiba>")
                data_of_file += ("\n            <DokVeids>" + "V" + "</DokVeids>")
                data_of_file += "\n        </R>"
                # updating document information:
                for move in p_data['moves']:
                    if move.id in move_data:
                        info_data['PVN1-III'].append({
                            'doc_number': move_data[move.id]['move'].name,
                            'deal_type': '',
                            'doc_type': "V",
                            'partner_name': partner['name'],
                            'base': move_data[move.id]['base'],
                            'tax_amount': move_data[move.id]['tax_amount']
                        })
            # summing up, what's left:
            if p_data['base'] < p_data['limit_val']:
                if 'base' in other_data:
                    other_data['base'] += p_data['base']
                if 'base' not in other_data:
                    other_data.update({'base': p_data['base']})
                if 'tax_amount' in other_data:
                    other_data['tax_amount'] += p_data['tax_amount']
                if 'tax_amount' not in other_data:
                    other_data.update({'tax_amount': p_data['tax_amount']})
                if 'moves' in other_data:
                    other_data['moves'] += p_data['moves']
                if 'moves' not in other_data:
                    other_data.update({'moves': p_data['moves']})
        # putting in values for document type "T":
        if other_data:
            data_of_file += "\n        <R>"
            data_of_file += ("\n            <VertibaBezPvn>" + str(other_data['base']) + "</VertibaBezPvn>")
            data_of_file += ("\n            <PvnVertiba>" + str(other_data['tax_amount']) + "</PvnVertiba>")
            data_of_file += ("\n            <DokVeids>" + "T" + "</DokVeids>")
            data_of_file += ("\n        </R>")
            # updating document information:
            for move in other_data['moves']:
                if move.id in move_data:
                    partner = self.form_partner_data(move_data[move.id]['partner'])
                    info_data['PVN1-III'].append({
                        'doc_number': move_data[move.id]['move'].name,
                        'deal_type': '',
                        'doc_type': "T",
                        'partner_name': partner['name'],
                        'base': move_data[move.id]['base'],
                        'tax_amount': move_data[move.id]['tax_amount']
                    })
        # putting in values for document type "X":
        if x_data:
            data_of_file += "\n        <R>"
            data_of_file += ("\n            <VertibaBezPvn>" + str(x_data['base']) + "</VertibaBezPvn>")
            data_of_file += ("\n            <PvnVertiba>" + str(x_data['tax_amount']) + "</PvnVertiba>")
            data_of_file += ("\n            <DokVeids>" + "X" + "</DokVeids>")
            data_of_file += ("\n        </R>")
        return data_of_file, info_data

    @api.model
    def form_pvn2_data(self, data, data_of_file, info_data):
        info_data.update({'PVN2': []})
        partner_data = {}
        for d in data:
            partner = self.form_partner_data(d['partner'])
            deal_type = d['prod_type'] in ['service', False] and 'P' or 'G'
            # getting tax amount:
            if not d['child_taxes']:
                tax_amount = d['amount']
            else:
                for c in d['child_taxes']:
                    c_tags = [t.name for t in c['tax'].tag_ids]
                    if '45' in c_tags:
                        tax_amount = c['amount']
            base = d['refund'] and d['base'] * (-1.0) or d['base']
            tax_amount = d['refund'] and tax_amount * (-1.0) or tax_amount
            if (d['partner'], deal_type) in partner_data:
                partner_data[(d['partner'], deal_type)]['base'] += base
                partner_data[(d['partner'], deal_type)]['tax_amount'] += tax_amount
            if (d['partner'], deal_type) not in partner_data:
                partner_data.update({(d['partner'], deal_type): {
                    'base': base,
                    'tax_amount': tax_amount
                }})
            # updating document information:
            info_data['PVN2'].append({
                'doc_number': d['move'].name,
                'deal_type': deal_type,
                'doc_type': '',
                'partner_name': partner['name'],
                'base': base,
                'tax_amount': tax_amount
            })
        for pd, p_data in partner_data.items():
            partner = self.form_partner_data(pd[0])
            data_of_file += "\n        <R>"
            data_of_file += "\n            <Valsts>" + partner['country'] + "</Valsts>"
            data_of_file += "\n            <PVNNumurs>" + str(partner['vat']) + "</PVNNumurs>"
            data_of_file += "\n            <Summa>" + str(p_data['base']) + "</Summa>"
            data_of_file += "\n            <Pazime>" + pd[1] + "</Pazime>"
            data_of_file += "\n        </R>"
        return data_of_file, info_data

    @api.model
    def create_file(self):
        self.ensure_one()
        company = self.env['res.users'].browse(self.env.uid).company_id
        partner_obj = self.env['res.partner']
        move_obj = self.env['account.move']

        # defining file content:
        data_of_file = """<?xml version="1.0"?>
<DokPVNv4 xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <ParskGads>%(year)s</ParskGads>""" % ({'year': str(self.date_to.year)})

        # getting info for period tags:
        start_date = self.date_from
        end_date = self.date_to + timedelta(days=1)
        diff = relativedelta(end_date, start_date)
        diff_month = diff.months + (diff.years * 12)
        if diff_month == 1:
            data_of_file += "\n    <ParskMen>" + str(int(start_date.month)) + "</ParskMen>"
        if diff_month in [3, 6]:
            fy_end_date = datetime(start_date.year, company.fiscalyear_last_month, company.fiscalyear_last_day)
            diff_fy = relativedelta(start_date, fy_end_date - relativedelta(years=1) + timedelta(days=1))
            diff_month_fy = diff_fy.months + (diff_fy.years * 12)
            if diff_month == 3 and diff_month_fy in [3, 6, 9]:
                quarter = (diff_month_fy == 9 and 4) or (diff_month_fy == 6 and 3) or (diff_month_fy == 3 and 2) or 1
                data_of_file += "\n    <ParskCeturksnis>" + str(quarter) + "</ParskCeturksnis>"
            if diff_month == 6 and diff_month_fy in [0, 6]:
                half_year = (diff_month_fy == 6) and 2 or 1
                data_of_file += "\n    <TaksPusgads>" + str(half_year) + "</TaksPusgads>"

        # getting company VAT number (company registry):
        vat_no = company.partner_id.vat
        if vat_no:
            vat_no = vat_no.replace(' ','').upper()
            if vat_no[:2].isalpha():
                vat = vat_no[2:]
            else:
                vat = vat_no
            data_of_file += "\n    <NmrKods>" + str(vat) + "</NmrKods>"
        if not vat_no:
            vat = company.company_registry
            data_of_file += "\n    <NmrKods>" + str(vat) + "</NmrKods>"
            if not vat:
                raise UserError(_('No TIN or Company Registry number associated with your company.'))

        # getting e-mail and phone:
        default_address = company.partner_id.address_get().get("default", company.partner_id)
        if default_address.email:
            data_of_file += "\n    <Epasts>" + default_address.email + "</Epasts>"
        if default_address.phone:
            phone = default_address.phone.replace('.','').replace('/','').replace('(','').replace(')','').replace(' ','')
            data_of_file += "\n    <Talrunis>" + phone + "</Talrunis>"

        #TODO: needs overpaid (420)

        moves = move_obj.search([('date','<=',self.date_to), ('date','>=',self.date_from), ('state','=','posted'), ('journal_id.type','in',['sale', 'purchase','expense'])])
        move_data = self.process_moves(moves)
        info_data = {}

        add_pvn = False
        for key, value in move_data.items():
            if value != 0.0 and value != []:
                add_pvn = True

        if add_pvn == True:
            pvn_rows = ['41', '41.1', '42', '43', '45', '46', '47', '48', '48.1', '48.2', '49', '50', '51', '52', '53', '54', '55', '56', '61', '62', '63', '64', '65', '66', '67', '57']
            data_of_file += "\n    <PVN>"
            for row in pvn_rows:
                if move_data.get(row, 0.0) != 0.0:
                    tag_name = row.replace('.','')
                    data_of_file += ("\n        <R%s>%s</R%s>" % (tag_name, move_data[row], tag_name))
            data_of_file += "\n    </PVN>"
            if move_data.get('PVN1-I', []):
                data_of_file += "\n    <PVN1-I>"
                data_of_file, info_data = self.form_pvn1i_data(move_data['PVN1-I'], data_of_file, info_data)
                data_of_file += "\n    </PVN1-I>"
            if move_data.get('PVN1-II', []):
                data_of_file += "\n    <PVN1-II>"
                data_of_file, info_data = self.form_pvn1ii_data(move_data['PVN1-II'], data_of_file, info_data)
                data_of_file += "\n    </PVN1-II>"
            if move_data.get('PVN1-III', []):
                data_of_file += "\n    <PVN1-III>"
                data_of_file, info_data = self.form_pvn1iii_data(move_data['PVN1-III'], data_of_file, info_data)
                data_of_file += "\n    </PVN1-III>"
            if move_data.get('PVN2', []):
                data_of_file += "\n    <PVN2>"
                data_of_file, info_data = self.form_pvn2_data(move_data['PVN2'], data_of_file, info_data)
                data_of_file += "\n    </PVN2>"

        data_of_file += "\n</DokPVNv4>"

        data_of_file_real = base64.encodestring(data_of_file.encode('utf8'))

        # info:
        info_file_columns = [_("Document Number"), _("Deal Type"), _("Document Type"), _("Partner"), _("Untaxed Amount"), _("Tax Amount")]
        info_file_data = u",".join(info_file_columns)
        info_file_data += u"\n"
        ikey_list = ['PVN1-I', 'PVN1-II', 'PVN1-III', 'PVN2']
        for ikey in ikey_list:
            ivalue = info_data.get(ikey, [])
            if ivalue:
                info_file_data += ",,,,,\n"
                info_file_data += (ikey.replace('-', '') + ",,,,,\n")
                for ival in ivalue:
                    info_file_data += ((ival['doc_number'] and ('"' + ival['doc_number'].replace('"', '') + '"') or "") + ",")
                    info_file_data += ((ival['deal_type'] and ('"' + ival['deal_type'].replace('"', '') + '"') or "") + ",")
                    info_file_data += ((ival['doc_type'] and ('"' + ival['doc_type'].replace('"', '') + '"') or "") + ",")
                    info_file_data += ((ival['partner_name'] and ('"' + ival['partner_name'].replace('"', '') + '"') or "") + ",")
                    info_file_data += ((ival['base'] and str(ival['base']) or "") + ",")
                    info_file_data += ((ival['tax_amount'] and str(ival['tax_amount']) or "") + "\n")
        info_file_data_real = base64.encodestring(info_file_data.encode('utf8'))

        self.write({
            'file_save': data_of_file_real,
            'name': self.name,
            'info_file_name': self.info_file_name,
            'info_file_save': info_file_data_real
        })

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'l10n_lv.vat.declaration',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': self.id,
            'views': [(False,'form')],
            'target': 'new',
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
