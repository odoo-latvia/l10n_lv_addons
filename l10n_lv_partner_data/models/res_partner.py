# -*- encoding: utf-8 -*-
##############################################################################
#
#    Part of Odoo.
#    Copyright (C) 2021 Ozols Grupa (<http://www.ozols.lv/>)
#                       E-mail: <info@ozols.lv>
#                       Address: <Vienibas gatve 109 LV-1058 Riga Latvia>
#                       Phone: +371 67289211
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import api, fields, models, _

class Partner(models.Model):
    _inherit = "res.partner"

    partner_registry = fields.Char(string='Registration No.', index=True)
    individual_registry = fields.Char(string='Personal No.')
    code = fields.Char(string='Code')

    @api.onchange('individual_registry')
    def _change_individual_registry(self):
        if self.company_type == 'individual':
            self.partner_registry = self.individual_registry


class Company(models.Model):
    _inherit = "res.company"

    company_registry = fields.Char(string='Registration No.')

    @api.model
    def create(self, vals):
        company = super(Company, self).create(vals)
        if 'company_registry' in vals and company.partner_id:
            company.partner_id.write({
                'partner_registry': vals['company_registry']
            })
        return company

    @api.model
    def write(self, values):
        res = super(Company, self).write(values)
        if 'company_registry' in values:
            for company in self:
                if company.partner_id:
                    company.partner_id.write({
                        'partner_registry': values['company_registry']
                    })
        return res


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
