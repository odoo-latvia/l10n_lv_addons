# -*- encoding: utf-8 -*-
##############################################################################
#
#    Part of Odoo.
#    Copyright (C) 2018 Allegro (<http://www.allegro.lv/>)
#                       E-mail: <info@allegro.lv>
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


    def create_fullname(self, data):
        """ Construct a partner's fullname from a dict or recordset"""
        parts = []
        for field in ['firstname', 'surname']:
            try:
                if data[field]:
                    parts.append(data[field])
            except KeyError:
                pass

        return ' '.join(parts)


    def create_firstlast_names(self, data):
        """ Construct firstname and surname from a dict or recordset with a name"""
        try:
            name = (data['name'] or '').strip()
        except KeyError:
            return None, None

        try:
            name = name.decode()
        except AttributeError:
            pass

        parts = name.rsplit(' ', 1)

        if len(parts) == 2:
            return tuple(parts)
        else:
            return parts[0], None


    @api.onchange('firstname', 'surname', 'is_company')
    def change_first_last_name(self):
        if (not self.is_company) and (self.firstname or self.surname):
            self.name = self.create_fullname(self)


    @api.onchange('name', 'is_company')
    def change_name(self):
        if self.is_company:
            self.firstname, self.surname = None, None
        else:
            self.firstname, self.surname = self.create_firstlast_names(self)

    @api.model
    def create(self, values):
        if not values.get('is_company'):
            if values.get('name'):
                fname, sname = self.create_firstlast_names(values)
                values.update(firstname=fname, surname=sname)
            else:
                values.update(name=self.create_fullname(values))
        return super(Partner, self).create(values)

    def write(self, values):
        if values.get('name'):
            fname, sname = self.create_firstlast_names(values)
            values.update(firstname=fname, surname=sname)
        for partner in self:
            if not values.get('name') and not partner.name:
                partner_values = values.copy()
                name = self.create_fullname(partner_values)
                partner_values.update(name=name)
                super(Partner, partner).write(partner_values)
            else:
                super(Partner, partner).write(values)
        return True

    @api.model
    def generate_names(self):
        nonames = self.search([('is_company','=',False), '|', ('firstname','=',False), ('surname','=',False)])
        for nn in nonames:
            fname, sname = self.create_firstlast_names(nn)
            nn_vals = {}
            if (not nn.firstname) and fname:
                nn_vals.update({'firstname': fname})
            if (not nn.surname) and sname:
                nn_vals.update({'surname': sname})
            if nn_vals:
                nn.write(nn_vals)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
