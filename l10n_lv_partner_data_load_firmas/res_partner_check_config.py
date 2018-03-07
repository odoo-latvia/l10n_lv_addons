# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2017 Allegro (<http://www.allegro.lv/>)
#                       E-mail: <info@allegro.lv>
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

from odoo import api, models, fields, _
from odoo.exceptions import UserError, Warning
from . import firmas

import requests
import logging
import json

logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    firmas_username = fields.Char()
    firmas_password = fields.Char()
    firmas_active = fields.Boolean()

    @api.model
    def get_values(self):
        firmas = json.loads(self.env['ir.config_parameter'].get_param(
                'l10n_lv_partner_data_load_firmas', '{}'))
        self.firmas_username = firmas.get('username')
        self.firmas_password = firmas.get('password')
        self.firmas_active = firmas.get('active')

        vals = super(ResConfigSettings, self).get_values()
        return vals

    @api.multi
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        config = {
                'username': self.firmas_username,
                'password': self.firmas_password,
                'active': self.firmas_active,
                }
        if not all(config.values()):
            config = {}
        self.env['ir.config_parameter'].set_param(
                'l10n_lv_partner_data_load_firmas', json.dumps(config))

## vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
