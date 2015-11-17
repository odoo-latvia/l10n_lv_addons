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

from openerp import models, fields, api
from openerp.tools.translate import _
import xml.etree.ElementTree as ET

class stock_transfer_details(models.TransientModel):
    _inherit = 'stock.transfer_details'

    def default_get(self, cr, uid, fields, context=None):
        if context is None: context = {}
        res = super(stock_transfer_details, self).default_get(cr, uid, fields, context=context)
        if 'item_ids' in res:
            product_obj = self.pool.get('product.product')
            for ind, item in enumerate(res['item_ids']):
                if item.get('product_id',False) and item.get('lot_id',False):
                    ctx = context.copy()
                    ctx.update({'lot_id': item['lot_id']})
                    if item.get('sourceloc_id',False):
                        ctx.update({'location': item['sourceloc_id']})
                    qty_data = product_obj._product_available(cr, uid, [item['product_id']], context=ctx)
                    qty = qty_data[item['product_id']]['qty_available']
                    if qty <= 0.0:
                        res['item_ids'][ind]['lot_id'] = False
        return res

class stock_transfer_details_items(models.TransientModel):
    _inherit = 'stock.transfer_details_items'

    @api.multi
    def product_id_change(self, product, uom=False):
        res = super(stock_transfer_details_items, self).product_id_change(product, uom=uom)
        if product:
            ctx = dict(self._context)
            sourceloc_id = ctx.get('sourceloc_id',False)
            lot_obj = self.pool.get('stock.production.lot')
            product_obj = self.pool.get('product.product')
            lot_ids = lot_obj.search(self._cr, self._uid, [('product_id','=',product)], context=ctx)
            lot_list = []
            for lot in lot_ids:
                ctx2 = ctx.copy()
                ctx2.update({'lot_id': lot})
                if sourceloc_id:
                    ctx2.update({'location': sourceloc_id})
                qty_data = product_obj._product_available(self._cr, self._uid, [product], context=ctx2)
                qty = qty_data[product]['qty_available']
                if qty > 0.0:
                    lot_list.append(lot)
            res['domain']['lot_id'] = [('id','in',lot_list)]
            res['value']['lot_id'] = False
            if len(lot_list) == 1:
                res['value']['lot_id'] = lot_list[0]
        return res

    @api.multi
    def sourceloc_id_change(self, sourceloc):
        res = {'value': {}, 'domain': {}}
        ctx = dict(self._context)
        product_id = ctx.get('product_id',False)
        if product_id:
            lot_obj = self.pool.get('stock.production.lot')
            product_obj = self.pool.get('product.product')
            lot_ids = lot_obj.search(self._cr, self._uid, [('product_id','=',product_id)], context=ctx)
            lot_list = []
            for lot in lot_ids:
                ctx2 = ctx.copy()
                ctx2.update({'lot_id': lot})
                if sourceloc:
                    ctx2.update({'location': sourceloc})
                qty_data = product_obj._product_available(self._cr, self._uid, [product], context=ctx2)
                qty = qty_data[product]['qty_available']
                if qty > 0.0:
                    lot_list.append(lot)
            res['domain']['lot_id'] = [('id','in',lot_list)]
            res['value']['lot_id'] = False
            if len(lot_list) == 1:
                res['value']['lot_id'] = lot_list[0]
        return res

    def fields_get(self, cr, uid, allfields=[], context=None):
        res = super(stock_transfer_details_items, self).fields_get(cr, uid, allfields=allfields, context=context)
        print '--------------------------'
        print res
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: