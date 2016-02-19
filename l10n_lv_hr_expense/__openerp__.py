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
    'name': 'LV Expense Management',
    'version': '1.0',
    'description': """
Accounting improvements for expenses.
=====================================
Partner in expenses and journal items created from the corresponding expense.
Report for Expenses in PDF.
    """,
    'author': 'ITS-1',
    'website': 'http://www.its1.lv/',
    'category': 'Human Resources',
    'depends': ['hr_expense', 'l10n_lv_verbose'],
    'demo_xml': [],
    'data': [
        'views/hr_expense_view.xml',
        'views/hr_expense_report.xml',
        'wizard/hr_expense_account_report_view.xml'
    ],
    'auto_install': False,
    'installable': True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: