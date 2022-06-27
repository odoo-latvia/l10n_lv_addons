# -*- encoding: utf-8 -*-
##############################################################################
#
#    Part of Odoo.
#    Copyright (C) 2022 Ozols Grupa (<http://www.ozols.lv/>)
#                       E-mail: <info@ozols.lv>
#                       Address: <Vienibas gatve 109 LV-1058 Riga Latvia>
#                       Phone: +371 67289211
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
    'name': 'LV Partner name',
    'version': '1.0',
    'description': """
Separate partner first and last name fields.
============================================

For individuals partner surname is the last complete word. Multiple surnames can be
written by delimiting them with a dash. "Berzins Priede" -> "Berzins-Priede".
The conversion is automatic when writen in the surname field.

First and middle names are separated by a space 'Martins Juris Kristians'.


    """,
    'author': 'Allegro IT',
    'website': 'http://www.allegro.lv',
    'license': 'AGPL-3',
    'category': 'Hidden',
    'depends': ['base'],
    'data': [
        'views/res_partner_view.xml',
        'data/res_partner_data.xml'
    ],
    'auto_install': False,
    'installable': True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
