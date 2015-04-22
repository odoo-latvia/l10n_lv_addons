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

from openerp.osv import fields,osv
from openerp.tools.translate import _
import urllib
from xml.dom.minidom import getDOMImplementation, parseString
import base64
import re

company_list = [
    (u'Sabiedrība ar ierobežotu atbildību', 'SIA'),
    (u'Individuālais komersants', 'IK'),
    (u'Akciju sabiedrība', 'AS'),
    (u'Pašnodarbinātais', 'PN'),
    (u'Individuālais uzņēmums', 'IU'),
    (u'Zemnieku saimniecība', 'ZS'),
    (u'Zvejnieku saimniecība', 'ZvS'),
    (u'Pilnsabiedrība', 'PS'),
    (u'Komandītsabiedrība', 'KS')
    ]

class res_partner(osv.osv):
    _inherit = "res.partner"

    _columns = {
        'company_registry': fields.char('Company Registry'),
        'identification_id': fields.char('Identification ID'),
        'load_from_registry': fields.boolean('Load data from LV company registry'),
        'allow_creation': fields.boolean('Allow similar Partner creation')
    }

    def onchange_load_from_registry(self, cr, uid, ids, load_from_registry, company_registry, context=None):
        if context is None:
            context = {}
        val = {}
        if company_registry and (load_from_registry == True):
            reg_num = re.sub("\D", "", company_registry)
            url = 'http://services.ozols.lv/misc/company_info.aspx?type=1&rnum=%s' % reg_num
            try:
                pyPage = urllib.urlopen(url)
            except:
                raise osv.except_osv(_("Unable to connect to service!"), _("There is a problem with data loading, so you may have to enter data manually."))
            content = pyPage.read()
#            encoding = pyPage.headers['content-type'].split('charset=')[-1]
            record = content.decode('utf-8').encode('cp1257')
            dom = parseString(record)
            name = dom.getElementsByTagName('name')
            if name:
                val['name'] = name[0].toxml().replace('<name>','').replace('</name>','')
            c_type = dom.getElementsByTagName('companytype')
            if c_type and name:
                c_type_t = c_type[0].toxml().replace('<companytype>','').replace('</companytype>','')
                for item in company_list:
                    if c_type_t.upper() == item[0].upper():
                        c_type_t = item[-1]
                        break
                val['name'] = c_type_t + ' "' + val['name'] + '"'
            c_reg_num = dom.getElementsByTagName('regnum')
            if c_reg_num:
                val['company_registry'] = c_reg_num[0].toxml().replace('<regnum>','').replace('</regnum>','')
            phone = dom.getElementsByTagName('phone')
            if phone:
                val['phone'] = phone[0].toxml().replace('<phone>','').replace('</phone>','')
            street = dom.getElementsByTagName('street')
            if street:
                val['street'] = street[0].toxml().replace('<street>','').replace('</street>','').replace('&quot;','"')
            city = dom.getElementsByTagName('city')
            if city:
                val['city'] = city[0].toxml().replace('<city>','').replace('</city>','')
            zip_no = dom.getElementsByTagName('postalcode')
            if zip_no:
                val['zip'] = zip_no[0].toxml().replace('<postalcode>','').replace('</postalcode>','')
            vat = dom.getElementsByTagName('vatnum')
            if vat:
                val['vat'] = vat[0].toxml().replace('<vatnum>','').replace('</vatnum>','')
            val['country_id'] = self.pool.get('ir.model.data').get_object(cr, uid, 'base', 'lv').id
            country = dom.getElementsByTagName('country')
            if country:
                country_name = country[0].toxml().replace('<country>','').replace('</country>','')
                country_ids = self.pool.get('res.country').search(cr, uid, [('name','=',country_name)], context=context)
                if country_ids:
                    val['country_id'] = country_ids[0]
            if (not country) and (zip_no):
                country_code = re.sub(r"[^A-Za-z]+", '', val['zip'])
                country_ids = self.pool.get('res.country').search(cr, uid, [('code','=',country_code)], context=context)
                if country_ids:
                    val['country_id'] = country_ids[0]
            if (not country) and (not zip_no) and (vat):
                country_code = re.sub(r"[^A-Za-z]+", '', val['vat'])
                country_ids = self.pool.get('res.country').search(cr, uid, [('code','=',country_code)], context=context)
                if country_ids:
                    val['country_id'] = country_ids[0]
            if (not country) and (not zip_no) and (not vat):
                country_code = re.sub(r"[^A-Za-z]+", '', company_registry)
                country_ids = self.pool.get('res.country').search(cr, uid, [('code','=',country_code)], context=context)
                if country_ids:
                    val['country_id'] = country_ids[0]
            val['load_from_registry'] = False
        return {'value': val}

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

    def test_partners(self, cr, uid, name, company_registry, parent_id, context=None):
        if context is None:
            context = {}

        test_name = False
        if name:
            test_name = self._form_name(cr, uid, name, context=context)
        partner_domain = []
        if parent_id:
            partner_domain.append(('parent_id','=',parent_id))
        partner_ids = self.search(cr, uid, partner_domain, context=context)
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
            if parent_id:
                parent = self.browse(cr, uid, parent_id, context=context)
                first_text = _("%s contacts found with similar name%s") % (str(partner_count), partner_names)
                if partner_count > 0 and partner_count_reg > 0:
                    first_text += ", "
                if partner_count_reg > 0:
                    first_text += _("%s contacts found with the same company registry%s") % (str(partner_count_reg), partner_names_reg)
                first_text += _(" for partner %s.") % parent.name
                raise osv.except_osv(first_text, _("Check the 'Allow similar Partner creation' box and try again if you want to save the contact anyway."))
            else:
                raise osv.except_osv(_("%s partners found with similar name%s. %s partners found with the same company registry%s.") % (str(partner_count), partner_names, str(partner_count_reg), partner_names_reg), _("Check the 'Allow similar Partner creation' box and try again if you want to save the Partner anyway."))
        return False

    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}
        if 'allow_creation' not in vals or vals['allow_creation'] == False:
            name = vals.get('name',False)
            company_registry = vals.get('company_registry',False)
            parent_id = vals.get('parent_id',False)
            self.test_partners(cr, uid, name, company_registry, parent_id, context=context)
        return super(res_partner, self).create(cr, uid, vals, context=context)

    def write(self, cr, uid, ids, vals, context=None):
        if context is None:
            context = {}
        allow = True
        partner_obj = self.pool.get('res.partner')
        if not isinstance(ids, list):
            ids = [ids]
        for rec in ids:            
            if partner_obj.browse(cr, uid, rec, context).allow_creation == False:
                allow = False
                break
        name = vals.get('name',False)
        company_registry = vals.get('company_registry',False)
        parent_id = vals.get('parent_id',False)
        if ('allow_creation' in vals and vals['allow_creation'] == False) or ('allow_creation' not in vals and allow == False):
            if name or company_registry or parent_id:
                self.test_partners(cr, uid, name, company_registry, parent_id, context=context)
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
