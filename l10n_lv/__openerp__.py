# -*- encoding: utf-8 -*-
##############################################################################
#
#    Part of Odoo.
#    Copyright (C) 2016 ITS-1 (<http://www.its1.lv/>)
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
    'name': 'Latvia - Accounting',
    'version': '1.0',
    'description': """
Latvian Accounting
-------------------------

This is the base module for Latvian localization of :

* Account Codes
* Chart of Accounts
* Tax Codes
* Chart of Taxes
* Fiscal Positions
    """,
    'author': 'ITS-1',
    'website': 'http://www.its1.lv/',
    'category': 'Localization/Account Charts',
    'depends': ['account', 'base_vat', 'base_iban'],
    'data': [
        'data/res_company.xml',
        'data/account_account_type.xml',
        'data/account_account_tag.xml',
        'data/account_chart_template.xml',
        'data/account_account_template.xml',
        'data/account_tax_template.xml',
        'data/account_fiscal_position_template.xml'
    ],
    'auto_install': False,
    'installable': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: