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

            if old.firstname != self.firstname:
                self.name = u' '.join(filter(None, [self.firstname, self.surname]))

            if old.surname != self.surname:
                if ' ' in self.surname.strip():
                    self.surname = self.surname.strip().replace(' ', '-')
                self.name = u' '.join(filter(None, [self.firstname, self.surname]))

    @api.onchange('name')
    def change_name(self):
        if self.is_company:
            self.firstname, self.surname = ('', '')
        else:
            parts = (self.name or '').strip().rsplit(' ', 1)
            if len(parts) == 2:
                self.firstname, self.surname = parts
            else:
                self.firstname = parts[0]
                self.surname = ''

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
        changed = self.new({}).server_change_name(values)
        values.update(changed)
        return super(Partner, self).write(values)


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
