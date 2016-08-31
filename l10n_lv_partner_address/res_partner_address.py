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

import math
from openerp.osv import fields,osv
import openerp.tools
import openerp.pooler
from openerp.tools.translate import _
import xml.etree.ElementTree as ET

class res_partner_address_type(osv.osv):
    _description ='Partner Address Types'
    _name = 'res.partner.address.type'

    _columns = {
        'name': fields.char('Type Name', size=36, required=True),
        'for': fields.selection([('juridical','Juridical Person'),('physical','Physical Person')], 'For', required=True, help="Choose the type of person this address type will be used for.")
    }

res_partner_address_type()

class res_partner_address(osv.osv):
    _description ='Partner Addresses'
    _name = 'res.partner.address'
    _order = 'type, street'

    _columns = {
        'partner_id': fields.many2one('res.partner', 'Partner', ondelete='cascade'),
        'type': fields.many2one('res.partner.address.type', 'Type'),
        'street': fields.char('Street'),
        'street2': fields.char('Street2'),
        'zip': fields.char('Zip', change_default=True, size=24),
        'city': fields.char('City'),
        'state_id': fields.many2one('res.country.state', 'State', domain="[('country_id','=',country_id)]", ondelete='restrict'),
        'country_id': fields.many2one('res.country', 'Country', ondelete='restrict'),
        'is_customer_add': fields.related('partner_id', 'customer', type='boolean', string='Customer'),
        'is_supplier_add': fields.related('partner_id', 'supplier', type='boolean', string='Supplier'),
        'active': fields.boolean('Active', help="Uncheck the active field to hide the contact."),
        'company_id': fields.many2one('res.company', 'Company', select=1),
        'color': fields.integer('Color Index'),
        'notes': fields.text('Notes')
    }

    def _get_default_country(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        company_obj = self.pool.get('res.company')
        company_id = company_obj._company_default_get(cr, uid, 'res.partner.address', context=context)
        country_id = company_obj.browse(cr, uid, company_id, context=context).partner_id.country_id.id or False
        return country_id

    _defaults = {
        'active': lambda *a: 1,
        'company_id': lambda s,cr,uid,c: s.pool.get('res.company')._company_default_get(cr, uid, 'res.partner.address', context=c),
        'country_id': _get_default_country,
    }

    def name_get(self, cr, user, ids, context=None):
        if context is None:
            context = {}
        if not len(ids):
            return []
        res = []
        for r in self.browse(cr, user, ids, context=context):
            elems = [r.street, r.street2, r.city, r.zip]
            if r.state_id:
               elems.append(r.state_id.name)
            if r.country_id:
                elems.append(r.country_id.name)
            addr = ', '.join(filter(bool, elems))
            params = context.get('params',{})
            if (r.partner_id or r.type) and (params.get('model',False) != 'res.partner'):
                x = []
                if r.partner_id:
                    x.append(r.partner_id.name)
                if r.type:
                    x.append(r.type.name)
                if addr:
                    addr += ' '
                addr += ('(' + ', '.join(filter(bool,x)) + ')')
            res.append((r.id, addr or '/'))
        return res

    def name_search(self, cr, user, name='', args=None, operator='ilike', context=None, limit=100):
        if not args:
            args = []
        if context is None:
            context = {}
        if name:
            country_ids = self.pool.get('res.country').search(cr, user, [('name',operator,name)])
            state_ids = self.pool.get('res.country.state').search(cr, user, [('name',operator,name)])
            search_args = ['|', ('street',operator,name), '|', ('street2',operator,name), '|', ('city',operator,name), '|', ('zip',operator,name), '|', ('country_id','in',country_ids), ('state_id','in',state_ids)]
            ids = self.search(cr, user, args + search_args)
        else:
            ids = self.search(cr, user, args, limit=limit, context=context)
        return self.name_get(cr, user, ids, context=context)

    def _update_partner(self, cr, uid, record, vals, context=None):
        if context is None:
            context = {}
        partner_obj = self.pool.get('res.partner')
        address_type_decl = self.pool.get('ir.model.data').get_object(cr, uid, 'l10n_lv_partner_address', 'res_partner_address_type_declared').id
        address_type_legal = self.pool.get('ir.model.data').get_object(cr, uid, 'l10n_lv_partner_address', 'res_partner_address_type_legal').id
        is_company = record.partner_id.is_company
        type = record.type and record.type.id or False
        if (is_company == True and type == address_type_legal) or (is_company == False and type == address_type_decl):
            partner_vals = {}
            if 'street' in vals:
                partner_vals.update({'street': vals['street']})
            if 'street2' in vals:
                partner_vals.update({'street2': vals['street2']})
            if 'city' in vals:
                partner_vals.update({'city': vals['city']})
            if 'zip' in vals:
                partner_vals.update({'zip': vals['zip']})
            if 'state_id' in vals:
                partner_vals.update({'state_id': vals['state_id']})
            if 'country_id' in vals:
                partner_vals.update({'country_id': vals['country_id']})
            if partner_vals:
                ctx = context.copy()
                ctx.update({'no_update_partner': True})
                partner_obj.write(cr, uid, [record.partner_id.id], partner_vals, context=ctx)
        return True

    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}
        res = super(res_partner_address, self).create(cr, uid, vals, context=context)
        if not context.get('no_update_address',False):
            record = self.browse(cr, uid, res, context=context)
            if record.partner_id:
                self._update_partner(cr, uid, record, vals, context=context)
        return res

    def write(self, cr, uid, ids, vals, context=None):
        if context is None:
            context = {}
        res = super(res_partner_address, self).write(cr, uid, ids, vals, context=context)
        if not context.get('no_update_address',False):
            for record in self.browse(cr, uid, ids, context=context):
                if record.partner_id:
                    self._update_partner(cr, uid, record, vals, context=context)
        return res

