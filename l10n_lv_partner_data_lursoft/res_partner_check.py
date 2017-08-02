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

import requests
import lursoft_client

from requests.exceptions import ConnectionError

from odoo import api, models, fields, _
from odoo.exceptions import UserError

import logging

logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    field_map = {
            'city': 'city',
            'zip': 'index',
            'name': 'firm',
            #'website': 'www',
            #'email': 'email',
            'phone': 'phone',
            'vat': 'vat',
            }

    registry_valid = fields.Boolean()

    def service_is_enabled(self):
        return self.env.user.lursoft_enabled

    def _normalize_company_data(self, values):
        normalized = {}
        for field, remote_key in self.field_map.iteritems():
            normalized[field] = values[remote_key]

        # NOTE: this is probably more understandable than a cryptic lambda func
        normalized.update(
                street='%s %s' % (values['street'], values['house']),
                country_id=self.env.ref('base.%s' % values['country'].lower()).id
                )
        return normalized


    def check_registry(self, code):
        client = lursoft_client.LursoftClient(self.env.user.lursoft_username,
                                              self.env.user.lursoft_password)
        try:
            response = client.query_by_regno(code)
        except ConnectionError:
            raise UserError(_('Couldnt not connect to Lursoft. Please try again later!'))
        except AuthError:
            username = self.env.user.lursoft_username
            raise UserError(_('Login with account {} failed!'
                              'Please check your login information '
                              'and try again.').format(username))
        except MaxLoginAttempts:
            raise UserError(_('Password was entered incorrectly more than 5 times'))
        except QuotaExceed:
            raise UserError(_('No requests/credit left. Please contact Lursoft'))
        except NotFoundError:
            raise UserError(_('Company not found!'))
        except LursoftException:
            raise UserError(_('Something went wrong. Try again later'))
        else:
            return self._normalize_company_data(response)


## vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
