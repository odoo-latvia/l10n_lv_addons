# -*- encoding: utf-8 -*-
##############################################################################
#
#    Part of Odoo.
#    Copyright (C) 2019 Allegro IT (<http://www.its1.lv/>)
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

class BusinessTripRate(models.Model):
    _inherit = 'hr.bt.rate'

    @api.model
    def update_currencies(self):
        cur_list = ['EUR', 'USD', 'AUD', 'DKK', 'GBP', 'CAD', 'CHF', 'NOK']
        datas = self.env['ir.model.data'].sudo().search([
            ('name','in',cur_list),
            ('module','=','base'),
            ('model','=','res.currency')
        ])
        c_ids = []
        for d in datas:
            if d.res_id and d.res_id not in c_ids:
                c_ids.append(d.res_id)
        currencies = self.env['res.currency'].sudo().search([
            ('id','in',c_ids),
            ('active','=',False)
        ])
        if currencies:
            currencies.toggle_active()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: