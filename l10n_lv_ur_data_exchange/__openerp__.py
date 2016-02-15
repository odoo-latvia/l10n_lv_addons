# -*- encoding: utf-8 -*-
##############################################################################
#
#    Part of Odoo.
#    Copyright (C) 2016 ITS-1 (<http://www.its1.lv/>)
#                       E-mail: <info@its1.lv>
#                       Address: <Vienibas gatve 109 LV-1058 Riga Latvia>
#                       Phone: +371 67289467
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
    'name': 'LV company registry data exchange',
    'version': '1.0',
    'description': """
Data exchange with the company registry of Latvia.
=====================================
Adds a checkbox 'Load data from LV company registry' in Partner form view. If this checkbox is checked, data from Latvian company registry is loaded in the corresponding Partner's data fields.
The data search is based on the Registration No field's value.
When the data loading checkbox is checked, the loaded data is not saved, so that the user can choose to save/edit the new data or leave the old data by pressing 'Discard'.
    """,
    'author': 'ITS-1',
    'website': 'http://www.its1.lv/',
    'category': 'Hidden',
    'depends': ['l10n_lv_partner_data'],
    'data': [
        'views/res_partner_view.xml'
    ],
    'auto_install': False,
    'installable': True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: