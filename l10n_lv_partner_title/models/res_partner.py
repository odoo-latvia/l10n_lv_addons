# -*- encoding: utf-8 -*-
##############################################################################
#
#    Part of Odoo.
#    Copyright (C) 2021 Allegro IT (<http://www.allegro.lv/>)
#                       E-mail: <info@allegro.lv>
#                       Address: <Vienibas gatve 109 LV-1058 Riga Latvia>
#                       Phone: +371 67289467
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
from xml.dom.minidom import parseString

class Partner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(Partner, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        dom = parseString(res['arch'])
        if view_type != 'search':
            xml_fields = dom.getElementsByTagName('field')
            ct_found = False
            t_field_tag = False
            for f in xml_fields:
                if f.getAttribute('name') == 'company_type':
                    ct_found = True
                if f.getAttribute('name') == 'title':
                    t_field_tag = f
            if t_field_tag and (not t_field_tag.getAttribute('domain')):
                t_field_tag.setAttribute("domain", "['|', ('type', '=', company_type), ('type', '=', False)]")
                if (not ct_found):
                    ct_field_tag = dom.createElement("field")
                    ct_field_tag.setAttribute("name", "company_type")
                    ct_field_tag.setAttribute("invisible", "1")
                    t_field_parent = t_field_tag.parentNode
                    t_field_parent.insertBefore(ct_field_tag, t_field_tag)
        res['arch'] = dom.toxml()
        return res


class PartnerTitle(models.Model):
    _inherit = 'res.partner.title'
    _rec_name = 'shortcut'

    type = fields.Selection([
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
