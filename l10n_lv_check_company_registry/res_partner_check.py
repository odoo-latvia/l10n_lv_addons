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
from operator import itemgetter

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

    def test_partners(self, cr, uid, name, company_registry, identification_id, parent_id, partner_id=False, context=None):
        if context is None:
            context = {}

        test_name = False
        if name:
            test_name = self._form_name(cr, uid, name, context=context)
            test_name = test_name.encode('utf-8')
        partner_domain = []
        ename = _("partner")
        enames = _("partners")
        if parent_id:
            ename = _("contact")
            enames = _("contacts")
            partner_domain.append(('parent_id','=',parent_id))
            parent_name = self.read(cr, uid, [parent_id], ['name'], context=context)[0]['name']
        if partner_id:
            partner_domain.append(('id','!=',partner_id))
        partner_ids = []
        err_text = ""
        if test_name:
            partner_name_domain = partner_domain[:]
            cr.execute("""CREATE OR REPLACE FUNCTION array_remove_txtfromlst(inputarr TEXT[], inputtxt TEXT)
RETURNS text[] AS $outputarr$
DECLARE
    outputarr text[];
BEGIN
    FOR i IN array_lower(inputarr, 1) .. array_upper(inputarr, 1)
    LOOP
        IF inputarr[i] != inputtxt THEN
            outputarr = array_append(outputarr, inputarr[i]);
        END IF;
    END LOOP;
    RETURN outputarr;
END;
$outputarr$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION form_name_fromtxt(srcname TEXT)
RETURNS text AS $resname$
DECLARE
    new_srcname text;
    textlist text[];
    replacelist text[];
    rpl int;
    rplval text;
    t int;
    tval text;
    t1 text;
    resname text;
BEGIN
    replacelist =  array['SIA', 'IU', 'I/U', 'AS', 'A/S', 'SABIEDRĪBA', 'LTD', 'CORP', 'INC'];
    new_srcname = upper(srcname);
    FOR rpl IN array_lower(replacelist, 1) .. array_upper(replacelist, 1)
    LOOP
        rplval = replacelist[rpl];
        textlist = string_to_array(new_srcname, ' ');
        IF array_lower(textlist, 1) != NULL THEN
            FOR t IN array_lower(textlist, 1) .. array_upper(textlist, 1)
            LOOP
                tval = textlist[t];
                t1 = replace(replace(replace(replace(tval,',',''),' ',''),'"',''),'''','');
                IF rplval = t1 THEN
                    textlist = array_remove_txtfromlst(textlist, tval);
                END IF;
            END LOOP;
            new_srcname = array_to_string(textlist, ' ');
            new_srcname = replace(replace((trim(both ',' from (trim(both ' ' from new_srcname)))),'"',''),'''','');
        END IF;
    END LOOP;
    resname = new_srcname;
    RETURN resname;
END;
$resname$ LANGUAGE plpgsql;

select id from res_partner
where char_length(form_name_fromtxt(name)) > 1 and (convert_from(convert_to(form_name_fromtxt(name),'utf-8'),'utf-8') like concat('%%','%s','%%') or '%s' like concat('%%',convert_from(convert_to(form_name_fromtxt(name),'utf-8'),'utf-8'),'%%'));""" % (test_name, test_name))
            sp_ids = map(itemgetter(0), cr.fetchall())
            partner_name_domain.append(('id','in',sp_ids))
            partner_name_ids = self.search(cr, uid, partner_name_domain, context=context)
            partner_ids += partner_name_ids
            pname_count = len(partner_name_ids)
            inp_text = "."
            if pname_count != 0:
                inp_text = ""
                if parent_id:
                    inp_text += _(" for partner %s") % parent_name
                pn_ids = partner_name_ids
                if pname_count > 6:
                    pn_ids = pn_ids[:6]
                p_names = [r['name'] for r in self.read(cr, uid, pn_ids, ['name'], context=context)]
                p_names = ", ".join(p_names)
                inp_text += ": %s" % p_names
                inp_text += (pname_count > 6 and "..." or ".")
            err_text += _("%s %s found with similar name%s") % (pname_count, enames, inp_text)
        preg_count = 0
        if company_registry:
            partner_reg_domain = partner_domain[:]
            partner_reg_domain.append(('is_company','=',True))
            partner_reg_domain.append(('company_registry','=',company_registry))
            partner_reg_ids = self.search(cr, uid, partner_reg_domain, context=context)
            partner_ids += partner_reg_ids
            preg_count = len(partner_reg_ids)
            inp_text = "."
            if preg_count != 0:
                pr_ids = partner_reg_ids
                if preg_count > 6:
                    pr_ids = pr_ids[:6]
                p_names = [r['name'] for r in self.read(cr, uid, pr_ids, ['name'], context=context)]
                p_names = ", ".join(p_names)
                inp_text = ": %s" % p_names
                inp_text += (preg_count > 6 and "..." or ".")
            err_text += _("%s %s found with the same company registry%s") % (preg_count, enames, inp_text)
        if identification_id:
            partner_id_domain = partner_domain[:]
            partner_id_domain.append(('is_company','=',False))
            partner_id_domain.append(('identification_id','=',identification_id))
            partner_id_ids = self.search(cr, uid, partner_id_domain, context=context)
            partner_ids += partner_id_ids
            pid_count = len(partner_id_ids)
            inp_text = "."
            if pid_count != 0:
                inp_text = ""
                if parent_id:
                    inp_text += _(" for partner %s") % parent_name
                pi_ids = partner_id_ids
                if pid_count > 6:
                    pi_ids = pi_ids[:6]
                p_names = [r['name'] for r in self.read(cr, uid, pi_ids, ['name'], context=context)]
                p_names = ", ".join(p_names)
                inp_text += ": %s" % p_names
                inp_text += (pid_count > 6 and "..." or ".")

            err_text += _("%s %s found with the same identification ID%s") % (preg_count, enames, inp_text)
        if partner_ids:
            raise osv.except_osv(err_text, _("Check the 'Allow similar Partner creation' box and try again if you want to save the %s anyway.") % ename)
        return False

    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}
        if 'allow_creation' not in vals or vals['allow_creation'] == False:
            name = vals.get('name',False)
            company_registry = vals.get('company_registry',False)
            identification_id = vals.get('identification_id',False)
            parent_id = vals.get('parent_id',False)
            self.test_partners(cr, uid, name, company_registry, identification_id, parent_id, context=context)
        return super(res_partner, self).create(cr, uid, vals, context=context)

    def write(self, cr, uid, ids, vals, context=None):
        if context is None:
            context = {}
        allow = True
        partner_obj = self.pool.get('res.partner')
        if not isinstance(ids, list):
            ids = [ids]
        for partner in partner_obj.browse(cr, uid, ids, context):            
            if ('allow_creation' in vals and vals['allow_creation'] == False) or ('allow_creation' not in vals and partner.allow_creation == False):
                name = 'name' in vals and vals['name'] or partner.name
                company_registry = 'company_registry' in vals and vals['company_registry'] or partner.company_registry
                identification_id = 'identification_id' in vals and vals['identification_id'] or partner.identification_id
                parent_id = 'parent_id' in vals and vals['parent_id'] or (partner.parent_id and partner.parent_id.id or False)
                if name or company_registry or identification_id or parent_id:
                    self.test_partners(cr, uid, name, company_registry, identification_id, parent_id, partner_id=partner.id, context=context)
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
