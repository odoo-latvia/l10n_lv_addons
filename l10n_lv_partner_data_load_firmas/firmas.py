#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import xml.etree.ElementTree as ET
import requests

from datetime import datetime as dt
from hashlib import md5


xmlns = {
    'env': 'http://www.w3.org/2001/09/soap-envelope',
    'ls': 'x-schema:http://www.firmas.lv/schemas/firmaslv_header.xsd',
    }


class QuotaExceed(Exception):
    pass

class MissingUserCode(Exception):
    pass

class MiscelaneousError(Exception):
    pass

class NotFoundError(Exception):
    pass

class AuthFailure(Exception):
    pass

class Firmas(object):

    # TODO: change URL
    baseurl = 'https://www.firmas.lv/api'
    session_id = None

    ns = xmlns
    def __init__(self, user, password):
        self.user = user
        self.password = password


    def get(self, user=None, **kwargs):

        #if not user:
        #    raise MissingUserCode

        if not self.session_id:
            try:
                self.auth()
            except Exception as e:
                self.auth()

                if not self.session_id:
                    raise AuthFailure('invalid Session')

        kwargs.update(SessionId=self.session_id, utf=1)
        response = requests.post(self.baseurl, params=kwargs)

        # TODO: verify that parsing is done lazily
        respXML = ET.fromstring(response.content)
        err_code = _get_error_code(respXML)
        if err_code == 1:
            raise AuthFailure('Session Expired')
        elif err_code == -6:
            raise QuotaExceed
        elif err_code == 11:
            raise NotFoundError
        # if session expired reauth and rerun the request

        # look for <fault> raise error
        # return jsonified object
        return response

    def auth(self):
        response = requests.post(self.baseurl, params={
            'act': 'LOGINXML',
            'Userid': self.user,
            'Password': self.password})
        respXML = ET.fromstring(response.content)
        err_code = _get_error_code(respXML)
        if err_code:
            raise AuthFailure('Auth request returned error code %s' % err_code)
        header = respXML.find('env:Header', self.ns)
        self.session_id = header.find('ls:SessionId', self.ns).text
        return True

    def logout(self):
        response = requests.post(self.baseurl, params={
            'act': 'LOGOUTXML',
            'SessionId': self.session_id,
            })
        # TODO: verify that session is closed
        return response

    def query(self, regno, part=None):
        response = self.get(act='URPERSON_XML', code=regno)
        return FirmasPerson(response)



class FirmasPerson(dict):
    """A wrapper for requests response"""

    ns = xmlns

    # maybe replace by a XSLT map
    # TODO: make a single source of truth
    field_map = {
        'source': None,
        'country': None,
        'search_code': None,

        'url': 'person/url',
        'name': 'person/name',
        'registered': 'person/registered',
        'regcode': 'person/regcode',
        'code': 'person/code',
        'firm': 'person/firm',
        'fname': 'person/fname',
        'aname': 'person/aname',
        'register': 'person/register',
        'type': 'person/type',
        'vat_code': 'person/vatcode',

        'full_address': 'person/address/address_full',
        'city': 'person/address/city',
        'street': 'person/address/street',
        'house': 'person/address/house',
        'index': 'person/address/index',
        'codelevel': 'person/address/codelevel',
 
        'fact_full_address': 'person/address/address_full',
        'fact_city': 'person/address/city',
        'fact_street': 'person/address/street',
        'fact_house': 'person/address/house',
        'fact_index': 'person/address/index',
        'fact_codelevel': 'person/address/codelevel',

        'status': 'person/statuss',
        'statusdate': 'person/statussdate',
        'phone': 'person/phone',
        'www': 'person/www',
        'email': 'person/email',
        'last_changed': 'person/LastChanges',
    }

    def __init__(self, request):
        """requests response or sql dict mapping from the db"""
        self._request = request
        self._xmlTree = ET.fromstring(request.content)
        err_code = _get_error_code(self._xmlTree)
        if err_code:
            raise Exception('Request returned error code %s' % err_code)

    def __getitem__(self, name):
        try:
            value = super(FirmasPerson, self).__getitem__(name)
        except KeyError:
            path = self.field_map[name] or name
            node = self._xmlTree.find('env:Body/answer/%s' % path, self.ns)
            value = (None if node is None else node.text)
        return value

    def all(self):
        vals = self.copy()
        for key in self.field_map.keys():
            vals[key] = self[key]
        return vals


def _get_error_code(etree):
    err_code =  etree.find('env:Body/Fault/details/ls:errorCode', xmlns)
    return None if err_code is None else int(err_code.text)

def xml2dict(el):
    return {e.tag: e and xml2dict(e) or e.text for e in el}


if __name__ == '__main__':
    import sys
    args = sys.argv[1:]
    l = Firmas(args[0], args[1])
