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

class document_page(osv.osv):
    _inherit = "document.page"
    _order = "write_date desc"

    _columns = {
        'group_ids': fields.many2many('res.groups', 'page_group_rel', 'page_id', 'group_id', 'Groups')
    }

    def write(self, cr, uid, ids, vals, context=None):
        result = super(document_page, self).write(cr, uid, ids, vals, context)
        if vals.get('group_ids',False):
            p_ids = self.search(cr, uid, [('id','in',ids)], context=context)
            for p in self.browse(cr, uid, p_ids, context=context):
                if p.menu_id:
                    p.menu_id.write({'groups_id': [[6, 0, [g.id for g in p.group_ids]]]})
                if p.child_ids:
                    self.write(cr, uid, [c.id for c in p.child_ids], {'group_ids': [[6, 0, [g.id for g in p.group_ids]]]}, context=context)
        return result

    def onchange_parent_id(self, cr, uid, ids, parent_id, content, context=None):
        res = {}
        if parent_id and not content:
            parent = self.browse(cr, uid, parent_id, context=context)
            if parent.type == "category":
                res['value'] = {
                    'content': parent.content,
                    'group_ids': [g.id for g in parent.group_ids]
                }
        return res

document_page()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: