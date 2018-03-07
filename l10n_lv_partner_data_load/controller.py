# -*- encoding: utf-8 -*-
from requests.exceptions import ConnectionError
from odoo.exceptions import UserError

from odoo import http

import werkzeug
import requests
import logging
import json

logger = logging.getLogger(__name__)


class RegistryCheck(http.Controller):

    def _vendors(self, **kw):
        """ Override to append a vendor"""
        return {}

    @http.route(['/l10n_lv_partner_data_load/vendors'], type='json')
    def vendors(self, **kw):
        return json.dumps(self._vendors(**kw))

    @http.route(['/l10n_lv_partner_data_load/<vendor>/<regno>'], type='json')
    def get_by_regno(self, vendor, regno, **kw):
        method = getattr(self, 'get_by_regno_{}'.format(vendor))
        return method(regno)

    @http.route(['/l10n_lv_partner_data_load/goto/<vendor>/<regno>'], type='http')
    def goto_vendor_site(self, vendor, regno, **kw):
        url = self._vendors()[vendor]['url'].format(regno)
        return werkzeug.utils.redirect(url, 301)


## vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
