# -*- encoding: utf-8 -*-
##############################################################################
#
#    Part of Odoo.
#    Copyright (C) 2016 ITS-1 (<http://www.its1.lv/>)
#                       E-mail: <info@its1.lv>
#                       Address: <Vienibas gatve 109 LV-1058 Riga Latvia>
#                       Phone: +371 67289467
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

from openerp import api, fields, models, _
from openerp.exceptions import UserError
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

class ResPartner(models.Model):
    _inherit = "res.partner"

    load_from_registry = fields.Boolean('Load data from LV company registry')

    @api.onchange('load_from_registry', 'company_registry')
    def _onchange_load_from_registry(self):
        company_registry = self.company_registry
        if company_registry and (self.load_from_registry == True):
            country_obj = self.env['res.country']
            reg_num = re.sub("\D", "", company_registry)
            url = 'http://services.ozols.lv/misc/company_info.aspx?type=1&rnum=%s' % reg_num
            try:
                pyPage = urllib.urlopen(url)
            except:
                raise UserError(_("Unable to connect to service! There is a problem with data loading, so you may have to enter data manually."))
            content = pyPage.read()
#            encoding = pyPage.headers['content-type'].split('charset=')[-1]
            record = content.decode('utf-8').encode('cp1257')
            dom = parseString(record)
            name = dom.getElementsByTagName('name')
            name_val = False
            if name:
                name_val = name[0].toxml().replace('<name>','').replace('</name>','')
            c_type = dom.getElementsByTagName('companytype')
            if c_type and name:
                c_type_t = c_type[0].toxml().replace('<companytype>','').replace('</companytype>','')
                for item in company_list:
                    if c_type_t.upper() == item[0].upper():
                        c_type_t = item[-1]
                        break
                name_val = c_type_t + ' "' + name_val + '"'
            if name_val:
                self.name = name_val
            c_reg_num = dom.getElementsByTagName('regnum')
            if c_reg_num:
                self.company_registry = c_reg_num[0].toxml().replace('<regnum>','').replace('</regnum>','')
            phone = dom.getElementsByTagName('phone')
            if phone:
                self.phone = phone[0].toxml().replace('<phone>','').replace('</phone>','')
            street = dom.getElementsByTagName('street')
            if street:
                self.street = street[0].toxml().replace('<street>','').replace('</street>','').replace('&quot;','"')
            city = dom.getElementsByTagName('city')
            if city:
                self.city = city[0].toxml().replace('<city>','').replace('</city>','')
            zip_no = dom.getElementsByTagName('postalcode')
            zip_val = False
            if zip_no:
                zip_val = zip_no[0].toxml().replace('<postalcode>','').replace('</postalcode>','')
                self.zip = zip_val
            vat = dom.getElementsByTagName('vatnum')
            vat_val = False
            if vat:
                vat_val = vat[0].toxml().replace('<vatnum>','').replace('</vatnum>','')
                self.vat = vat_val
            country_id = self.env.ref('base.lv').id
            country = dom.getElementsByTagName('country')
            if country:
                country_name = country[0].toxml().replace('<country>','').replace('</country>','')
                countries = country_obj.search([('name','=',country_name)])
                if countries:
                    country_id = countries[0].id
            if (not country) and (zip_val):
                country_code = re.sub(r"[^A-Za-z]+", '', zip_val)
                countries = country_obj.search([('code','=',country_code)])
                if countries:
                    country_id = countries[0].id
            if (not country) and (not zip_no) and (vat_val):
                country_code = re.sub(r"[^A-Za-z]+", '', vat_val)
                countries = country_obj.search([('code','=',country_code)])
                if countries:
                    country_id = countries[0].id
            if (not country) and (not zip_no) and (not vat):
                country_code = re.sub(r"[^A-Za-z]+", '', company_registry)
                countries = country_obj.search([('code','=',country_code)])
                if countries:
                    country_id = countries[0].id
            self.country_id = country_id
            self.load_from_registry = False

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: