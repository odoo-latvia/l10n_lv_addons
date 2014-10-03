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

class document_page_create_menu(osv.osv_memory):
    _inherit = "document.page.create.menu"

    def document_page_menu_create(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        obj_page = self.pool.get('document.page')
        obj_view = self.pool.get('ir.ui.view')
        obj_menu = self.pool.get('ir.ui.menu')
        obj_action = self.pool.get('ir.actions.act_window')
        page_id = context.get('active_id', False)
        page = obj_page.browse(cr, uid, page_id, context=context)

        datas = self.browse(cr, uid, ids, context=context)
        data = False
        if datas:
            data = datas[0]
        if not data:
            return {}
        value = {
            'name': 'Document Page',
            'view_type': 'form',
            'view_mode': 'form,tree',
            'res_model': 'document.page',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'inlineview',
        }
        value['domain'] = "[('parent_id','=',%d)]" % (page.id)
        value['res_id'] = page.id

        action_id = obj_action.create(cr, uid, value)
        menu_id = obj_menu.create(cr, uid, {
                        'name': data.menu_name,
                        'parent_id':data.menu_parent_id.id,
                        'icon': 'STOCK_DIALOG_QUESTION',
                        'action': 'ir.actions.act_window,'+ str(action_id),
                        'groups_id': [g.id for g in page.group_ids]
                        }, context)
        obj_page.write(cr, uid, [page_id], {'menu_id':menu_id})
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: