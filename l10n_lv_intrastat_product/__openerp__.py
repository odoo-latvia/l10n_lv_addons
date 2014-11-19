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

{
    'name': 'Module for Intrastat product reporting for Latvia',
    'version': '1.0',
    'category': 'Accounting & Finance',
    'license': 'AGPL-3',
    'description': """This module adds support for the Intrastat product reporting for Latvia.
    """,
    'author': 'Akretion, Alistek Ltd, ITS-1',
    'website': 'http://www.its1.lv/',
    'depends': ['report_intrastat', 'base_incoterms'],
    'init_xml': [],
    'data': [
#        'security/ir.model.access.csv',
#        'data/types.xml',
        'intrastat_menu.xml',
#        'intrastat_product_view.xml',
#        'intrastat_type_view.xml',
#        'company_view.xml',
        'partner_view.xml',
        'product_view.xml',
#        'stock_view.xml',
#        'invoice_view.xml',
        'tax_view.xml'
    ],
    'installable': True,
    'active': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: