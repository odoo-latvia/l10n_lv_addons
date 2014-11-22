# -*- encoding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2010-2011 Akretion (http://www.akretion.com). All Rights Reserved
#    @author Alexis de Lattre <alexis.delattre@akretion.com>
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

class report_intrastat_code(osv.osv):
    _inherit = "report.intrastat.code"

    _columns = {
        'name': fields.char(
            'C.N. code', size=16, required=True,
            help="Full lenght C.N. code"), # re-defined
        'description': fields.char(
            'Description', size=255,
            help='Short text description of the C.N. category'), # re-defined
        'intrastat_code': fields.char(
            'Intrastat code', size=9, required=True,
            help="C.N. code. Must be part "
            "of the 'Nomenclature combinée' (NC) with 8 digits with "
            "sometimes a 9th digit for the "
            "'Nomenclature Générale des Produits' (NGP)."),
        'intrastat_uom_id': fields.many2one(
            'product.uom', 'UoM for intrastat product report',
            help="Select the unit of measure if one is required for "
            "this particular intrastat code (other than the weight in Kg). "
            "If no particular unit of measure is required, leave empty."),
    }

    def name_get(self, cr, uid, ids, context=None):
        res = []
        for code in self.read(
                cr, uid, ids, ['name', 'description'], context=context):
            display_name = code['name']
            if code['description']:
                display_name = '%s %s' % (display_name, code['description'])
            res.append((code['id'], display_name))
        return res

    def _intrastat_code(self, cr, uid, ids):
        for intrastat_code_to_check in self.read(
                cr, uid, ids, ['intrastat_code']):
            if intrastat_code_to_check['intrastat_code']:
                if (not intrastat_code_to_check['intrastat_code'].isdigit()
                        or len(intrastat_code_to_check['intrastat_code'])
                        not in (8, 9)):
                    return False
        return True

    def _hs_code(self, cr, uid, ids):
        for code_to_check in self.read(cr, uid, ids, ['name']):
            if code_to_check['name']:
                if not code_to_check['name'].isdigit():
                    return False
        return True

    _constraints = [
        (
            _intrastat_code,
            "The 'Intrastat code for DEB' should have exactly 8 or 9 digits.",
            ['intrastat_code']
        ),
        (
            _hs_code,
            "'Intrastat code' should only contain digits.",
            ['name']
        ),
    ]

class product_uom(orm.Model):
    _inherit = "product.uom"

    _columns = {
        'intrastat_label': fields.char(
            'Intrastat label', size=12,
            help="Label used in the XML file export of the Intrastat "
            "product report for this unit of measure.")
        }

class product_template(orm.Model):
    _inherit = "product.template"

    _columns = {
        'exclude_from_intrastat': fields.boolean(
            'Exclude from Intrastat reports',
            help="If set to True, the product or service will not be "
            "taken into account for Intrastat Product or Service reports. "
            "So you should leave this field to False unless you have a "
            "very good reason."), # intrastat_base
        'is_accessory_cost': fields.boolean(
            'Is accessory cost',
            help="Activate this option for shipping costs, packaging "
            "costs and all services related to the sale of products. "
            "This option is used for Intrastat reports."), # intrastat_base
        'country_id': fields.many2one(
            'res.country', 'Country of origin',
            help="Country of origin of the product i.e. product "
            "'made in ____'. If you have different countries of origin "
            "depending on the supplier from which you purchased the product, "
            "leave this field empty and use the equivalent field on the "
            "'product supplier info' form."),
    }

    _defaults = {
        'exclude_from_intrastat': False
    }

    def _check_accessory_cost(self, cr, uid, ids):
        for product in self.browse(cr, uid, ids):
            if product.is_accessory_cost and product.type != 'service':
                raise orm.except_orm(
                    _('Error :'),
                    _("The option 'Is accessory cost?' should only be "
                        "activated on 'Service' products. You have activated "
                        "this option for the product '%s' which is of type "
                        "'%s'"
                        % (product.name, product.type)))
        return True

    _constraints = [(
        _check_accessory_cost,
        "Wrong configuration of the product",
        ['is_accessory_cost', 'type']
        )]

class product_category(orm.Model):
    _inherit = "product.category"

    _columns = {
        'intrastat_id': fields.many2one(
            'report.intrastat.code', 'Intrastat code',
            help="Code from the Harmonised System. If this code is not "
            "set on the product itself, it will be read here, on the "
            "related product category."),
    }

class product_supplierinfo(orm.Model):
    _inherit = "product.supplierinfo"

    _columns = {
        'origin_country_id': fields.many2one(
            'res.country', 'Country of origin',
            help="Country of origin of the product "
            "(i.e. product 'made in ____') when purchased from this supplier. "
            "This field is used only when the equivalent field on the product "
            "form is empty."),
        }

    def _same_supplier_same_origin(self, cr, uid, ids):
        """Products from the same supplier should have the same origin"""
        for supplierinfo in self.browse(cr, uid, ids):
            country_origin_id = supplierinfo.origin_country_id.id
            # Search for same supplier and same product
            same_product_same_supplier_ids = self.search(
                cr, uid, [
                    ('product_id', '=', supplierinfo.product_id.id),
                    ('name', '=', supplierinfo.name.id)])
            # 'name' on product_supplierinfo is a many2one to res.partner
            for supplieri in self.browse(
                    cr, uid, same_product_same_supplier_ids):
                if country_origin_id != supplieri.origin_country_id.id:
                    raise orm.except_orm(
                        _('Error !'),
                        _("For a particular product, all supplier info "
                            "entries with the same supplier should have the "
                            "same country of origin. But, for product '%s' "
                            "with supplier '%s', there is one entry with "
                            "country of origin '%s' and another entry with "
                            "country of origin '%s'.")
                        % (supplieri.product_id.name,
                            supplieri.name.name,
                            supplierinfo.origin_country_id.name,
                            supplieri.origin_country_id.name))
        return True

    _constraints = [(
        _same_supplier_same_origin,
        "Wrong configuration of the supplier information",
        ['origin_country_id', 'name', 'product_id']
        )]

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: