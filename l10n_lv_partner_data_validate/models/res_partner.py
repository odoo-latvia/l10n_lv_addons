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

from odoo.addons.l10n_lv_partner_data_validate import pk

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class Partner(models.Model):
    _inherit = ['res.partner']

    country_code = fields.Char(related='country_id.code', readonly=True)

    @api.one
    @api.constrains('partner_registry', 'individual_registry', 'country_id')
    def _check_registry(self):
        if self.country_id.code == 'LV':
            registry = self.partner_registry or self.individual_registry
            if registry and not pk.validate(registry):
                raise ValidationError(_('Invalid registry number'))

    # TODO: provide proper server side validation
    @api.model
    def frontend_check(self, value):
        return pk.validate(value)


#class Company(models.Model):
#    _inherit = "res.company"
#
#    @api.model
#    def fields_get(self, allfields=None, attributes=None):
#        res = super(Company, self).fields_get(allfields=allfields, attributes=attributes)
#        if 'company_registry' in res and 'string' in res['company_registry']:
#            res['company_registry']['string'] = _('Registration No.')
#        return res
#
#    @api.model
#    def create(self, vals):
#        company = super(Company, self).create(vals)
#        if 'company_registry' in vals and company.partner_id:
#            company.partner_id.write({
#                'partner_registry': vals['company_registry']
#            })
#        return company
#
#    @api.multi
#    def write(self, values):
#        res = super(Company, self).write(values)
#        if 'company_registry' in values:
#            for company in self:
#                if company.partner_id:
#                    company.partner_id.write({
#                        'partner_registry': values['company_registry']
#                    })
#        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
