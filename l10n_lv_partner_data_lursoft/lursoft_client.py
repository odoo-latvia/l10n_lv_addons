#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import xml.etree.ElementTree as ET
import requests
import logging

from lxml.etree import ParseError
from datetime import datetime as dt
from hashlib import md5

logger = logging.getLogger(__name__)


xmlns = {
    'env': 'http://www.w3.org/2001/09/soap-envelope',
    'ls': 'x-schema:/schemas/lursoft_header.xsd',
    }

class LursoftException(Exception):
    pass

class AuthError(LursoftException):
    """Auth failure. Ussualy a retry solves the problem
    """
    pass

class QuotaExceed(LursoftException):
    """User might be out of funds. He/she should contact Lursoft
    """
    pass

class MissingArguments(LursoftException):
    """Lursoft API excepts arguments not supplied by odoo
    """
    pass

class MissingUserCode(LursoftException):
    """Users personal number not supplied
    """
    pass

class NotFoundError(LursoftException):
    pass

class ServerError(LursoftException):
    pass

class MaxLoginAttempts(LursoftException):
    pass

class LursoftClient(object):

    baseurl = 'https://www.lursoft.lv/server3'
    session_id = None

    ns = xmlns
    def __init__(self, user, password):
        self.user = user
        self.password = password

    def get(self, **kwargs):

        if not self.session_id:
            self.auth()

        kwargs.update(SessionId=self.session_id, utf=1)

        return self._get(kwargs)

    def _get(self, **kwargs):
        response = requests.post(self.baseurl, params=kwargs)

        error = self.find_error(response.content)
        if error:
            raise error

        return response.content

    def find_error(self, response):
        """raise error returned by API call
        """
        try:
            respXML = ET.fromstring(response)
        except ParseError as e:
            raise LursoftException(e.message)

        errCodeXml = respXML.find('env:Body/Fault/details/ls:ErrorCode',
                                  self.ns)
        try:
            errcode = int(errCodeXml is not None and errCodeXml.text or None)
        except TypeError:
            return None

        else:
            msg = respXML.find('env:Body/Fault/details/ls:ErrorMsg/font',
                            self.ns).text

            # The doc we have specifies describes 10, 11
            # similiar to a HTTP 500, but in practice 10
            # is returned for invalid credentials.
            if errcode == 19:
                return MaxLoginAttempts(errcode, msg)
            elif (errcode >= 1 and errcode <= 10) or\
                    (errcode >= 15 and errcode <= 18):
                return AuthError(errcode, msg)
            elif errcode <= -1 and errcode >= -9:
                return QuotaExceed(errcode, msg)
            elif errcode == 11:
                return ServerError(errcode, msg)
            elif errcode == 12:
                return MissingArguments(errcode, msg)
            elif errcode == 13:
                return MissingUserCode(errcode, msg)
            elif errcode == 14:
                return NotFoundError(errcode, msg)
            else:
                return LursoftException(errcode, msg)

    def get_session_id(self, response):
        respXML = ET.fromstring(response)
        header = respXML.find('env:Header', self.ns)
        return header.find('ls:SessionId', self.ns).text


    def auth(self, retry=2):
        """Retry authentication x amount of times before giving up
        """
        try:
            print 'Login attempts left ', retry
            xmlresponse = self._get(act='LOGINXML',
                                    Userid=self.user,
                                    Password=self.password)
        except AuthError as e:
            if retry > 0:
                return self.auth(retry-1)
            else:
                raise e

        else:
            self.session_id = self.get_session_id(xmlresponse)
            return self.session_id

    def query_by_regno(self, regno, part=None):
        response = self.get(code=regno)
        return LursoftPerson(response)



class LursoftPerson(dict):
    """A wrapper for requests response"""

    ns = xmlns

    # maybe replace by a XSLT map
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
        #'aname': 'person/aname',
        'register': 'person/register',
        'type': 'person/type',
        'vat': 'person/pvncode',

        'full_address': 'person/address/address_full',
        'city': 'person/address/city',
        'street': 'person/address/street',
        'house': 'person/address/house',
        'index': 'person/address/index',
        #'codelevel': 'person/address/codelevel',
 
        'fact_full_address': 'person/address/address_full',
        'fact_city': 'person/address/city',
        'fact_street': 'person/address/street',
        'fact_house': 'person/address/house',
        'fact_index': 'person/address/index',
        'fact_codelevel': 'person/address/codelevel',

        'status': 'person/statuss',
        #'statusdate': 'person/statussdate',
        'phone': 'person/phone',
        #'www': 'person/www',
        #'email': 'person/email',
        #'last_changed': 'person/LastChanges',
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
            value = super(LursoftPerson, self).__getitem__(name)
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


# todo error should be handler by the client
def _get_error_code(etree):
    err_code =  etree.find('env:Body/Fault/details/ls:errorCode', xmlns)
    return None if err_code is None else int(err_code.text)


if __name__ == '__main__':
    import sys
    args = sys.argv[1:]
    l = LursoftClient(args[0], args[1])
