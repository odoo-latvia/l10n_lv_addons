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

from openerp.osv import fields, osv

class hr_config_settings(osv.osv_memory):
    _inherit = 'hr.config.settings'

    _columns = {
        'group_multiple_emp_id_vat': fields.boolean("Use Multiple Personal ID / TIN for Countries",
            implied_group='l10n_lv_hr.group_multiple_emp_id_vat',
            help="Allows you to use multiple Identification Numbers and TINs for Employees in different Countries."),
    }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: