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

class account_invoice(orm.Model):
    _inherit = "account.invoice"

    _columns = {
        'intrastat_transport': fields.selection([
            (1, 'Maritime transport'),
            (2, 'Rail transport'),
            (3, 'Road transport'),
            (4, 'Air transport'),
            (5, 'Post'),
            (7, 'Fixed transport systems (pipelines)'),
            (8, 'Inland waterway transport'),
            (9, 'Carrying without means of transport')
            ], 'Type of transport',
            help="Type of transport of the goods. This information is "
            "required for the product intrastat report.",
            readonly=True, states={'draft': [('readonly', False)]}),
        'intrastat_country_id': fields.many2one(
            'res.country', 'Destination/Origin country of the goods',
            help="For a customer invoice, contains the country to which "
            "the goods have been shipped. For a supplier invoice, contains "
            "the country from which the goods have been shipped.",
            readonly=True, states={'draft': [('readonly', False)]}),
        'intrastat_type_id': fields.many2one(
            'report.intrastat.type', 'Intrastat type', ondelete='restrict',
            readonly=True, states={'draft': [('readonly', False)]}),
        }


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: