# -*- encoding: utf-8 -*-

from odoo import api, models, fields, _
from odoo.exceptions import UserError

import lursoft_client
import logging

logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = 'res.users'

    lursoft_username = fields.Char('Username')
    lursoft_password = fields.Char('Password')
    lursoft_enabled = fields.Boolean(help='Lursoft credentials are valid.')


## vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
