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

    def form_fidavista_data(self, active_ids):
        return False

    def form_iso20022_data(self, active_ids):
        return False

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: