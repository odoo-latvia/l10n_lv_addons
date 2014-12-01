# -*- encoding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (c) 2008-2012 Alistek Ltd. (http://www.alistek.com)
#                       All Rights Reserved.
#                       General contacts <info@alistek.com>
#    Copyright (C) 2014 ITS-1 (<http://www.its1.lv/>)
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

class stock_move(osv.osv):
    _name = 'stock.move'
    _inherit = 'stock.move'

    _columns = {
        'cmr_line_weight': fields.float('Pack Gross Weight (kg)  in CMR', digits=(16,3), help='This is for Natural Resources Tax only:  \nenter here a gross weight of goods package  (kgs).'),
        'cmr_package_drn_categ': fields.many2one('product.category.drn', 'NRT Transport Package Type', ondelete='set null', help='This is for Natural Resources Tax only:  \nenter here a gross weight of goods package as stated in CMR.'),
        'add_drn_package_weight': fields.float('Pallets and similar, included in shipment (kg)', digits=(16,3), help='This is for Natural Resources Tax only:  \nenter here net weight of transportation package (kgs). (20-25kgs, for standard EURO pallet).\nTransportation package can be pallets, wooden boxes, polyethylene etc.'),
        'add_drn_package_cat': fields.many2one('product.category.drn', 'Transportation Package Type for pallets and similar', ondelete='set null', help='This is for Natural Resources Tax only:  \nenter here type of transportation package if stated in CMR. \nTransportation package can be pallets, wooden boxes, polyethylene etc.'),
    }

    _defaults = {
        'add_drn_package_weight': 0.0,
        'cmr_line_weight': 0.0,
    }

    def _check_add_drn_package(self, cr, uid, ids):
        for r in self.browse(cr, uid, ids, {}):
            if r.add_drn_package_cat and r.add_drn_package_cat.code!='NO' \
                     and r.add_drn_package_weight<=0:
                return False
            elif not r.add_drn_package_cat and r.add_drn_package_weight>0:
                return False
        return True

    _constraints = [
        (_check_add_drn_package, _('Transportation Package value for pallets and similar cannot be less or equal than zero!'), ['']),
    ]

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: