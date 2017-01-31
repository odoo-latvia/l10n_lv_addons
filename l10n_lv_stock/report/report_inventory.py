# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2016 ITS-1 (<http://www.its1.lv/>)
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

import time
from openerp.report import report_sxw
from openerp.osv import osv

class report_stock_inventory(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(report_stock_inventory, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'cr':cr,
            'uid': uid,
            'get_numbers': self.get_numbers,
            'get_warehouse': self.get_warehouse,
            'get_cost': self.get_cost,
            'get_totals': self.get_totals
        })
        self.context = context

    def get_numbers(self, lines):
        data = {}
        n = 0
        for l in lines:
            n += 1
            data.update({l.id: n})
        return data

    def get_warehouse(self, location):
        wh_id = self.pool.get('stock.location').get_warehouse(self.cr, self.uid, location, context=self.context)
        wh_name = ''
        if wh_id:
            wh = self.pool.get('stock.warehouse').browse(self.cr, self.uid, wh_id, context=self.context)
            wh_name = wh.name
        return wh_name

    def get_cost(self, line):
        cost = line.product_id.standard_price
        inv_line_obj = self.pool.get('stock.inventory.line')
        quant_ids = inv_line_obj._get_quants(self.cr, self.uid, line, context=self.context)
        if quant_ids and line.theoretical_qty >= 0.0:
            quant_obj = self.pool.get('stock.quant')
            uom_obj = self.pool.get('product.uom')
            total_cost = 0.0
            total_qty = 0.0
            for quant in quant_obj.browse(self.cr, self.uid, quant_ids, context=self.context):
                total_cost += (quant.cost * quant.qty)
                total_qty += quant.qty
            if line.product_uom_id and line.product_id.uom_id.id != line.product_uom_id.id:
                total_qty = uom_obj._compute_qty_obj(self.cr, self.uid, line.product_id.uom_id, total_qty, line.product_uom_id, context=self.context)
            if total_qty < line.product_qty:
                diff = line.product_qty - total_qty
                total_qty += diff
                total_cost += (line.product_id.standard_price * diff)
            cost = total_qty != 0.0 and total_cost / total_qty or 0.0
        f1 = open('/home/santa/log.txt', 'a')
        f1.write((str(line.id) + ',' + str(cost) + '\n'))
        f1.close()
        return cost

    def get_totals(self, lines):
        qty = 0.0
        value = 0.0
        for l in lines:
            qty += l.product_qty
            cost = self.get_cost(l)
            value += (cost * l.product_qty)
        return {'quantity': qty, 'value': value}

class report_inventory(osv.AbstractModel):
    _name = 'report.stock.report_inventory'
    _inherit = 'report.abstract_report'
    _template = 'stock.report_inventory'
    _wrapped_report_class = report_stock_inventory

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: