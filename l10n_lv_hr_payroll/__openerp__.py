# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 ITS-1 (<http://www.its1.lv/>)
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
    'name': 'Latvia - HR Payroll',
    'version': '1.0',
    'description': """
Latvian Payroll
-------------------------
Upgrades Payslip Details report.
Adds Disability group in Employee form.
Adds Code field to Leave types.
Upgrades Employee on_change function, so that it:
* computes average salary for last 6 months (VDA6M) in Other Inputs;
* uses Leave Type Code in Worked Days;
* puts number of dependent persons (APG) in Other Inputs (from Employee children);
* computes number of calendar days absent (KAL) in Other Inputs.
Adds button "Reload Inputs" in Payslip form, which calls the Employee on_change function, so that, in case of data change, you don't have to edit the payslip and change employee again to see it.
Adds a new report - Payslip Summary.
    """,
    'author': 'ITS-1',
    'website': 'http://www.its1.lv/',
    'category': 'Human Resources',
    'depends': ['hr_payroll'],
    'data': [
        'security/hr_payroll_security.xml',
        'security/ir.model.access.csv',
        'hr_payroll_view.xml',
        'views/report_payslip_summary.xml',
        'hr_payroll_report.xml'
    ],
    'auto_install': False,
    'installable': True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: