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
    def get_firmaslv_response(self, act, value, field_name=False, utf=True):
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
            'act': act,
            'SessionId': sessionid
        }
        if act == 'URSEARCH_XML':
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
        if act == 'URPERSON_XML':
            params.update({
                'code': value,
#                'part': 'B'
            })
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
                    fc_node = fc[0].firstChild
                    fc_val = fc_node.nodeValue
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
                return {'error': True, 'error_message': error_message}
        return rc

    @api.model
    def load_firmaslv_suggestions(self, value, field_name=False):
        rc = self.get_firmaslv_response('URSEARCH_XML', value, field_name=field_name)
        if isinstance(rc, dict):
            return [rc]
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
                    answ_dict.update({'src': 'Firmas.lv'})
                    res.append(answ_dict)
        return res

    @api.model
    def load_firmaslv_data(self, virtualid):
        def process_address(address, country_id=False):
            addr_tag_list = ['address_full', 'city', 'region', 'village', 'parish', 'street', 'housename', 'house', 'flat', 'index']
            addr_tag_data = {}
            for atag_name in addr_tag_list:
                atag = address[0].getElementsByTagName(atag_name)
                if atag:
                    atag_node = atag[0].firstChild
                    atag_value = atag_node.nodeValue
                    if atag_value:
                        addr_tag_data.update({atag_name: atag_value})
            addr_data = {}
            if addr_tag_data:
                if addr_tag_data.get('index', False):
                    addr_data.update({'zip': addr_tag_data['index']})
                street_lst = []
                for sf in ['street', 'housename', 'house', 'flat']:
                    if addr_tag_data.get(sf, False):
                        street_lst.append(addr_tag_data[sf])
                if addr_tag_data.get('region', False):
                    stts_domain = [('name','=',addr_tag_data['region'])]
                    if country_id:
                        stts_domain.append(('country_id','=',country_id['id']))
                    stts = self.env['res.country.state'].sudo().search(stts_domain)
                    if len(stts) == 1:
                        addr_data.update({'state_id': {'id': stts.id, 'display_name': stts.display_name}})
                        if not country_id:
                            addr_data.update({'country_id': {'id': stts.country_id.id, 'display_name': stts.country_id.display_name}})
                    else:
                        street_lst.append(addr_tag_data['region'])
                if street_lst:
                    addr_data.update({'street': ", ".join(street_lst)})
                city_lst = []
                for cf in ['city', 'village', 'parish']:
                    if addr_tag_data.get(cf, False):
                        city_lst.append(addr_tag_data[cf])
                if city_lst:
                    addr_data.update({'city': ", ".join(city_lst)})
                if (not addr_data) and addr_tag_data.get('address_full', False):
                    addr_data.update({'street': addr_tag_data['address_full']})
                if addr_data:
                    for af in ['street', 'street2', 'city', 'state_id', 'zip', 'country_id']:
                        if af not in addr_data:
                            addr_data.update({af: False})
            return addr_data
        res_data = {}
        if virtualid:
            rc = self.get_firmaslv_response('URPERSON_XML', virtualid)
            if isinstance(rc, dict):
                return rc
            answ = rc.getElementsByTagName('answer')
            if answ:
                country = answ[0].getElementsByTagName('country')
                if country:
                    country_node = country[0].firstChild
                    country_code = country_node.nodeValue
                    if country_code:
                        ctry = self.env['res.country'].sudo().search([('code','=',country_code)])
                        if len(ctry) == 1:
                            res_data.update({'country_id': {'id': ctry.id, 'display_name': ctry.display_name}})
                person = answ[0].getElementsByTagName('person')
                if person:
                    person_term_map = {
                        'name': 'name',
                        'firm': 'short_name',
                        'type': 'title',
                        'regcode': 'partner_registry',
                        'vatcode': 'vat',
                        'phone': 'phone',
                        'email': 'email',
                        'www': 'website'
                    }
                    for tag, fld in person_term_map.items():
                        ptag = person[0].getElementsByTagName(tag)
                        if ptag:
                            ptag_node = ptag[0].firstChild
                            ptag_value = ptag_node.nodeValue
                            if ptag_value:
                                res_data.update({fld: ptag_value})
                    if res_data.get('title', False):
                        ttls = self.env['res.partner.title'].sudo().search([('shortcut','=',res_data['title'])])
                        if len(ttls) == 1:
                            res_data.update({'title': {'id': ttls.id, 'display_name': ttls.display_name}})
                            if res_data.get('short_name', False):
                                res_data.update({'name': res_data['short_name']})
                        else:
                            res_data.pop('title')
                    res_data.pop('short_name')
                    address = person[0].getElementsByTagName('address')
                    if address:
                        addr_data = process_address(address, country_id=res_data.get('country_id', False))
                        if addr_data:
                            if res_data.get('country_id', False) and 'country_id' in addr_data and (not addr_data['country_id']):
                                addr_data.pop('country_id')
                            res_data.update(addr_data)
        return res_data

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
