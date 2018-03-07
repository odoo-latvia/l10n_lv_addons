# -*- encoding: utf-8 -*-
from odoo.addons.l10n_lv_partner_data_load.controller import RegistryCheck
from odoo.http import request, Response
from odoo import _
from . import firmas

import werkzeug
import json

class FirmasCheck(RegistryCheck):

    def _vendors(self):
        vendors = super()._vendors()
        firmas = json.loads(request.env['ir.config_parameter'].get_param(
                'l10n_lv_partner_data_load_firmas', '{}'))
        if firmas.get('active'):
            vendors.update({
                'firmas': {
                        'label': 'Firmas.lv',
                        'url': 'https://www.firmas.lv/results?srch={}',
                    }
                })
        return vendors

    def get_credentials_firmas(self):
        firmas = json.loads(request.env['ir.config_parameter'].get_param(
                'l10n_lv_partner_data_load_firmas', '{}'))
        return firmas.get('username'), firmas.get('password')


    def get_by_regno_firmas(self, regno):
        client = firmas.Firmas(*self.get_credentials_firmas())
        try:
            info = client.query(regno)
        except firmas.AuthFailure:
            return {'error': _('Authentication failure')}
        except firmas.NotFoundError:
            return {'error': _('Firm %s not found') % regno}
        except firmas.QuotaExceed:
            return {'error':
                    _('Quota exceeded! Contact Firmas.lv for more information')
                    }


        payload = {
            'name': info['firm'],
            'city': info['city'],
            'zip': info['index'],
            'vat': info['vat_code'],
            'phone': info['phone'],
            'email': info['email'],
            'website': info['www'],
            }

        payload.update({
            'street': ', '.join(x for x in [info['street'], info['house']]),
            })
        return payload
