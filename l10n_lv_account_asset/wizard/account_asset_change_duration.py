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
import time
import xml.etree.ElementTree as ET
import json

class asset_modify(osv.osv_memory):
    _inherit = 'asset.modify'

    def _get_asset_method_time_tax(self, cr, uid, ids, field_name, arg, context=None):
        if ids and len(ids) == 1 and context.get('active_id'):
            asset = self.pool['account.asset.asset'].browse(cr, uid, context.get('active_id'), context=context)
            return {ids[0]: asset.method_time_tax}
        else:
            return dict.fromkeys(ids, False)

    _columns = {
        'method_number_tax': fields.integer('Number of Depreciations (Tax)', required=True),
        'method_period_tax': fields.integer('Period Length (Tax)'),
        'method_end_tax': fields.date('Ending date (Tax)'),
        'asset_method_time_tax': fields.function(_get_asset_method_time_tax, type='char', string='Asset Method Time (Tax)', readonly=True),
    }

    def default_get(self, cr, uid, fields, context=None):
        if not context:
            context = {}
        res = super(asset_modify, self).default_get(cr, uid, fields, context=context)
        asset_obj = self.pool.get('account.asset.asset')
        asset_id = context.get('active_id', False)
        asset = asset_obj.browse(cr, uid, asset_id, context=context)
        if 'method_number_tax' in fields and asset.method_time_tax == 'number':
            res.update({'method_number_tax': asset.method_number_tax})
        if 'method_period_tax' in fields:
            res.update({'method_period_tax': asset.method_period_tax})
        if 'method_end_tax' in fields and asset.method_time_tax == 'end':
            res.update({'method_end_tax': asset.method_end_tax})
        if context.get('active_id'):
            res['asset_method_time_tax'] = self._get_asset_method_time_tax(cr, uid, [0], 'asset_method_time_tax', [], context=context)[0]
        return res

    def fields_view_get(self, cr, uid, view_id=None, view_type='tree', context=None, toolbar=False, submenu=False):
        if context is None:
            context = {}
        res = super(asset_modify,self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)
        def new_modifiers(node):
            attrs = node.get('attrs')
            attrs_dict = {}
            if attrs is not None:
                attrs_dict = eval(attrs)
            attrs_dict.update({'invisible': 1})
            modifiers = node.get('modifiers')
            modifiers_dict = {}
            if modifiers is not None:
                true = True
                false = False
                modifiers_dict = eval(modifiers)
            modifiers_dict.update({'invisible': 1})
            return attrs_dict, modifiers_dict
        if view_type == 'form':
            doc = ET.XML(res['arch'])
            node_mn = doc.find(".//field[@name='method_number']")
            if (node_mn is not None) and (context.get('tax',False) == True):
                attrs_dict, modifiers_dict = new_modifiers(node_mn)
                node_mn.set('attrs',str(attrs_dict))
                node_mn.set('modifiers',json.dumps(modifiers_dict))
            node_mnt = doc.find(".//field[@name='method_number_tax']")
            if (node_mnt is not None) and (context.get('tax',False) == False):
                attrs_dict, modifiers_dict = new_modifiers(node_mnt)
                node_mnt.set('attrs',str(attrs_dict))
                node_mnt.set('modifiers',json.dumps(modifiers_dict))
            node_me = doc.find(".//field[@name='method_end']")
            if (node_me is not None) and (context.get('tax',False) == True):
                attrs_dict, modifiers_dict = new_modifiers(node_me)
                node_me.set('attrs',str(attrs_dict))
                node_me.set('modifiers',json.dumps(modifiers_dict))
            node_met = doc.find(".//field[@name='method_end_tax']")
            if (node_met is not None) and (context.get('tax',False) == False):
                attrs_dict, modifiers_dict = new_modifiers(node_met)
                node_met.set('attrs',str(attrs_dict))
                node_met.set('modifiers',json.dumps(modifiers_dict))
            node_mp_label = doc.find(".//label[@for='method_period']")
            if (node_mp_label is not None) and (context.get('tax',False) == True):
                node_mp_label.set('attrs',str({'invisible': 1}))
                node_mp_label.set('modifiers',json.dumps({'invisible': 1}))
            node_mp_div = doc.findall(".//div")
            if (len(node_mp_div) != 0) and (context.get('tax',False) == True):
                node_mp_div[0].set('attrs',str({'invisible': 1}))
                node_mp_div[0].set('modifiers',json.dumps({'invisible': 1}))
            node_mpt_label = doc.find(".//label[@for='method_period_tax']")
            if (node_mpt_label is not None) and (context.get('tax',False) == False):
                node_mpt_label.set('attrs',str({'invisible': 1}))
                node_mpt_label.set('modifiers',json.dumps({'invisible': 1}))
            node_mpt_div = doc.findall(".//div")
            if (len(node_mpt_div) > 1) and (context.get('tax',False) == False):
                node_mpt_div[1].set('attrs',str({'invisible': 1}))
                node_mpt_div[1].set('modifiers',json.dumps({'invisible': 1}))
            res['arch'] = ET.tostring(doc, encoding='utf8', method='xml')
            print res['arch']
        return res

    def modify(self, cr, uid, ids, context=None):
        """ Modifies the duration of asset for calculating depreciation
        and maintains the history of old values.
        @param self: The object pointer.
        @param cr: A database cursor
        @param uid: ID of the user currently logged in
        @param ids: List of Ids 
        @param context: A standard dictionary 
        @return: Close the wizard. 
        """ 
        if not context:
            context = {}
        asset_obj = self.pool.get('account.asset.asset')
        history_obj = self.pool.get('account.asset.history')
        asset_id = context.get('active_id', False)
        asset = asset_obj.browse(cr, uid, asset_id, context=context)
        data = self.browse(cr, uid, ids[0], context=context)
        history_vals = {
            'asset_id': asset_id,
            'name': data.name,
            'method_time': asset.method_time,
            'method_number': asset.method_number,
            'method_period': asset.method_period,
            'method_end': asset.method_end,
            'user_id': uid,
            'date': time.strftime('%Y-%m-%d'),
            'note': data.note,
        }
        # ---- add tax vals:
        history_vals.update({
            'method_time_tax': asset.method_time_tax,
            'method_number_tax': asset.method_number_tax,
            'method_period_tax': asset.method_period_tax,
            'method_end_tax': asset.method_end_tax,
        })
        history_obj.create(cr, uid, history_vals, context=context)
        asset_vals = {
            'method_number': data.method_number,
            'method_period': data.method_period,
            'method_end': data.method_end,
        }
        # ---- add tax vals:
        asset_vals.update({
            'method_number_tax': data.method_number_tax,
            'method_period_tax': data.method_period_tax,
            'method_end_tax': data.method_end_tax
        })
        asset_obj.write(cr, uid, [asset_id], asset_vals, context=context)
        asset_obj.compute_depreciation_board(cr, uid, [asset_id], context=context)
        return {'type': 'ir.actions.act_window_close'}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: