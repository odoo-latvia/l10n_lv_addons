# -*- coding: utf-8 -*-

from lxml import etree

from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT 


class ResPartner(models.Model):
    _inherit = 'res.partner'

    title = fields.Many2one(domain="['|', ('type', '=', company_type), ('type', '=', False)]")

class ResPartnerTitle(models.Model):
    _inherit = 'res.partner.title'
    _rec_name = 'shortcut'

    type = fields.Selection([
        ('person', 'Individual'),
        ('company', 'Company'),
        ], 'Is Company')

    def name_get(self, details=True):

        if details:
            name = u'{r.shortcut} {r.name}'
        else:
            name = u'{r.shortcut}'

        names = []
        for rec in self:
            names.append((rec.id, name.format(r=rec) or r.name))

        return names

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        if args == None:
            args = []

        if operator == 'ilike':
            args += [
                '|',
                ('shortcut', 'ilike', name),
                ('name', 'ilike', name),
                ]

        return self.search(args, limit=limit).name_get(details=True)
