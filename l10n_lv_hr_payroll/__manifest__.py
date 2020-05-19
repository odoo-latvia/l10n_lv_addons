# -*- encoding: utf-8 -*-
##############################################################################
#
#    Part of Odoo.
#    Copyright (C) 2020 Allegro IT (<http://www.allegro.lv/>)
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
    'name': 'Latvian Localization for Payroll',
    'version': '1.0',
    'description': """
Latvian Payroll
-------------------------
Adds Code field to Leave types.
Upgrades Employee onchange function, so that it:
* computes average salary for last 6 months (VDA6M) in Other Inputs;
* uses Leave Type Code in Worked Days.
Adds button "Reload Inputs" in Payslip form, which calls the same function as the Employee onchange function, so that, in case of data change, you don't have to edit the payslip and change employee again to see it.
    """,
    'author': 'Allegro IT',
    'website': 'http://www.allegro.lv',
    'category': 'Localization',
    'depends': ['hr_payroll'],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_payroll_views.xml',
#        'wizard/payslip_eds_export_view.xml',
        'wizard/relief_eds_import_view.xml'
    ],
    'auto_install': False,
    'installable': True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: