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
    _rec_name = 'street'

    _columns = {
        'partner_id': fields.many2one('res.partner', 'Partner', ondelete='cascade'),
        'type': fields.many2one('res.partner.address.type', 'Type'),
        'street': fields.char('Street', size=256),
        'zip': fields.char('Zip', change_default=True, size=24),
        'city': fields.char('City', size=128),
        'state_id': fields.many2one("res.country.state", 'Fed. State', domain="[('country_id','=',country_id)]"),
        'country_id': fields.many2one('res.country', 'Country'),
        'is_customer_add': fields.related('partner_id', 'customer', type='boolean', string='Customer'),
        'is_supplier_add': fields.related('partner_id', 'supplier', type='boolean', string='Supplier'),
        'active': fields.boolean('Active', help="Uncheck the active field to hide the contact."),
        'company_id': fields.many2one('res.company', 'Company',select=1),
        'color': fields.integer('Color Index'),
        'partner_street': fields.related('partner_id', 'street', type='char', string='Partner Street'),
        'partner_street2': fields.related('partner_id', 'street2', type='char', string='Partner Street 2'),
        'partner_city': fields.related('partner_id', 'city', type='char', string='Partner City'),
        'partner_zip': fields.related('partner_id', 'zip', type='char', string='Partner Zip'),
        'partner_state': fields.related('partner_id', 'state_id', type='many2one', relation='res.country.state', string='Partner State'),
        'partner_country': fields.related('partner_id', 'country_id', type='many2one', relation='res.country', string='Partner Country'),
        'for_domain1': fields.char('For Domain 1', size=16),
        'for_domain2': fields.char('For Domain 2', size=16),
    }

    def _get_default_country(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        company_obj = self.pool.get('res.company')
        company_id = company_obj._company_default_get(cr, uid, 'res.partner.address', context=context)
        country_id = company_obj.browse(cr, uid, company_id, context=context).partner_id.country_id.id or ''
        return country_id

    _defaults = {
        'active': lambda *a: 1,
        'company_id': lambda s,cr,uid,c: s.pool.get('res.company')._company_default_get(cr, uid, 'res.partner.address', context=c),
        'country_id': _get_default_country,
        'for_domain1': 'juridical',
        'for_domain2': 'physical'
    }

    def name_get(self, cr, user, ids, context=None):
        if context is None:
            context = {}
        if not len(ids):
            return []
        res = []
        for r in self.read(cr, user, ids, ['street','city','zip','country_id']):
            # make a comma-separated list with the following non-empty elements
            elems = [r['street'], r['city'], r['zip']]
            addr = ', '.join(filter(bool, elems))
            res.append((r['id'], addr or '/'))
        return res

    def onchange_street(self, cr, uid, ids, street, partner_id, context=None):
        if context is None:
            context = {}
        if partner_id:
            return {'value': {'partner_street': street, 'partner_street2': False}}
        return {}

    def onchange_city(self, cr, uid, ids, city, partner_id, context=None):
        if context is None:
            context = {}
        if partner_id:
            return {'value': {'partner_city': city}}
        return {}

    def onchange_zip(self, cr, uid, ids, zip, partner_id, context=None):
        if context is None:
            context = {}
        if partner_id:
            return {'value': {'partner_zip': zip}}
        return {}

    def onchange_state_id(self, cr, uid, ids, state_id, partner_id, context=None):
        if context is None:
            context = {}
        if partner_id:
            return {'value': {'partner_state': state_id}}
        return {}

    def onchange_country_id(self, cr, uid, ids, country_id, partner_id, context=None):
        if context is None:
            context = {}
        domain = {}
        if country_id:
            domain = {'state_id': [('country_id', '=', country_id)]}
        if partner_id:
            return {'value': {'partner_country': country_id}, 'domain': domain}
        return {'domain': domain}

res_partner_address()

class res_partner(osv.osv):
    _inherit = "res.partner"

    def _address_type(self, cr, uid, ids, field_name, arg, context=None):
        if context is None:
            context = {}
        res = {}
        for part in self.browse(cr, uid, ids, context=context):
            office_address = self.pool.get('ir.model.data').get_object(cr, uid, 'l10n_lv_partner_address', 'res_partner_address_type_office').id
            delivery_address = self.pool.get('ir.model.data').get_object(cr, uid, 'l10n_lv_partner_address', 'res_partner_address_type_delivery').id
            res.update({part.id: {'office_address_type': office_address, 'delivery_address_type': delivery_address}})
        return res

    _columns = {
        'name': fields.char('Name', size=148, required=True, select=True),
        'company_registry': fields.char('Company Registry', size=64),
        'address_id': fields.one2many('res.partner.address', 'partner_id', 'Address'),
        'office_address': fields.many2one('res.partner.address', 'Office Address', help='Enter this address, if it differs from Legal Address.'),
        'delivery_address': fields.many2one('res.partner.address', 'Delivery Address', help='Enter this address, if it differs from Legal Address.'),
        'allow_creation': fields.boolean('Allow similar Partner creation'),
        'office_address_type': fields.function(_address_type, type='many2one', relation='res.partner.address.type', string='Office Address Type', multi='address_type'),
        'delivery_address_type': fields.function(_address_type, type='many2one', relation='res.partner.address.type', string='Delivery Address Type', multi='address_type')
    }

    def _create_address(self, cr, uid, record, vals, method, context=None):
        if context is None:
            context = {}
        address_obj = self.pool.get('res.partner.address')
        address_type_obj = self.pool.get('res.partner.address.type')
        address_type_physical = address_type_obj.search(cr, uid, [('for','=','physical')], context=context)[0]
        address_type_juridical = address_type_obj.search(cr, uid, [('for','=','juridical')], context=context)[0]
        street = vals.get('street',[])
        street2 = vals.get('street2',[])
        if (street != []) or (street2 != []):
            if (street != []) and (street2 != []):
                if (street != False) and (street2 != False):
                    street = street + ' ' + street2
                if (street != False) and (street2 == False):
                    street = street
                if (street2 != False) and (street == False):
                    street = street2
            if (street != []) and (street2 == []):
                if record.street2:
                    if street:
                        street = street + ' ' + record.street2
                    else:
                        street = record.street2
                else:
                    street = street
            if (street2 != []) and (street == []):
                if record.street:
                    if street2:
                        street = record.street + ' ' + street2
                    else:
                        street = record.street
                else:
                    street = street2
        city = vals.get('city',[])
        zip = vals.get('zip',[])
        state = vals.get('state_id',[])
        country = vals.get('country_id',[])
        is_company = vals.get('is_company',[])
        address_id = []
        address_vals = {}
        for addr in record.address_id:
            address_id.append((addr.id))
        if address_id:
            if street != []:
                address_obj.write(cr, uid, address_id, {'street': street}, context=context)
            if city != []:
                address_obj.write(cr, uid, address_id, {'city': city}, context=context)
            if zip != []:
                address_obj.write(cr, uid, address_id, {'zip': zip}, context=context)
            if state != []:
                address_obj.write(cr, uid, address_id, {'state_id': state}, context=context)
            if country != []:
                address_obj.write(cr, uid, address_id, {'country_id': country}, context=context)
            if is_company != []:
                if is_company == True:
                    address_obj.write(cr, uid, address_id, {'type': address_type_juridical, 'for_domain1': 'juridical', 'for_domain2': 'juridical'}, context=context)
                if is_company == False:
                    address_obj.write(cr, uid, address_id, {'type': address_type_physical, 'for_domain1': 'physical', 'for_domain2': 'physical'}, context=context)
        test_val = []
        if method == 'create':
            test_val = False
        if method == 'write':
            test_val = []
        if (not address_id) and ((street != test_val) or (city != test_val) or (zip != test_val) or (state != test_val) or (country != test_val)):
            if is_company != []:
                if is_company == True:
                    addr_type = address_type_juridical
                    for_domain1 = 'juridical'
                    for_domain2 = 'juridical'
                if is_company == False:
                    addr_type = address_type_physical
                    for_domain1 = 'physical'
                    for_domain2 = 'physical'
            if is_company == []:
                if record.is_company == True:
                    addr_type = address_type_juridical
                    for_domain1 = 'juridical'
                    for_domain2 = 'juridical'
                if record.is_company == False:
                    addr_type = address_type_physical
                    for_domain1 = 'physical'
                    for_domain2 = 'physical'
            address_vals.update({
                'partner_id': record.id,
                'type': addr_type,
                'for_domain1': for_domain1,
                'for_domain2': for_domain2
            })
            if street != test_val:
                address_vals.update({'street': street})
            if city != test_val:
                address_vals.update({'city': city})
            if zip != test_val:
                address_vals.update({'zip': zip})
            if state != test_val:
                address_vals.update({'state_id': state})
            if country != test_val:
                address_vals.update({'country_id': country})
            if (country == []) or (country == False):
                context.update({'default_country_id': False})
            address_obj.create(cr, uid, address_vals, context=context)
        return True

    def _add_partner_name(self, cr, uid, partner, partner_count, context=None):
        if context is None:
            context = {}
        next_partner_name = ""
        if partner_count == 1:
            next_partner_name = (": " + partner.name)
        if (partner_count != 1) and (partner_count <= 5):
            next_partner_name += (", " + partner.name)
        if partner_count == 6:
            next_partner_name += "..."
        return next_partner_name

    def _form_name(self, cr, uid, name, context=None):
        if context is None:
            context = {}
        new_name = name.upper()
        replace_list = ['SIA', 'IU', 'I/U', 'AS', 'A/S', u'SABIEDRĪBA', 'LTD', 'CORP', 'INC']
        for value in replace_list:
            new_name_l = new_name.split(" ")
            for v in new_name_l:
                v1 = v.replace(",","").replace(" ","").replace('"',"").replace("'","")
                if value == v1:
                    new_name_l.remove(v)
            new_name = " ".join(new_name_l)
            new_name = new_name.strip().strip(",").replace('"',"").replace("'","")
        return new_name

    def test_partners(self, cr, uid, name, company_registry, context=None):
        if context is None:
            context = {}

        test_name = False
        if name:
            test_name = self._form_name(cr, uid, name, context=context)
        partner_ids = self.search(cr, uid, [], context=context)
        partner_count = 0
        partner_names = ""
        partner_count_reg = 0
        partner_names_reg = ""
        for partner in self.browse(cr, uid, partner_ids, context=context):
            if (test_name) and len(partner.name) > 1:
                p_name = self._form_name(cr, uid, partner.name, context=context)
                if (test_name in p_name) or (p_name in test_name):
                    partner_count += 1
                    if partner_count <= 6:
                        partner_names += self._add_partner_name(cr, uid, partner, partner_count, context=context)
            if (company_registry) and (partner.company_registry == company_registry):
                partner_count_reg += 1
                if partner_count_reg <= 6:
                    partner_names_reg += self._add_partner_name(cr, uid, partner, partner_count_reg, context=context)
        if (partner_count > 0) or (partner_count_reg > 0):
            raise osv.except_osv(_("%s partners found with similar name%s. %s partners found with the same company registry%s.") % (str(partner_count), partner_names, str(partner_count_reg), partner_names_reg), _("Check the 'Allow similar Partner creation' box and try again if you want to save the Partner anyway."))
        return False

    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}
        if (vals.get('allow_creation',[]) == False):
            name = vals.get('name',False)
            company_registry = vals.get('company_registry',False)
            self.test_partners(cr, uid, name, company_registry, context=context)
        res = super(res_partner, self).create(cr, uid, vals, context=context)
        record = self.browse(cr, uid, res, context=context)
        self._create_address(cr, uid, record, vals, 'create', context=context)
        return res

    def write(self, cr, uid, ids, vals, context=None):
        if context is None:
            context = {}
        name = vals.get('name',False)
        company_registry = vals.get('company_registry',False)
        if not vals.get('allow_creation',False):
            self.test_partners(cr, uid, name, company_registry, context=context)
        if isinstance(ids, list):
            ids = ids
        else:
            ids = [int(ids)]
        partner_ids = self.search(cr, uid, [('id','in',ids)], context=context)
        for record in self.browse(cr, uid, partner_ids, context=context):
            if (vals.get('allow_creation',[]) == []) and (record.allow_creation == False):
                self.test_partners(cr, uid, name, company_registry, context=context)
            self._create_address(cr, uid, record, vals, 'write', context=context)
        return super(res_partner, self).write(cr, uid, ids, vals, context=context)

    def copy(self, cr, uid, id, default=None, context=None):
        if default is None:
            default = {}
        default.update({'allow_creation': True})
        return super(res_partner, self).copy(cr, uid, id, default, context)

res_partner()

class res_users(osv.osv):
    _inherit = "res.users"

    def copy(self, cr, uid, id, default=None, context=None):
        if default is None:
            default = {}
        default.update({'allow_creation': True})
        return super(res_users, self).copy(cr, uid, id, default, context)

    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}
        context.update({'default_allow_creation': True})
        return super(res_users, self).create(cr, uid, vals, context=context)

res_users()

class res_company(osv.osv):
    _inherit = "res.company"

    def copy(self, cr, uid, id, default=None, context=None):
        if default is None:
            default = {}
        default.update({'allow_creation': True})
        return super(res_company, self).copy(cr, uid, id, default, context)

    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}
        context.update({'default_allow_creation': True})
        return super(res_company, self).create(cr, uid, vals, context=context)

res_company()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