res_partner_address()

class res_partner(osv.osv):
    _inherit = "res.partner"

    _columns = {
        'company_registry': fields.char('Company Registry'),
        'address_id': fields.one2many('res.partner.address', 'partner_id', 'Address'),
        'office_address': fields.many2one('res.partner.address', 'Office Address', help='Enter this address, if it differs from Legal Address.'),
        'delivery_address': fields.many2one('res.partner.address', 'Delivery Address', help='Enter this address, if it differs from Legal Address.'),
        'allow_creation': fields.boolean('Allow similar Partner creation')
    }

    def fields_view_get(self, cr, uid, view_id=None, view_type='tree', context=None, toolbar=False, submenu=False):
        if context is None:
            context = {}
        res = super(res_partner,self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)
        if view_type == 'form':
            doc = ET.XML(res['arch'])
            office_type = self.pool.get('ir.model.data').get_object(cr, uid, 'l10n_lv_partner_address', 'res_partner_address_type_office').id
            node_office = doc.find(".//field[@name='office_address']")
            if node_office:
                node_office.set('domain', "[('partner_id','=',id), ('type','=',%s)]" %(office_type))
                node_office.set('context', "{'default_partner_id': id, 'default_type': %s}" %(office_type))
            delivery_type = self.pool.get('ir.model.data').get_object(cr, uid, 'l10n_lv_partner_address', 'res_partner_address_type_delivery').id
            node_delivery = doc.find(".//field[@name='delivery_address']")
            if node_delivery:
                node_delivery.set('domain', "[('partner_id','=',id), ('type','=',%s)]" %(delivery_type))
                node_delivery.set('context', "{'default_partner_id': id, 'default_type': %s}" %(delivery_type))
            res['arch'] = ET.tostring(doc, encoding='utf8', method='xml')
        return res

    def _create_address(self, cr, uid, record, vals, context=None):
        if context is None:
            context = {}
        address_obj = self.pool.get('res.partner.address')
        address_type_obj = self.pool.get('res.partner.address.type')
        address_type_decl = self.pool.get('ir.model.data').get_object(cr, uid, 'l10n_lv_partner_address', 'res_partner_address_type_declared').id
        address_type_legal = self.pool.get('ir.model.data').get_object(cr, uid, 'l10n_lv_partner_address', 'res_partner_address_type_legal').id

        address_vals = {}
        if 'street' in vals:
            address_vals.update({'street': vals['street']})
        if 'street2' in vals:
            address_vals.update({'street2': vals['street2']})
        if 'city' in vals:
            address_vals.update({'city': vals['city']})
        if 'zip' in vals:
            address_vals.update({'zip': vals['zip']})
        if 'state_id' in vals:
            address_vals.update({'state_id': vals['state_id']})
        if 'country_id' in vals:
            address_vals.update({'country_id': vals['country_id']})

        is_company = record.is_company
        if 'is_company' in vals:
            is_company = vals['is_company']
        addr_domain = [('partner_id','=',record.id)]
        if is_company == True:
            address_vals.update({'type': address_type_legal})
            addr_domain += [('type','=',address_type_legal)]
        if is_company == False:
            address_vals.update({'type': address_type_decl})
            addr_domain += [('type','=',address_type_decl)]
        address_id = address_obj.search(cr, uid, addr_domain, context=context)

        if address_vals:
            ctx = context.copy()
            ctx.update({'no_update_address': True})
            if address_id:
                address_obj.write(cr, uid, address_id, address_vals, context=ctx)
            if not address_id:
                address_vals.update({
                    'partner_id': record.id
                })
                address_obj.create(cr, uid, address_vals, context=ctx)
        return True

    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}
        res = super(res_partner, self).create(cr, uid, vals, context=context)
        if not context.get('no_update_partner',False):
            record = self.browse(cr, uid, res, context=context)
            self._create_address(cr, uid, record, vals, context=context)
        return res

    def write(self, cr, uid, ids, vals, context=None):
        if context is None:
            context = {}
        if isinstance(ids, list):
            ids = ids
        else:
            ids = [int(ids)]
        partner_ids = self.search(cr, uid, [('id','in',ids)], context=context)
        for record in self.browse(cr, uid, partner_ids, context=context):
            if not context.get('no_update_partner',False):
                self._create_address(cr, uid, record, vals, context=context)
        return super(res_partner, self).write(cr, uid, ids, vals, context=context)

    def copy(self, cr, uid, id, default=None, context=None):
        if default is None:
            default = {}
        default.update({'office_address': False, 'delivery_address': False})
        return super(res_partner, self).copy(cr, uid, id, default, context)

res_partner()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: