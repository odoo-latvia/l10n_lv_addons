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
    'name': 'Latvia - Accounting Invoice',
    'version': '1.1',
    'category': 'Localization',
    'summary': 'Adds invoice report with signatures',
    'description': """
    Adds invoice report with signatures
    """,
    'author': 'Ozols Grupa',
    'website': 'http://www.ozols.lv',
    'depends': [
        'account',
        'l10n_lv_partner_data'
    ],
    'data': [
        'views/tax_group_view.xml',
        'reports/report_invoice.xml'
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'qweb': [],
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
