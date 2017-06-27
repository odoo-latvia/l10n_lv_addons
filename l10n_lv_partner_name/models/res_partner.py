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


    @api.onchange('firstname')
    def change_firstname(self):
        if not self.is_company:
            self.name = u'{r.firstname} {r.surname}'.format(r=self).strip()

    @api.onchange('surname')
    def change_surname(self):
        if not self.is_company:
            if ' ' in self.surname.strip():
                self.surname = self.surname.strip().replace(' ', '-')
            self.name = u'{r.firstname} {r.surname}'.format(r=self).strip()

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


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
