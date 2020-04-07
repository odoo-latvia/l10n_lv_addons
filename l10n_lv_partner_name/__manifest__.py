# -*- encoding: utf-8 -*-
##############################################################################
#
#    Part of Odoo.
#    Copyright (C) 2018 Allegro (<http://www.allegro.lv/>)
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
    'name': 'LV Partner name',
    'version': '1.0',
    'description': """
Partner seporate first and last name fields.
============================================

A partners surname is the last complete word. Multiple surnames can be
writen by delimiting them with a dash. "Berzins Priede" -> "Berzins-Priede".
The conversion is automatic when writen in the surname field.

First and middle names are seporated by a space 'Martins Juris Kristians'.


    """,
    'author': 'Allegro',
    'website': 'http://www.allegro.lv/',
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