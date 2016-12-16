#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import xml.etree.ElementTree as ET
import requests

class Luresoft(object):

    baseurl = 'https://www.lursoft.lv/server3'
    user = 'in225854'
    password = 'novembris'
    session_id = None

    ns = {
        'env': 'http://www.w3.org/2001/09/soap-envelope',
        'ls': 'x-schema:/schemas/lursoft_header.xsd',
        }

    def __init__(self):
        pass

    def get(self, **kwargs):

        if not self.session_id:
            self.auth()

        kwargs.update(sessionid=self.session_id, userperscode=0, utf=1)

        response = requests.post(self.baseurl, data=kwargs)
        # look for <fault> raise error
        # return jsonified object
        if response.ok:
            return response.content
        return False

    def auth(self):
        response = requests.post(self.baseurl, {
            'act': 'LOGINXML',
            'userid': self.user,
            'password': self.password})
        respXML = ET.fromstring(response.content)
        header = respXML.find('env:Header', self.ns)
        self.session_id = header.find('ls:SessionId', self.ns).text
        return True

    def logout(self):
        pass


    def query(self, code, part=None):
        #import odoo.addons.l10n_lv_check_company_registry.responses
        #import responses
        #respXML = ET.fromstring(responses.success_query)
        #person = respXML.find('.//person')
        #return xml2dict(person)
        content = self.get(act='URPERSON_XML', code=code)
        respXML = ET.fromstring(content)
        person = respXML.find('.//person')
        return xml2dict(person)

def xml2dict(el):
    return {e.tag: e and xml2dict(e) or e.text for e in el}


if __name__ == '__main__':
    l = Luresoft()
