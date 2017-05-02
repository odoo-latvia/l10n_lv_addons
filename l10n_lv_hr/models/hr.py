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

    employee_name = fields.Char(string='Name')
    employee_surname = fields.Char(string='Surname')

    @api.onchange('employee_name', 'employee_surname')
    def _onchange_employee_name(self):
        if self.employee_name and self.employee_surname:
            self.name = self.employee_name + ' ' + self.employee_surname
        if self.employee_name and not self.employee_surname:
            self.name = self.employee_name
        if self.employee_surname and not self.employee_name:
            self.name = self.employee_surname
        if not self.employee_name and not self.employee_surname:
            self.name = False

    @api.onchange('name')
    def _onchange_name(self):
        if self.name:
            name_list = self.name.strip().split(' ')
            if len(name_list) > 1:
                surname = name_list[-1]
                name = ' '.join(name_list[:-1])
            else:
                name = name_list and name_list[0] or ''
                surname = ''
            self.employee_name = name
            self.employee_surname = surname
        if not self.name:
            self.employee_name = False
            self.employee_surname = False

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: