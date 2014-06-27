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
        'load_from_registry': fields.boolean('Load data from LV company registry')
    }

    def onchange_load_from_registry(self, cr, uid, ids, load_from_registry, company_registry, context=None):
        if context is None:
            context = {}
        val = {}
        if company_registry and (load_from_registry == True):
            reg_num = re.sub("\D", "", company_registry)
            url = 'http://services.ozols.lv/misc/company_info.aspx?type=1&rnum=%s' % reg_num
            pyPage = urllib.urlopen(url)
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

res_partner()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: