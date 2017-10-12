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

class Partner(models.Model):
    _inherit = "res.partner"

    firstname = fields.Char()
    surname = fields.Char()


    @api.onchange('firstname', 'surname')
    def change_first_last_name(self):
        if not self.is_company:

            old = self.browse(self.id)

            name = ''
            if self.firstname:
                name += self.firstname
            if self.surname:
                if name:
                    name += ' '
                name += self.surname

            self.name = name or None


    @api.onchange('name')
    def change_name(self):
        if self.is_company:
            self.firstname, self.surname = (None, None)

        elif not self.env.context.get('change_name'):
            parts = (self.name or '').strip().rsplit(' ', 1)
            if len(parts) == 2:
                self.firstname, self.surname = parts
            else:
                if self.firstname == self.name or self.surname == self.name:
                    pass
                else:
                    self.firstname = parts[0] or None
                    self.surname = None

    @api.model
    def server_change_name(self, values):
        changes = []
        change_values = values.copy()

        if 'name' in values:
            changes.append('name')
        else:
            if 'firstname' in values:
                changes.append('firstname')
            elif 'surname' in values:
                changes.append('surname')

        for field in ['name', 'firstname', 'surname']:
            if field not in values:
                change_values.update({field: getattr(self, field)})

        if changes:
            updates = self.onchange(
                    change_values,
                    changes,
                    self._onchange_spec())

            return updates.get('value', {})

        else:
            return {}

    @api.model
    def create(self, values):
        changed = self.new({}).server_change_name(values)
        values.update(changed)
        return super(Partner, self).create(values)

    @api.multi
    def write(self, values):
        for partner in self:
            partner_vals = values.copy()
            changed = partner.server_change_name(values)
            partner_vals.update(changed)
            super(Partner, partner).write(values)
        return True

    @api.multi
    def generate_names(self):
        for r in self:
            if r.name:
                r.write({'name': r.name})

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
