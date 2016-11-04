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
    'name': 'Check Partner Company Registry',
    'version': '1.0',
    'description': """
Partner Company Registry Check.
=====================================
Adds a checkbox 'Load data from LV company registry' in Partner form view. If this checkbox is checked, data from Latvian Company Registry is loaded in the corresponding Partner's data fields.
The data search is based on the Company Registry field's value.
When the data loading checkbox is checked, the loaded data is not saved, so that the user can choose to save/edit the new data or leave the old data by pressing 'Discard'.
    """,
    'author': 'ITS-1',
    'website': 'http://www.its1.lv/',
    'category': 'Hidden',
    'depends': ['l10n_lv_partner_data'],
    'demo_xml': [],
    'data': [
        'res_partner_check_view.xml'
    ],
    'auto_install': False,
    'installable': True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
