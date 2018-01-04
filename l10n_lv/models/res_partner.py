# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT 

class ResPartner(models.Model):
    _inherit = 'res.partner'

    bussiness_form = fields.Many2one(string='Bussiness Form', related='title')
