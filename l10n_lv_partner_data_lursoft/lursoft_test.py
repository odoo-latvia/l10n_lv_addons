# -*- coding: utf-8 -*-
import unittest
import lursoft_client

client = lursoft_client.LursoftClient(5, 5)

class TestLursoftClient(unittest.TestCase):

    def succesfull_auth(self):
        return """<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://www.w3.org/2001/09/soap-envelope">
<soap:Header xmlns:Lursoft="x-schema:/schemas/lursoft_header.xsd">
<Lursoft:SessionId>F2D95EBF8AAB1C6DCBC78FC9FB5289F4</Lursoft:SessionId>
<Lursoft:Language>LV</Lursoft:Language>
<Lursoft:IP>159.148.5.233</Lursoft:IP>
<Lursoft:Time>2017-08-01T09:42:08</Lursoft:Time>
<Lursoft:UserId>alegro_xml</Lursoft:UserId>
<Lursoft:Distributor>www.lursoft.lv</Lursoft:Distributor>
</soap:Header>
</soap:Envelope>"""

    def faulty_auth(self):
        return """<?xml version="1.0" encoding="windows-1257"?>
<soap:Envelope xmlns:soap="http://www.w3.org/2001/09/soap-envelope" xmlns:Lursoft="x-schema:/schemas/lursoft_header.xsd">
<soap:Header xmlns:Lursoft="x-schema:/schemas/lursoft_header.xsd">
<Lursoft:SessionId>3A26436D7A471A9B50FC5B2A7A09E476</Lursoft:SessionId>
<Lursoft:Language>LV</Lursoft:Language>
<Lursoft:IP>159.148.5.233</Lursoft:IP>
<Lursoft:Time>2017-08-01T10:26:46</Lursoft:Time>
<Lursoft:Distributor>www.lursoft.lv</Lursoft:Distributor>
</soap:Header>
<soap:Body>
<Fault>
<Faultcode>soap:Client</Faultcode>
<Faultstring>Request processing error</Faultstring>
<details>
<Lursoft:ErrorCode>10</Lursoft:ErrorCode>
<Lursoft:ErrorMsg><font color="#cc0000">K\xef\xfbdains lietot\xe2ja ID vai/un Parole!</font></Lursoft:ErrorMsg>
</details>
</Fault>
</soap:Body>
</soap:Envelope>"""

    def test_successfull_auth_parse_session_id(self):
        self.assertEqual(client.get_session_id(self.succesfull_auth()), 
                         'F2D95EBF8AAB1C6DCBC78FC9FB5289F4')

    def test_faulty_response_parse_error(self):
        exception = client.get_error(self.faulty_auth())
        print exception
        self.assertTrue(isinstance(exception, Exception))


if __name__ == '__main__':
    unittest.main()
