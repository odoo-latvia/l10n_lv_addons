# -*- coding: utf-8 -*-

from odoo import models, fields

class ResPartner(models.Model):
    _inherit = 'calendar.event'

    privacy = fields.Selection(default='confidential')
