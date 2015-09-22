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
from openerp.tools.translate import _

class account_move(osv.osv):
    _inherit = "account.move"

    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}
        if vals.get('date',False) and vals.get('period_id',False):
            period_obj = self.pool.get('account.period')
            period = period_obj.browse(cr, uid, vals['period_id'], context=context)
            if vals['date'] < period.date_start or vals['date'] > period.date_stop:
                ctx = context.copy()
                if vals.get('journal_id',False):
                    journal = self.pool.get('account.journal').browse(cr, uid, vals['journal_id'], context=context)
                    ctx.update({'company_id': journal.company_id.id})
                period_ids = period_obj.find(cr, uid, dt=vals['date'], context=context)
                if period_ids:
                    vals['period_id'] = period_ids[0]
        return super(account_move, self).create(cr, uid, vals, context=context)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: