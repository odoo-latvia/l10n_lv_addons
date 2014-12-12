# -*- encoding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2010-2011 Akretion (http://www.akretion.com). All Rights Reserved
#    @author Alexis de Lattre <alexis.delattre@akretion.com>
#    Copyright (c) 2008-2012 Alistek Ltd. (http://www.alistek.com)
#                       All Rights Reserved.
#                       General contacts <info@alistek.com>
#    Copyright (C) 2014 ITS-1 (<http://www.its1.lv/>)
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

class report_intrastat_type(orm.Model):
    _name = "report.intrastat.type"
    _description = "Intrastat type"

    _columns = {
        'name': fields.char(
            'Name', size=256, required=True,
            help="Description of the Intrastat type."),
        'active': fields.boolean(
            'Active',
            help="The active field allows you to hide the Intrastat "
            "type without deleting it."),
        'object_type': fields.selection([
            ('out_invoice', 'Customer Invoice'),
            ('in_invoice', 'Supplier Invoice'),
            ('out_refund', 'Customer Refund'),
            ('outgoing', 'Outgoing products'),
            ('incoming', 'Incoming products'),
            ('none', 'None'),
        ], 'Possible on', select=True, required=True),
        'transaction_code': fields.selection([
            ('', '-'),
            ('11', '11'), ('12', '12'), ('13', '13'), ('14', '14'), ('19', '19'),
            ('21', '21'), ('22', '22'), ('23', '23'), ('29', '29'),
            ('30', '30'),
            ('41', '41'), ('42', '42'),
            ('51', '51'), ('52', '52'),
            ('63', '63'), ('64', '64'),
            ('70', '70'),
            ('80', '80'),
            ('91', '91'), ('99', '99'),
            ], 'Transaction code',
            help='Transaction nature codes, according to Intrastat annex No 4.'),
         'intrastat_product_type': fields.selection([
         ('import', 'Import'),
         ('export', 'Export'),
         ], 'Type', required=True),
        }

    _defaults = {
        'active': True,
    }

    _sql_constraints = [(
        'code_invoice_type_uniq',
        'unique(procedure_code, transaction_code)',
        'The pair (procedure code, transaction code) must be unique.'
        )]

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: