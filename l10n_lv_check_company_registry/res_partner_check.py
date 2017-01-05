# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012 ITS-1 (<http://www.its1.lv/>)
#                       E-mail: <info@its1.lv>
#                       Address: <Vienibas gatve 109 LV-1058 Riga Latvia>
#                       Phone: +371 66116534
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

import lursoft

from odoo import api, models, fields, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    registry_valid= fields.Boolean()

    #@api.onchange('load_from_registry')
    #def change_from_registry(self):
    #    registry = self.partner_registry or self.individual_registry
    #    data = None
    #    if registry and len(registry) == 11:
    #        data = lursoft.Luresoft().query(registry)
    #        self.name = data['name']
    #        self.partner_registry = data['regcode']
    #        #self.phone = data['phone']
    #        #c_type = dom.getElementsByTagName('companytype')
    #        self.street = data['address']['street'] + ' ' + data['address']['house'] 
    #        self.city = data['address']['city']
    #        self.zip = data['address']['index']
    #        self.vat = data['pvncode']
    #    return {'data': data}

    def check_registry(self, code):
        return self.check_luresoft(code)

    def get_luresoft(self, code):
        self.request = lursoft.Luresoft().query(code)

    def check_luresoft(self, code):
        self.get_luresoft(code)
        luresoft_data = self.request
        data = {
            'partner_registry': luresoft_data['regcode'],
            'name': luresoft_data['name'],
            'vat': luresoft_data['pvncode'],
            'city': luresoft_data['address']['city'],
            'zip': luresoft_data['address']['index'],
            'street': u'{street} {housenr}{housepart}'.format(
                street=luresoft_data['address']['street'],
                housenr=luresoft_data['address']['house'],
                housepart=luresoft_data['address'].get('housepart', ''))
            }

        title = self.env['res.partner.title'].search(
            [('shortcut', '=', luresoft_data['type'])], limit=1)
        if title:
            data['title'] = title.id

        return data


## vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
