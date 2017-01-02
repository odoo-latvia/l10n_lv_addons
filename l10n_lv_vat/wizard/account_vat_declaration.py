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
        ml_obj = self.env['account.move.line']
        for m in moves:
            invoices = list(set([ml.invoice_id for ml in m.line_ids]))
            inv_type = invoices and invoices[0].type or False
            j_type = m.journal_id.type
            tax_amt_data = []
            for line in m.line_ids:
                if line.tax_ids:
                    for tax in line.tax_ids:
                        t_tags = [t.name for t in tax.tag_ids]
                        if tax.amount_type == 'group':
                            for ctax in tax.children_tax_ids:
                                tax_mls = ml_obj.search([('move_id','=',m.id), ('tax_line_id','=',ctax.id)])
                                tax_amount = 0.0
                                for tm in tax_mls:
                                    tax_amount += (tm.debit or tm.credit)
                                tax_amt_data.append({
                                    'tax': ctax,
                                    'parent_tax': tax,
                                    'base': line.debit or line.credit,
                                    'amount': tax_amount
                                })
                        else:
                            tax_mls = ml_obj.search([('move_id','=',m.id), ('tax_line_id','=',tax.id)])
                            tax_amount = 0.0
                            for tm in tax_mls:
                                tax_amount += (tm.debit or tm.credit)
                            tax_amt_data.append({
                                'tax': tax,
                                'base': line.debit or line.credit,
                                'amount': tax_amount
                            })
        return md

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
        diff_month = relativedelta.relativedelta(end_date, start_date).months
        if diff_month == 1:
            data_of_file += "\n    <ParskMen>" + str(int(start_date.month)) + "</ParskMen>"
        if diff_month in [3, 6]:
            fy_end_date = datetime(start_date.year, company.fiscalyear_last_month, company.fiscalyear_last_day)
            fy_start_date = fy_end_date - relativedelta(years=1) + relativedelta(days=1)
            diff_month_fy = relativedelta.relativedelta(start_date, fy_start_date).months
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
                raise osv.except_osv(_('Insufficient data!'), _('No TIN or Company Registry number associated with your company.'))

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
        return {}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: