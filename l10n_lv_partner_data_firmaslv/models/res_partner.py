# -*- encoding: utf-8 -*-
##############################################################################
#
#    Part of Odoo.
#    Copyright (C) 2021 Ozols Grupa (<http://www.ozols.lv/>)
#                       E-mail: <info@ozols.lv>
#                       Address: <Vienibas gatve 109 LV-1058 Riga Latvia>
#                       Phone: +371 67289211
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

from odoo import api, fields, models, _
import xml.etree.ElementTree as ET
from xml.dom.minidom import parseString
import requests

class Partner(models.Model):
    _inherit = "res.partner"

    @api.model
    def login_firmaslv(self, userid, password, utf=True):
        baseurl = 'https://www.firmas.lv/api'
        params = {
            'act': 'LOGINXML',
            'Userid': userid,
            'Password': password
        }
        if utf:
            params.update({'utf': 1})
        response = requests.post(baseurl, params=params)
        rc = parseString(response.content)
        fault = rc.getElementsByTagName('Fault')
        if fault:
            e_txt = 'Firmas.lv:'
            for f in fault:
                fs = f.getElementsByTagName('Firmaslv:errorMsg')
                if fs:
                    fs_node = fs[0].firstChild
                    e_txt += ' %s' % fs_node.nodeValue
            return {'error': True, 'error_message': e_txt}
        else:
            sessionid = rc.getElementsByTagName('Firmaslv:SessionId')
            sessionid_node = sessionid[0].firstChild
            return {'SessionId': sessionid_node.nodeValue}

    @api.model
    def load_firmaslv_suggestions(self, value, field_name=False, utf=True):
        param_obj = self.env['ir.config_parameter'].sudo()
        usr = param_obj.get_param('firmaslv_user')
        pwd = param_obj.get_param('firmaslv_password')
        sessionid = param_obj.get_param('firmaslv_sessionid')
        if not sessionid:
            lc = self.login_firmaslv(usr, pwd)
            if lc.get('error', False):
                return [lc]
            else:
                param_obj.set_param('firmaslv_sessionid', lc['SessionId'])
                sessionid = lc['SessionId']
        baseurl = 'https://www.firmas.lv/api'
        params = {
            'act': 'URSEARCH_XML',
            'SessionId': sessionid
        }
        if not field_name:
            params.update({'any': value})
        else:
            field_term_map = {
                'name': 'name',
                'partner_registry': 'code',
                'vat': 'code',
                'street': 'adr',
                'street2': 'adr'
            }
            if field_name in field_term_map:
                params.update({field_term_map[field_name]: value})
            else:
                params.update({'any': value})
        if utf:
            params.update({'utf': 1})
        response = requests.post(baseurl, params=params)
        rc = parseString(response.content)
        fault = rc.getElementsByTagName('Fault')
        if fault:
            login_codes = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '15', '16', '17', '18', '19', '20']
            needs_login = False
            error_msgs = []
            for f in fault:
                fc = f.getElementsByTagName('Firmaslv:errorCode')
                if fc:
                    fc_node = fs[0].firstChild
                    fc_val = fs_node.nodeValue
                    if fc_val in login_codes:
                        needs_login = True
                        break
                fs = f.getElementsByTagName('Firmaslv:errorMsg')
                if fs:
                    fs_node = fs[0].firstChild
                    fs_node_val = fs_node.nodeValue
                    if fs_node_val:
                        error_msgs.append(fs_node_val)
            if needs_login:
                lc = self.login_firmaslv(usr, pwd)
                if lc.get('error', False):
                    return [lc]
                else:
                    param_obj.set_param('firmaslv_sessionid', lc['SessionId'])
                    params.update({'SessionId': lc['SessionId']})
                    response = requests.post(baseurl, params=params)
                    rc = parseString(response.content)
                    fault = rc.getElementsByTagName('Fault')
                    if fault:
                        error_msg = 'Firmas.lv: '
                        for f in fault:
                            fs = f.getElementsByTagName('Firmaslv:errorMsg')
                            if fs:
                                fs_node = fs[0].firstChild
                                fs_node_val = fs_node.nodeValue
                                if fs_node_val:
                                    error_msg += fs_node_val
                        return [{'error': True, 'error_message': error_msg}]
            else:
                error_message = 'Firmas.lv: %s' % " ".join(error_msgs)
                return [{'error': True, 'error_message': error_message}]

        res = []
        answ_list = rc.getElementsByTagName('list')
        if answ_list:
            answ_term_map = {
                'name': 'name',
                'firm': 'label',
                'fname': 'title',
                'regcode': 'partner_registry',
                'vatcode': 'vat',
                'regtype': 'regtype',
                'virtualid': 'virtualid',
                'address': 'address',
                'faddress': 'faddress',
                'phone': 'phone',
                'email': 'email',
                'www': 'website',
                'statuss': 'status'
            }
            objects = answ_list[0].getElementsByTagName('object')
            for obj in objects:
                answ_dict = {}
                for tag, fld in answ_term_map.items():
                    otag = obj.getElementsByTagName(tag)
                    if otag:
                        otag_node = otag[0].firstChild
                        otag_value = otag_node.nodeValue
                        if otag_value:
                            answ_dict.update({fld: otag_value})
                if answ_dict:
                    res.append(answ_dict)
        return res

    @api.model
    def load_firmaslv_data(self, company_domain, partner_gid, vat):
        return {
            'name': 'Test'
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
