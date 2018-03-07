# -*- encoding: utf-8 -*-

from odoo import api, models, fields, _

import logging
import json

logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    firmas_username = fields.Char()
    firmas_password = fields.Char()
    firmas_active = fields.Boolean()

    @api.onchange('firmas_validate')
    def change_firmas_validate(self):
        pass

    @api.model
    def get_values(self):
        firmas = json.loads(self.env['ir.config_parameter'].get_param(
                'l10n_lv_partner_data_load_firmas', '{}'))

        vals = super(ResConfigSettings, self).get_values()
        vals.update({
            'firmas_username': firmas.get('username'),
            'firmas_password': firmas.get('password'),
            'firmas_active': firmas.get('active'),
            })
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

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
