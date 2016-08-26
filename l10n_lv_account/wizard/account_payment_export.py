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

class AccountPaymentExport(models.TransientModel):
    _name = 'account.payment.export'

    format = fields.Selection([('ofx','.OFX'), ('fidavista','FiDAViSta'), ('iso20022', 'ISO 20022')], string='Format', required=True)
    name = fields.Char('File Name', default='export.xml')
    data_file = fields.Binary(string='Save File')

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
        data_of_file = """<?xml version="1.0" encoding="UTF-8" ?>
<FIDAVISTA xmlns="http://bankasoc.lv/fidavista/fidavista0101.xsd">"""
        data_of_file += "\n    <Header>"
        data_of_file += ("\n        <Timestamp>" + datetime.now().strftime('%Y%m%d%H%M%S%f')[:-3] + "</Timestamp>")
        company = self._get_company(active_ids)
        data_of_file += ("\n        <From>" + format_string(company.name) + "</From>")
        data_of_file += "\n    </Header>"
        for payment in self.env['account.payment'].browse(active_ids):
            data_of_file += "\n    <Payment>"
            payment_name = len(payment.name) > 10 and payment.name[-10:] or payment.name
            data_of_file += ("\n        <DocNo>" + payment_name + "</DocNo>")
            payment_date = len(payment.payment_date) > 10 and payment.payment_date[0:10] or payment.payment_date
            data_of_file += ("\n        <RegDate>" + payment_date + "</RegDate>")
            if payment.communication:
                payment_communication = len(payment.communication) > 140 and payment.communication[0:140] or payment.communication
                data_of_file += ("\n        <PmtInfo>" + payment_communication + "</PmtInfo>")
        return False

    def form_iso20022_data(self, active_ids):
        return False

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: