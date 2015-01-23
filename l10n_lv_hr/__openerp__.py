# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012 ITS-1 (<http://www.its1.lv/>)
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
    'name': 'Latvia - Employee Directory',
    'version': '1.0',
    'description': """
Latvian localisation for hr and hr_contract modules.
=====================================
Field Home Address changed to Declared Address.

New field Residence Address added.

All address fields changed to res.partner.address.

New fields for passport added: Passport Issue Date and Passport Expiration Date.

New fields for Additional Information added: Contract, Contract Start Date and Introductory Done

Separate fields for employee name and surname.

Section (tab) for employees CV text.

Addtional fields for Contracts: Main Duties, Additional Duties, Other Terms.

Report for Contracts: Employee Contract - prints out a contract to sign. (Needs upgrading from Webkit to QWeb.)

Removes User simple view, so that new users (with default name) can be created from employees.

Looks for Employees with the same Name field in the system when creating/updating an Employee. If such Employees are found, the corresponding Employee cannot be created/updated.

Adds a User access rights group 'HR Reader' which can access all HR documents in readonly mode.
Adds a User access rights group 'HR Instructor' for Introductory Done field.

Adds a Code field to HR Departments, which is used also in the name_get() methos of the corresponding object.

HR Job: only active Employees in count fields.

Adds 3 new fields in Company form view: 'Responsible Person', 'Position of Responsible Person', 'Justification of Act of the Responsible Person' for Contract report.

Multy-company rule for Employees and Company filter for Empoloyees and contracts.

Configuration: Multiple Identification Numbers and TINs for Employee in different countries.

Fix for button viewing in Employee form view.

Company field visible in Job form view; Job menu in HR Configuration.
    """,
    'author': 'ITS-1',
    'website': 'http://www.its1.lv/',
    'category': 'Localization/Human Resources',
    'depends': ['hr_contract', 'l10n_lv_partner_address'],
    'demo_xml': [],
    'update_xml': [
        'security/hr_security.xml',
        'security/ir.model.access.csv',
        'res_company_view.xml',
        'hr_view.xml',
        'views/employee_contract_report.xml',
        'hr_report.xml',
        'res_config_view.xml'
    ],
    'auto_install': False,
    'installable': True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
