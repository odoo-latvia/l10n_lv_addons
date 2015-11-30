# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 ITS-1 (<http://www.its1.lv/>)
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

from openerp.osv import osv, fields
from openerp import SUPERUSER_ID
from openerp.tools.translate import _
from datetime import datetime
import openerp.addons.decimal_precision as dp

class stock_production_lot(osv.osv):
    _inherit = 'stock.production.lot'

    def _lot_available(self, cr, uid, ids, field_names=None, arg=False, context=None):
        context = context or {}
        field_names = field_names or []
        product_obj = self.pool.get('product.product')
        res = {}
        for lot in self.browse(cr, uid, ids, context=context):
            ctx = context.copy()
            ctx.update({'lot_id': lot.id})
            location = False
            if 'location_id' in context:
                location = context['location_id']
            if (not location) and 'default_sourceloc_id' in context:
                location = context['default_sourceloc_id']
            if location:
                ctx.update({'location': location})
            qty_data = product_obj._product_available(cr, uid, [lot.product_id.id], context=ctx)
            qty = qty_data[lot.product_id.id]['qty_available']
            res[lot.id] = qty
        return res

    _columns = {
        'qty_available': fields.function(_lot_available, type='float', digits_compute=dp.get_precision('Product Unit of Measure'), string='Quantity On Hand')
    }

    def name_get(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        if not isinstance(ids, list):
            ids = [ids]
        res = []
        if not ids:
            return res
        product_obj = self.pool.get('product.product')
        for record in self.browse(cr, uid, ids, context=context):
            name = record.name
            if 'default_sourceloc_id' in context or 'location_id' in context:
                location = False
                if 'location_id' in context:
                    location = context['location_id']
                if (not location) and 'default_sourceloc_id' in context:
                    location = context['default_sourceloc_id']
                ctx = context.copy()
                ctx.update({'lot_id': record.id})
                if location:
                    ctx.update({'location': location})
                qty_data = product_obj._product_available(cr, uid, [record.product_id.id], context=ctx)
                qty = qty_data[record.product_id.id]['qty_available']
                name += (' (' + str(qty) + ')')
            res.append((record.id, name))
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: