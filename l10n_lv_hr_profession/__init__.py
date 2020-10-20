# -*- encoding: utf-8 -*-
##############################################################################
#
#    Part of Odoo.
#    Copyright (C) 2017 Allegro IT (<http://www.allegro.lv/>)
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

def post_init(cr, registry):
    from odoo.tools import convert_file
    profession_file = 'data/hr.profession.csv'
    convert_file(cr, 'l10n_lv_hr_profession', profession_file, None, mode='init', noupdate=True, kind='init')
    hazard_file = 'data/hr.job.hazard.csv'
    convert_file(cr, 'l10n_lv_hr_profession', hazard_file, None, mode='init', noupdate=True, kind='init')
    condition_file = 'data/hr.job.condition.csv'
    convert_file(cr, 'l10n_lv_hr_profession', condition_file, None, mode='init', noupdate=True, kind='init')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
