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

class product_category_drn(osv.osv):
    '''Product Category'''
    _name = 'product.category.drn'
    _description = "Product Category"

    _columns = {
        'code': fields.char('Category Code', size=64),
        'name': fields.char('Category Name', size=128, required=True),
        'parent_id': fields.many2one('product.category.drn', 'Parent Category', ondelete='set null'),
        'type': fields.char('Category Type', size=64),
        'cn_group': fields.char('CN group Code', size=8),
    }

class product_category(osv.osv):
    _name = 'product.category'
    _inherit = 'product.category'

    _columns = {
        'drn_product_category': fields.many2one('product.category.drn', 'Natural Resources Tax Category', ondelete='set null'),
        'drn_product_pack_category': fields.many2one('product.category.drn', 'Packaging Natural Resources Tax Category', ondelete='set null'),
        'is_eei': fields.boolean('Is EEI subject?'),
    }

class product_template(osv.osv):
    _name = 'product.template'
    _inherit = 'product.template'

    _columns = {
        'lubri_weight': fields.float('Lubricanting Oils', digits=(16,3), help='This is for Natural Resources Tax only:  \nenter here weight (kgs) of hazardous unit included in product.'),
        'accu_lead_weight': fields.float('Lead-containing electric accumulators', digits=(16,3), help='This is for Natural Resources Tax only:  \nenter here weight (kgs) of hazardous unit included in product.'),
        'accu_nicd_weight': fields.float('Electric accumulators, Ni-Cd un Fe-Ni', digits=(16,3), help='This is for Natural Resources Tax only:  \nenter here weight (kgs) of hazardous unit included in product.'),
        'accu_pri_weight': fields.float('Primary cells and primary batteries', digits=(16,3), help='This is for Natural Resources Tax only:  \nenter here weight (kgs) of hazardous unit included in product.'),
        'accu_oth_weight': fields.float('Other electric accumulators', digits=(16,3), help='This is for Natural Resources Tax only:  \nenter here weight (kgs) of hazardous unit included in product.'),
        'tires_weight': fields.float('All types of tires', digits=(16,3), help='This is for Natural Resources Tax only:  \nenter here weight (kgs) of hazardous unit included in product.'),
        'oil_filt_weight': fields.float('Oil Filters', digits=(16,3), help='This is for Natural Resources Tax only:  \nenter here weight (kgs) of hazardous unit included in product.'),
        'drn_prod_categ_id': fields.many2one('product.category.drn', 'EEI Category for NRT', ondelete='set null', help='This is for Natural Resources Tax only:  \nenter here weight (kgs) of hazardous unit included in product.'),
        'drn_prod_pack_categ_id': fields.many2one('product.category.drn', 'Primary Package Category for NRT', ondelete='set null', help='This is for Natural Resources Tax only:  \nenter here weight (kgs) of hazardous unit included in product.'),
        'is_eei': fields.boolean('Is EEI subject?'),
    }

class product_packaging(osv.osv):
    _name = 'product.packaging'
    _inherit = 'product.packaging'

    _columns = {
        'drn_cat_id': fields.many2one('product.category.drn', 'Natural Resources Tax Category', ondelete='set null')
    }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: