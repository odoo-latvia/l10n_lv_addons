# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2017 Allegro (<http://www.allegro.lv/>)
#                       E-mail: <info@allegro.lv>
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
    'name': 'Load Partner Data',
    'version': '1.0',
    'description': """

    Extend the regno widget to load company data based on their registry number.
    The widget expects the following options to be passed.
    options='{
        "is_company_field": "is_company fieldname",
        "country_code_field": "res.country.code fieldname",
        }'
    """,
    'author': 'Allegro',
    'website': 'http://www.allegro.lv/',
    'category': 'Hidden',
    'depends': ['crm', 'l10n_lv_partner_data_validate', 'l10n_lv_partner_title'],
    'demo_xml': [],
    'data': [
        'templates/registry_backend_assets.xml',
    ],
    'qweb': [
    ],
    'auto_install': False,
    'installable': True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
