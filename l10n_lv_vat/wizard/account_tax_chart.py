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

class account_tax_chart(osv.osv_memory):
    _inherit = "account.tax.chart"

    _columns = {
        'period_to_id': fields.many2one('account.period', 'Period To')
    }

    def account_tax_chart_open_window(self, cr, uid, ids, context=None):
        """
        Opens chart of Accounts
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param ids: List of account chart’s IDs
        @return: dictionary of Open account chart window on given fiscalyear and all Entries or posted entries
        """
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')
        if context is None:
            context = {}
        data = self.browse(cr, uid, ids, context=context)[0]
        result = mod_obj.get_object_reference(cr, uid, 'account', 'action_tax_code_tree')
        id = result and result[1] or False
        result = act_obj.read(cr, uid, [id], context=context)[0]
        if data.period_id:
            result['context'] = {'period_id': data.period_id.id, \
                                     'fiscalyear_id': data.period_id.fiscalyear_id.id, \
                                        'state': data.target_move}
            period_to_code = False
            if data.period_to_id:
                result['context'].update({'period_to_id': data.period_to_id.id})
                period_to_code = data.period_to_id.code
            result['context'] = str(result['context'])
            period_code = data.period_id.code
            name = period_code and (':' + period_code) or ''
            if period_to_code:
                name += (' - ' + period_to_code)
            result['name'] += (name != '') and (':' + name) or ''
        else:
            result['context'] = str({'state': data.target_move})

        return result

account_tax_chart()

class account_tax_code(osv.osv):
    _inherit = 'account.tax.code'

    def _sum_period(self, cr, uid, ids, name, args, context):
        if context is None:
            context = {}
        move_state = ('posted', )
        if context.get('state', False) == 'all':
            move_state = ('draft', 'posted', )
        if context.get('period_id', False) and context.get('period_to_id', False):
            period_ids = self.pool.get('account.period').build_ctx_periods(cr, uid, context['period_id'], context['period_to_id'])
            where = ' AND line.period_id IN %s AND move.state IN %s'
            where_params = (tuple(period_ids), move_state)
        elif context.get('period_id', False) and (not context.get('period_to_id', False)):
            period_id = context['period_id']
            where=' AND line.period_id=%s AND move.state IN %s'
            where_params = (period_id, move_state)
        else:
            ctx = dict(context, account_period_prefer_normal=True)
            period_id = self.pool.get('account.period').find(cr, uid, context=ctx)
            if not period_id:
                return dict.fromkeys(ids, 0.0)
            period_id = period_id[0]
            where=' AND line.period_id=%s AND move.state IN %s'
            where_params = (period_id, move_state)
        return self._sum(cr, uid, ids, name, args, context,
                where=where, where_params=where_params)

    _columns = {
        'sum_period': fields.function(_sum_period, string="Period Sum"),
    }

account_tax_code()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: