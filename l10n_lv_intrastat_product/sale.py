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

from openerp.osv import osv, orm, fields
from openerp.tools.translate import _

class sale_order(orm.Model):
    _inherit = "sale.order"

    def _prepare_invoice(self, cr, uid, order, lines, context=None):
        invoice_vals = super(sale_order, self)._prepare_invoice(
            cr, uid, order, lines, context=context)
        if order.partner_shipping_id and order.partner_shipping_id.country_id:
            invoice_vals['intrastat_country_id'] = \
                order.partner_shipping_id.country_id.id
        if order.picking_ids and len(order.picking_ids) == 1:
            invoice_vals['intrastat_transport'] = \
                order.picking_ids[0].intrastat_transport
            invoice_vals['intrastat_type_id'] = \
                order.picking_ids[0].intrastat_type_id and order.picking_ids[0].intrastat_type_id.id or False
        return invoice_vals

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: