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

from openerp.osv import osv, orm, fields
from openerp.tools.translate import _

class res_company(orm.Model):
    _inherit = "res.company"

    _columns = {
        'export_obligation_level': fields.selection(
            [('detailed', 'Intrastat-1B/2B'), ('simplified', 'Intrastat-1A/2A')],
            'Export according to CBS defined limiting value for a reporting year',
            help='Export-Intrastat-1A limiting value for year 2014 is 130000 EUR.'),
        'import_obligation_level': fields.selection(
            [('detailed', 'Intrastat-1B/2B'), ('simplified', 'Intrastat-1A/2A')],
            'Import according to CBS defined limiting value for a reporting year',
            help='Import-Intrastat-1A limiting value for year 2014 is 130000 EUR.'),
        'default_intrastat_transport': fields.selection([
            (1, 'Maritime transport'),
            (2, 'Rail transport'),
            (3, 'Road transport'),
            (4, 'Air transport'),
            (5, 'Post'),
            (7, 'Fixed transport systems (pipelines)'),
            (8, 'Inland waterway transport'),
            (9, 'Carrying without means of transport'),
            ], 'Default type of transport',
            help="If the 'Type of Transport' is not set on the invoice, "
            "Odoo will use this value."),
        'statistical_pricelist_id' : fields.many2one(
            'product.pricelist',
            'Pricelist for statistical value',
            help="Select the pricelist that will be used to compute the statistical value intrastat lines generated from repair picking)."),
        'default_intrastat_type_out_invoice': fields.many2one(
            'report.intrastat.type',
            'Default intrastat type for customer invoice',
            ondelete='restrict'),
        'default_intrastat_type_out_refund': fields.many2one(
            'report.intrastat.type',
            'Default intrastat type for customer refund',
            ondelete='restrict'),
        'default_intrastat_type_in_invoice': fields.many2one(
            'report.intrastat.type',
            'Default intrastat type for supplier invoice',
            ondelete='restrict'),
        'default_intrastat_type_in_picking': fields.many2one(
            'report.intrastat.type',
            'Default intrastat type for incoming products'),
        'default_intrastat_type_out_picking': fields.many2one(
            'report.intrastat.type',
            'Default intrastat type for outgoing products'),
    }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: