# -*- encoding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
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

{
    "name" : "LV Natural resources tax",
    "version" : "1.0",
    "description" : """Module provides wizard for computing data for Natural resources tax declarations for Latvia.""",
    "author" : "Alistek Ltd, ITS-1",
    "website" : "http://www.its1.lv/",
    "category" : "Accounting & Finance",
    "url" : "",
    "depends" : ['stock_landed_costs', 'delivery', 'hr', 'base_returns'],
    "init_xml" : [],
    "data" : [
        'wizard/drn_wizard_view.xml',
        'l10n_lv_drn_menu.xml',
        'drn_product_view.xml',
        'drn_stock_move_view.xml',
        'security/ir.model.access.csv',
        'data/data_eei.xml',
        'data/report_data.xml',
        'data/data.xml'
    ],
    "demo_xml" : [],
    "license" : "GPL-3",
    "installable" : True,
    "active" : False,

}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: