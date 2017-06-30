# -*- encoding: utf-8 -*-
##############################################################################
#
#    Part of Odoo.
#    Copyright (C) 2017 ITS-1 (<http://www.its1.lv/>)
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


class Employee(models.Model):
    _inherit = "hr.employee"

    firstname = fields.Char(compute='compute_firstname',
                            inverse='inverse_name_part',
                            store=True)
    surname = fields.Char(compute='compute_surname',
                          inverse='inverse_name_part',
                          store=True)

    # computed functions are computed only after the record is created.
    # Therefore we compute fullname before the records creation
    @api.model
    def create(self, values):

        fullname = []

        try:
            fullname.append(values.pop('firstname'))
        except KeyError:
            pass

        try:
            fullname.append(values.pop('surname'))
        except KeyError:
            pass

        if not values.get('name'):
            values.update(name=' '.join(fullname))

        return super(Employee, self).create(values)

    # if name is explicitly written drop firstname and lastname
    # not to trigger inveser of fistname, surname
    @api.multi
    def write(self, values):

        if values.get('name'):

            try:
                values.pop('firstname')
            except KeyError:
                pass

            try:
                values.pop('surname')
            except KeyError:
                pass

        return super(Employee, self).write(values)

    @api.depends('name')
    def compute_firstname(self):
        self.firstname = (self.name or '').strip().rsplit(' ', 1)[0]

    @api.depends('name')
    def compute_surname(self):
        name = (self.name or '').strip().rsplit(' ', 1)
        if len(name) > 1:
            self.surname = name[1]

    @api.model
    def inverse_name_part(self):
        self.name = self.get_full_name()

    @api.model
    def get_full_name(self):
        return u'{firstname} {surname}'.format(
                firstname=getattr(self, 'firstname', '') or '',
                surname=getattr(self, 'surname', '') or '',
                ).strip()

    @api.onchange('firstname')
    def change_firstname(self):
        self.name = self.get_full_name()

    @api.onchange('surname')
    def change_surname(self):
        if ' ' in (self.surname or '').strip():
            self.surname = self.surname.strip().replace(' ', '-')
        self.name = self.get_full_name()

    @api.onchange('name')
    def change_name(self):
        parts = (self.name or '').strip().rsplit(' ', 1)
        if len(parts) == 2:
            self.firstname, self.surname = parts
        else:
            self.firstname = parts[0]
            self.surname = ''


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
