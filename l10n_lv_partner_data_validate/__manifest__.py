# -*- encoding: utf-8 -*-
##############################################################################
#
#    Part of Odoo.
#    Copyright (C) 2018 Allegro IT (<http://www.allegro.lv/>)
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
    'name': 'LV Partner data validate',
    'version': '1.1',
    'category': 'Localization',
    'description': """
Additional Partner data for Latvia.
=====================================
Validates the checksum of Registration No. and Personal No. to Partner.
""",
    'author': 'Allegro IT',
    'website': 'http://www.allegro.lv',
    'images': [],
    'depends': [
        'l10n_lv_partner_data'
    ],
    'data': [
       'views/res_partner_views.xml',
        'views/templates.xml'
    ],
    'external_dependencies': {'python': ['stdnum']},
    'demo': [],
    'installable': True,
    'auto_install': False,
    'qweb': [],
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: