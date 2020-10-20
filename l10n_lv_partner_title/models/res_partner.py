# -*- encoding: utf-8 -*-
##############################################################################
#
#    Part of Odoo.
#    Copyright (C) 2018 Allegro IT (<http://www.allegro.lv/>)
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
    _inherit = 'res.partner'

    title = fields.Many2one(domain="['|', ('company_type', '=', company_type), ('company_type', '=', False)]")


class PartnerTitle(models.Model):
    _inherit = 'res.partner.title'
    _rec_name = 'shortcut'

    company_type = fields.Selection([
        ('person', 'Individual'),
        ('company', 'Company'),
        ], 'Type')
 

    def name_get(self, details=True):
        if details:
            name = u'{r.shortcut} {r.name}'
        else:
            name = u'{r.shortcut}'
        names = []
        for rec in self:
            names.append((rec.id, name.format(r=rec) or r.name))
        return names

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        if args == None:
            args = []
        if operator == 'ilike':
            args += [
                '|',
                ('shortcut', 'ilike', name),
                ('name', 'ilike', name),
            ]
        return self.search(args, limit=limit).name_get(details=True)


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
