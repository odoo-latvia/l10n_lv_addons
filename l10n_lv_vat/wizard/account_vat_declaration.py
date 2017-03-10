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
from datetime import datetime
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
        return self._default_period()['date_from']

    @api.model
    def _default_date_to(self):
        return self._default_period()['date_to']

    name = fields.Char(string='File Name', default='vat_declaration.xml')
    date_from = fields.Date(string='Date From', required=True, default=_default_date_from)
    date_to = fields.Date(string='Date To', required=True, default=_default_date_to)
    partner_id = fields.Many2one('res.partner', string='Related Partner', default=_default_partner)
    msg = fields.Text(string='File Created', readonly=True, default='Save the File.')
    file_save = fields.Binary(string='Save File', filters='*.xml', readonly=True)
    amount_overpaid = fields.Float(string='Amount Overpaid', digits=dp.get_precision('Account'), readonly=True)
    transfer = fields.Boolean(string='Transfer')
    amount_to_transfer = fields.Float(string='Amount To Transfer', digits=dp.get_precision('Account'))
    bank_account_id = fields.Many2one('res.partner.bank', string='Bank Account')
    info_file_name = fields.Char(string='Info File Name', default='info.csv')
    info_file_save = fields.Binary('Save Information File', filters='*.csv', readonly=True, help='This file contains information about the documents used in VAT declaration.')

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
        base_tags = ['50', '51', '41', '42', '45', '48.2']
        ml_obj = self.env['account.move.line']
        for m in moves:
            if m.journal_id.type not in ['sale', 'purchase', 'expense']:
                continue
#            invoices = list(set([ml.invoice_id for ml in m.line_ids]))
#            inv_type = invoices and invoices[0].type or False
#            j_type = m.journal_id.type
            tax_amt_data = []
            for line in m.line_ids:
                if line.tax_ids:
                    refund = False
                    if (m.journal_id.type in ['purchase', 'expense'] and line.credit != 0.0) or (m.journal_id.type == 'sale' and line.debit != 0.0):
                        refund = True
                    for tax in line.tax_ids:
                        if tax.amount_type == 'group':
                            tax_dict = {
                                'tax': tax,
                                'move': m,
                                'base': line.debit or line.credit,
                                'base_cur': line.amount_currency,
                                'currency': line.currency_id,
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
                base = ta['base']
                base_cur = ta['base_cur']
                currency = ta['currency']
                refund = ta['refund']
                partner = ta['partner']
                amount = 'amount' in ta and ta['amount'] or 0.0
                child_taxes = 'child_taxes' in ta and ta['child_taxes'] or []
                if tax_datas.get((tax.id)):
                    base += tax_datas[(tax.id)]['base']
                    base_cur += tax_datas[(tax.id)]['base_cur']
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
                        'child_taxes': child_taxes
                    }
                tax_result.append(tax_datas[(tax.id)])
            tax_result2 = []
            for object in tax_result:
                if object != {}:
                    tax_result2.append(object)

            for tr in tax_result2:
                sect_tags = [t.name for t in tr['tax'].tag_ids if t.name in ['PVN1-I', 'PVN1-II', 'PVN1-III', 'PVN2']]
                row_tags = []
                if not tr['child_taxes']:
                    row_tags = [t.name for t in tr['tax'].tag_ids if t.name not in ['PVN1-I', 'PVN1-II', 'PVN1-III', 'PVN2']]
                if not tr['refund']:
                    if 'PVN1-I' in sect_tags:
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
                    if 'PVN1-III' in sect_tags:
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
                        md['PVN2'].append(tr)
                        if not tr['child_taxes']:
                            if '45' in row_tags:
                                md['45'] += tr['base']
                            if '48.2' in row_tags:
                                md['48.2'] += tr['base']
                if tr['refund']:
                    if 'PVN1-I' in sect_tags:
                        md['PVN1-I'].append(tr)
                        if (not tr['child_taxes']) and '67' in row_tags:
                            md['67'] += tr['amount']
                    if 'PVN1-II' in sect_tags:
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
                    if 'PVN1-III' in sect_tags:
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
                        md['PVN2'].append(tr)
                        if not tr['child_taxes']:
                            if '45' in row_tags:
                                md['45'] -= tr['base']
                            if '48.2' in row_tags:
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
    def form_pvn1i_data(self, data, data_of_file):
        limit_val = 1430.0
        for d in data:
            if d['move'].date <= datetime.strftime(datetime.strptime('2013-12-31', '%Y-%m-%d'), '%Y-%m-%d'):
                limit_val = 1000.0
            partner = self.form_partner_data(d['partner'])
            deal_type = ""
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
            if '65' in row_tags:
                deal_type = "K"
            if '62' in row_tags and '52' in row_tags:
                deal_type = "R4"
                limit_val = 0.0
            # getting document types "A", "N" and "I":
            if d['base'] >= limit_val:
                data_of_file += "\n        <R>"
                if deal_type != "I" and partner['country']:
                    data_of_file += ("\n            <DpValsts>" + unicode(partner['country']) + "</DpValsts>")
                if partner['vat'] and deal_type not in ["I", "N"]:
                    data_of_file += ("\n            <DpNumurs>" + str(partner['vat']) + "</DpNumurs>")
                data_of_file += ("\n            <DpNosaukums>" + unicode(partner['name']) + "</DpNosaukums>")
                data_of_file += ("\n            <DarVeids>" + deal_type + "</DarVeids>")
                data_of_file += ("\n            <VertibaBezPvn>" + str(d['base']) + "</VertibaBezPvn>")
                if not d['child_taxes']:
                    tax_amount = d['amount']
                else:
                    for c in d['child_taxes']:
                        c_tags = [t.name for t in c['tax'].tag_ids]
                        if '62' in c_tags:
                            tax_amount = c['amount']
                data_of_file += ("\n            <PvnVertiba>" + str(tax_amount) + "</PvnVertiba>")
                data_of_file += ("\n        </R>")
        return data_of_file

    @api.model
    def form_pvn1ii_data(self, data, data_of_file):
        
        return data_of_file

    @api.model
    def form_pvn1iii_data(self, data, data_of_file):
        
        return data_of_file

    @api.model
    def form_pvn2_data(self, data, data_of_file):
        
        return data_of_file

    @api.multi
    def create_file(self):
        self.ensure_one()
        company = self.env['res.users'].browse(self.env.uid).company_id
        partner_obj = self.env['res.partner']
        move_obj = self.env['account.move']

        # defining file content:
        data_of_file = """<?xml version="1.0"?>
<DokPVNv4 xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <ParskGads>%(year)s</ParskGads>""" % ({'year': str(datetime.strptime(self.date_to, '%Y-%m-%d').year)})

        # getting info for period tags:
        start_date = datetime.strptime(self.date_from, '%Y-%m-%d')
        end_date = datetime.strptime(self.date_to, '%Y-%m-%d')
        diff_month = relativedelta(end_date, start_date).months
        if diff_month == 1:
            data_of_file += "\n    <ParskMen>" + str(int(start_date.month)) + "</ParskMen>"
        if diff_month in [3, 6]:
            fy_end_date = datetime(start_date.year, company.fiscalyear_last_month, company.fiscalyear_last_day)
            fy_start_date = fy_end_date - relativedelta(years=1) + relativedelta(days=1)
            diff_month_fy = relativedelta(start_date, fy_start_date).months
            if diff_month == 3:
                quarter = (diff_month_fy > 9 and 4) or (diff_month_fy > 6 and 3) or (diff_month_fy > 3 and 2) or 1
                data_of_file += "\n    <ParskCeturksnis>" + str(quarter) + "</ParskCeturksnis>"
            if diff_month == 6:
                half_year = (diff_month_fy > 6) and 2 or 1
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

        add_pvn = False
        for key, value in move_data.iteritems():
            if value != 0.0 and value != []:
                add_pvn = True

        if add_pvn == True:
            data_of_file += "\n    <PVN>"
            for row, amount in move_data.iteritems():
                if row not in ['PVN1-I', 'PVN1-II', 'PVN1-III', 'PVN2'] and amount != 0.0:
                    tag_name = row.replace('.','')
                    data_of_file += ("\n        <R%s>%s</R%s>" % (tag_name, amount, tag_name))
            data_of_file += "\n    </PVN>"
            for part, data in move_data.iteritems():
                if part in ['PVN1-I', 'PVN1-II', 'PVN1-III', 'PVN2']:
                    data_of_file += ("\n    <%s>" % (part))
                    if part == 'PVN1-I':
                        data_of_file = self.form_pvn1i_data(data, data_of_file)
                    if part == 'PVN1-II':
                        data_of_file = self.form_pvn1ii_data(data, data_of_file)
                    if part == 'PVN1-III':
                        data_of_file = self.form_pvn1iii_data(data, data_of_file)
                    if part == 'PVN2':
                        data_of_file = self.form_pvn2_data(data, data_of_file)
                    data_of_file += ("\n    </%s>" %(part))

        data_of_file += "\n</DokPVNv4>"

        data_of_file_real = base64.encodestring(data_of_file.encode('utf8'))

        self.write({
            'file_save': data_of_file_real,
            'name': self.name,
            'info_file_name': self.info_file_name,
#            'info_file_save': info_file_data_real
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