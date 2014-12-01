# -*- encoding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (c) 2008-2012 Alistek Ltd. (http://www.alistek.com)
#                       All Rights Reserved.
#                       General contacts <info@alistek.com>
#    Copyright (C) 2014 ITS-1 (<http://www.its1.lv/>)
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

from openerp.osv import osv, orm, fields
from openerp.tools.translate import _

from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from datetime import datetime
from dateutil.relativedelta import relativedelta
import math

from xml.dom import minidom
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
import base64

def get_package_drn_categ(self, cr, uid, context={}):
    obj = self.pool.get('product.category.drn')
    ids = obj.search(cr, uid, [])
    res = obj.read(cr, uid, ids, ['code', 'name'], context)
    return dict([(r['code'], r['name']) for r in res])

hazard_map_codes = {'lubri_weight':'1.',
                 'accu_lead_weight':'2.1',
                 'accu_nicd_weight':'2.2',
                 'accu_pri_weight':'2.3',
                 'accu_oth_weight':'2.4',
                 'tires_weight':'4',
                 'oil_filt_weight':'5',
                }

LR_PVN_1 = u'LR PVN maksātājs'
LR_PVN_2 = u'LR PVN nemaksātājs'

EU_PVN_1 = u'ES PVN maksātājs'
EU_PVN_2 = u'ES PVN nemaksātājs'
EU_OTHER = u'Partneri citas valstis'

class drn_return_wizard(osv.osv_memory):
    '''Natural Resources Tax Declaration'''
    _name = 'drn.return.wizard'
    _description = "Natural Resources Tax Declaration"

    _columns = {
        'name': fields.char('Description', size=256, required=True, help='Enter declaration description here'),
        'type_id': fields.many2one('sr.return_type', 'Type', domain="[('code_system','=','DRN_LV')]", ondelete='set null'),
        'performer': fields.many2one('res.users', 'Performer', ondelete='set null'),
        'responsible': fields.many2one('res.partner', 'Responsible', ondelete='set null'),
        'date_start': fields.date('Start of Period'),
        'date_stop': fields.date('End of Period'),
        'state': fields.selection([('draft','Draft'), ('error','Errors'), ('warning','Warning'), ('done','Done')], 'State'),
        'logs': fields.one2many('drn.return.log', 'drn_return_id', 'Logs'),
        'message': fields.text('Message'),
        'logs_history_warning2': fields.one2many('drn.return.log', 'drn_return_id', 'History warning2', readonly=True),
        'except_move_ids':fields.many2many('stock.move', 'drn_return_stock_move_except_rel', 'drn_return_id', 'stock_move_id', 'Except stock moves'),
        'excluded_move_ids':fields.many2many('stock.move', 'drn_return_stock_move_excluded_rel', 'drn_return_id', 'stock_move_id', 'Excluded stock moves'),
        'not_excluded_move_ids':fields.many2many('stock.move', 'drn_return_stock_move_not_excluded_rel', 'drn_return_id', 'stock_move_id', 'Not excluded stock moves'),
    }

    def _get_date_start(self, cr, uid, context={}):
        return (datetime.now() + relativedelta(months=-3, day=1)).strftime(DF)

    def _get_date_stop(self, cr, uid, context={}):
        return (datetime.now() + relativedelta(day=1, days=-1)).strftime(DF)

    def search_type(self, cr, uid, context):
        return_type_obj = self.pool.get('sr.return_type')
        return_type_ids = return_type_obj.search(cr,uid, [('code_system','=','DRN_LV')])
        res = return_type_ids and return_type_ids[0] or False
        return res

    _defaults = {
        'state': 'draft',
        'date_stop': _get_date_stop,
        'performer': lambda self,cr,uid,context:uid,
        'date_start': _get_date_start,
        'type_id': search_type,
    }

    def process_next(self, cr, uid, ids, context={}):
        pick_obj = self.pool.get('stock.picking')
        period_obj = self.pool.get('account.period')
        uom_obj = self.pool.get('product.uom')
        this = self.browse(cr, uid, ids[0], context=context)
        if not this.excluded_move_ids:
            warn2_log = filter(lambda l: l.type=='warning2', this.logs)
            except_moves1 = this.except_move_ids # before exclude excepted stock move
            except_moves2 = this.not_excluded_move_ids or set(map(lambda l: l.move_id, warn2_log)) # after exclude excepted stock move
            excluded_stock_move_ids = list(set(map(int, except_moves1)) - set(map(int, except_moves2))) # excluded stock move
            this.write({'excluded_move_ids':[(6,0,excluded_stock_move_ids)]})
            this.write({'not_excluded_move_ids':[(6,0,map(int, except_moves2))]})
        else:
            excluded_stock_move_ids = map(int, this.excluded_move_ids)
            except_moves2 = this.not_excluded_move_ids
        for log in this.logs:
            log.unlink()
        logging = context.get('logging')
        error_logs = []
        warning_logs = []
        picking_ids = pick_obj.search(cr, uid, [('picking_type_id.code','=','outgoing'), ('state','=','done')])
        pick_out_stock_move = []
        message = ''
        for picking in pick_obj.browse(cr, uid, picking_ids, context=context):
            pick_move_lines_done = filter(lambda ml: ml.state=='done' and ml.picking_id.partner_id and \
                    ml.picking_id.partner_id.property_account_position.name in (LR_PVN_1, LR_PVN_2) or \
                    not ml.picking_id.partner_id.property_account_position, picking.move_lines)
            pick_out_stock_move.extend(pick_move_lines_done)
            bad_move_lines = filter(lambda ml: not ml.picking_id.partner_id.property_account_position, pick_move_lines_done) # check Fiscal position for customer
            for bml in bad_move_lines:
                log_rec = (0,0,{'type':'error',
                                'name':bml.name,
                                'move_id':bml.id})
                if log_rec not in error_logs and this.state not in ('warning','warning2'):
                    error_logs.append(log_rec)

        logs = error_logs+warning_logs
        if logging and logs:
            message = _('STOCK MOVE ERROR[W03]: Fiscal position for customer is not set!')
            this.write({'state':'error','logs':logs,'message':message})
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'drn.return.wizard',
                'view_type': 'form',
                'res_id': this.id,
                'views': [(False,'form')],
                'target': 'new'
            }

        out_stock_move_none_in = []
        pick_in_stock_move_result = []
        for ml in pick_out_stock_move:
            if ml.id in excluded_stock_move_ids:
                continue
            if ml.product_id.type!='product':
                continue
            if ml.lot_ids:
                for prodlot in ml.lot_ids:
                    quant_ids = self.pool.get('stock.quant').search(cr, uid, [('lot_id','=',prodlot.id)], context=context)
                    if ml.state == 'done':
                        ml_ids = self.pool.get('stock.move').search(cr, uid, [('quant_ids','in',quant_ids)], context=context)
                    else:
                        ml_ids = self.pool.get('stock.move').search(cr, uid, [('reserved_quant_ids','in',quant_ids)], context=context)
                    prodlot_moves = [m for m in self.pool.get('stock_move').browse(cr, uid, ml_ids, context=context)]
                    pick_in_stock_move = filter(lambda ml: ml.picking_id and ml.picking_id.picking_type_id.code == 'incoming', prodlot_moves)
                    bad_move_lines = filter(lambda ml: not ml.picking_id.partner_id.property_account_position, pick_in_stock_move) # check Fiscal position for supplier
                    if this.state not in ('warning','warning2'):
                        for bml in bad_move_lines:
                            log_rec = (0,0,{'type':'error',
                                        'name':bml.name,
                                        'move_id':bml.id})
                            if log_rec not in error_logs:
                                error_logs.append(log_rec)
                    if not bad_move_lines:
                        in_lines = filter(lambda ml: ml.picking_id.partner_id.property_account_position.name in (EU_PVN_1, EU_PVN_2, EU_OTHER), pick_in_stock_move)
                        if not in_lines:
                            out_stock_move_none_in.append(ml)
                        else:
                            pick_in_stock_move_result.extend(in_lines)
            else:
                out_stock_move_none_in.append(ml)

        logs = error_logs+warning_logs
        if logging and logs:
            message = _('STOCK MOVE ERROR[W04]: Fiscal position for supplier is not set!')
            this.write({'state':'error','logs':logs,'message':message})
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'drn.return.wizard',
                'view_type': 'form',
                'res_id': this.id,
                'views': [(False,'form')],
                'target': 'new'
            }

        # production lot CHECKING
        if not this.except_move_ids:
            except_move_ids = []
            for ml in out_stock_move_none_in:
                log_rec = (0,0,{'type':'warning2',
                                'name':ml.name,
                                'move_id':ml.id})
                except_move_ids.append(ml.id)
                if log_rec not in warning_logs and this.state not in ('warning','warning2'):
                    warning_logs.append(log_rec)

            logs = error_logs+warning_logs
            if logging and logs:
                message = _('STOCK MOVE WARNING[W05]: Cannot determine the origin of goods in stock move(s)!')
                this.write({'state':'warning','logs':logs,'except_move_ids':[(6,0,except_move_ids)],'message':message})
                return {
                    'type': 'ir.actions.act_window',
                    'res_model': 'drn.return.wizard',
                    'view_type': 'form',
                    'res_id': this.id,
                    'views': [(False,'form')],
                    'target': 'new'
                }

        current_date = datetime.now().strftime("%Y-%m-%d")
        last_periods = period_obj.search(cr, uid, [('date_start','>=',this.date_start),('date_stop','<=',this.date_stop)], context=context)
        pkg_type_list_by_product = {}
        pkg_type_list_by_product_excepted = {}

        log_state = 'warning'
        for stock_move_list, excepted in [(set(except_moves2),True), (set(pick_in_stock_move_result),False)]:
            for ml in stock_move_list:
                move_lines_product_sec_pkg_count = 0.0
                primary_weight = 0.0
                secondary_weight = 0.0
                ml_period_ids = period_obj.find(cr, uid, ml.date, context=context)
                if ml_period_ids and ml_period_ids[0] not in last_periods or not ml_period_ids:
                    continue
                if excepted:
                    data_list = pkg_type_list_by_product_excepted
                else:
                    data_list = pkg_type_list_by_product
                if ml.product_id not in data_list:
                    pkg_type_list = {'primary':{}, 'secondary':{}, 'tertiary':{}, 'hazardous':{}, 'electronics':{}, 'product_qty':0, 'weight':0, 'weight_net':0}
                    data_list[ml.product_id] = pkg_type_list
                else:
                    pkg_type_list = data_list[ml.product_id]
                ##### Collect incoming stock move data by product #####
                pkg_type_list['product_qty'] += uom_obj._compute_price(cr, uid, ml.product_uom.id, ml.product_qty, ml.product_id.uom_id.id)
                pkg_type_list['weight'] += ml.weight
                pkg_type_list['weight_net'] += ml.weight_net
                #######################################################
                if logging:
                # product CHECKING
                    if ml.product_id.weight<=0.0:
                        log_state = 'error'
                        log_rec = (0,0,{'type':'error',
                                        'name':_('PRODUCT ERROR[E01]: Gross weight of product "[%s] %s" cannot be less or equal than 0!') % (ml.product_id.code,ml.product_id.name),
                                        'product_id':ml.product_id.id})
                        if log_rec not in error_logs:
                            error_logs.append(log_rec)
                    if ml.product_id.weight_net<=0.0:
                        log_state = 'error'
                        log_rec = (0,0,{'type':'error',
                                        'name':_('PRODUCT ERROR[E02]: Net weight of product "[%s] %s" cannot be less or equal than 0!') % (ml.product_id.code,ml.product_id.name),
                                        'product_id':ml.product_id.id})
                        if log_rec not in error_logs:
                            error_logs.append(log_rec)
                    if filter(lambda pack: pack.weight <= 0, ml.product_id.packaging_ids):
                        log_state = 'error'
                        log_rec = (0,0,{'type':'error',
                                        'name':_('PRODUCT PACK ERROR[E03]: Secondary package(s) defined for product "[%s] %s" has weight less or equal than 0!') % (ml.product_id.code,ml.product_id.name),
                                        'product_id':ml.product_id.id})
                        if log_rec not in error_logs:
                            error_logs.append(log_rec)
                    if filter(lambda pack: not pack.drn_cat_id and pack.weight > 0, ml.product_id.packaging_ids):
                        log_state = 'error'
                        log_rec = (0,0,{'type':'error',
                                        'name':_('PRODUCT PACK ERROR[E04]: NRT Category is not defined for package included in product "[%s] %s"!') % (ml.product_id.code,ml.product_id.name),
                                        'product_id':ml.product_id.id})
                        if log_rec not in error_logs:
                            error_logs.append(log_rec)
                # stock move CHECKING
                    if ml.cmr_package_drn_categ and ml.cmr_package_drn_categ.code!='NO' and ml.cmr_line_weight<=0.0:
                        log_state = 'error'
                        log_rec = (0,0,{'type':'error',
                                        'name':_('STOCK MOVE ERROR[E05]: CMR Package weight of picking line "%s" cannot be less or equal than 0!') % (ml.name),
                                        'move_id':ml.id})
                        if log_rec not in error_logs:
                            error_logs.append(log_rec)
                    if ml.cmr_line_weight<0: # CMR Package Weight CHECKING
                        log_state = 'error'
                        log_rec = (0,0,{'type':'error',
                                        'name':_('STOCK MOVE ERROR[E07]: weight of picking line "%s" is negative!') % ml.name,
                                        'move_id':ml.id})
                        if log_rec not in error_logs:
                            error_logs.append(log_rec)
                # primary calculation
                group_key = ml.product_id.drn_prod_pack_categ_id or ml.product_id.categ_id.drn_product_pack_category
                if logging and not group_key: # product DRN category CHECKING
                    log_state = 'error'
                    log_rec = (0,0,{'type':'error',
                                    'name':_('PRODUCT PACK ERROR[E08]: Primary package for NRT in product \"[%s] %s\" is not defined!') % (ml.product_id.code,ml.product_id.name),
                                    'product_id':ml.product_id.id})
                    if log_rec not in error_logs:
                        error_logs.append(log_rec)
                primary_weight_by_group = (ml.product_id.weight - ml.product_id.weight_net) * ml.product_qty
                if primary_weight_by_group<0.0:
                    log_state = 'error'
                    log_rec = (0,0,{'type':'error',
                                    'name':_('PRODUCT ERROR[E09]: Product "[%s] %s" primary package gross weight can not be negative!') % (ml.product_id.code,ml.product_id.name),
                                    'product_id':ml.product_id.id})
                    if log_rec not in error_logs:
                        error_logs.append(log_rec)
                elif primary_weight_by_group==0.0:
                    log_rec = (0,0,{'type':'warning',
                                    'name':_('PRODUCT WARN[W01]: Product "[%s] %s" primary package gross weight is zero!') % (ml.product_id.code,ml.product_id.name),
                                    'product_id':ml.product_id.id})
                    if log_rec not in warning_logs:
                        warning_logs.append(log_rec)
                primary_weight = ml.product_id.weight * ml.product_qty
                # electronics calculation  
                if ml.product_id.is_eei == True or ml.product_id.categ_id.is_eei == True:
                      group_key = ml.product_id.drn_prod_categ_id or ml.product_id.categ_id.drn_product_category
                if logging and (ml.product_id.is_eei == True) and not group_key: # product DRN category CHECKING
                    log_state = 'error'
                    log_rec = (0,0,{'type':'error',
                                    'name':_('PRODUCT ERROR[E10]: EEI Product Category for NRT in product "[%s] %s" is not defined!') % (ml.product_id.code,ml.product_id.name),
                                    'product_id':ml.product_id.id})
                    if log_rec not in error_logs:
                        error_logs.append(log_rec)
                hazard_weight = sum([
                         ml.product_id.lubri_weight,
                         ml.product_id.accu_lead_weight,
                         ml.product_id.accu_nicd_weight,
                         ml.product_id.accu_oth_weight,
                         ml.product_id.accu_pri_weight,
                         ml.product_id.tires_weight,
                         ml.product_id.oil_filt_weight
                        ])
                #weight = ml.product_id.weight * ml.product_qty
                if logging and ml.product_id.weight < hazard_weight: # product total weight and hazard weight CHECKING
                    log_state = 'error'
                    log_rec = (0,0,{'type':'error',
                                    'name':_('PRODUCT ERROR[E11]: Product "[%s] %s" total weight is less than weight of his hazardous components!') % (ml.product_id.code,ml.product_id.name),
                                    'product_id':ml.product_id.id})
                    if log_rec not in error_logs:
                        error_logs.append(log_rec)
                for pkg in ml.product_id.packaging:
                    if logging and pkg.drn_cat_id and pkg.qty <= 0: # product secondary weight CHECKING
                        log_state = 'error'
                        log_rec = (0,0,{'type':'error',
                                        'name':_('PRODUCT PACK ERROR[E12]: Product "[%s] %s" has secondary package defined, but product qty in secondary package is 0 or less!') % (ml.product_id.code,ml.product_id.name),
                                        'product_id':ml.product_id.id})
                        if log_rec not in error_logs:
                            error_logs.append(log_rec)            
                    group_key = pkg.qty!=0 and pkg.drn_cat_id or False
                    if group_key:
                        if group_key not in pkg_type_list['secondary']:
                            pkg_type_list['secondary'][group_key] = (math.ceil(ml.product_qty / pkg.qty) * pkg.weight_ul)
                        else:
                            pkg_type_list['secondary'][group_key] += (math.ceil(ml.product_qty / pkg.qty) * pkg.weight_ul)
                        secondary_weight += pkg_type_list['secondary'][group_key]
                # tertiary calculation
                if not excepted:
                    if ml.cmr_line_weight>0:
                        group_key = ml.cmr_package_drn_categ or ml.product_id.categ_id.drn_product_category or False
                        tertiary_weight = ml.cmr_line_weight - sum(map(lambda l: l.weight, ml.picking_id.move_lines))
                        if group_key not in pkg_type_list['tertiary']:
                            pkg_type_list['tertiary'][group_key] = tertiary_weight
                        else:
                            pkg_type_list['tertiary'][group_key] += tertiary_weight
                        if logging and tertiary_weight and tertiary_weight <= 0: # product tertiar weight CHECKING
                            log_state = 'error'
                            log_rec = (0,0,{'type':'error',
                                            'name':_('MOVE ERROR[E13]: Product "[%s] %s" transport package in CMR less than should be according to calculation!') % (ml.product_id.code,ml.product_id.name),
                                            'move_id':ml.id})
                            if log_rec not in error_logs:
                                error_logs.append(log_rec)
                            warning_logs.append(log_rec)
                    if ml.add_drn_package_weight > 0:
                        group_key = ml.add_drn_package_cat
                        if group_key not in pkg_type_list['tertiary']:
                            pkg_type_list['tertiary'][group_key] = ml.add_drn_package_weight
                        else:
                            pkg_type_list['tertiary'][group_key] += ml.add_drn_package_weight
        logs = error_logs+warning_logs
        if logging and logs and this.state != 'warning2':
            if log_state=='warning':
                log_state='warning2'
            this.write({'state':log_state,'logs':logs,'message':message})
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'drn.return.wizard',
                'view_type': 'form',
                'res_id': this.id,
                'views': [(False,'form')],
                'target': 'new'
            }

        out_ml_by_product = {}
        for out_ml in pick_out_stock_move: # group out stock move lines by product
            if out_ml.id in excluded_stock_move_ids:
                continue
            if out_ml.product_id not in out_ml_by_product:
                out_ml_by_product[out_ml.product_id] = [out_ml]
            else:
                out_ml_by_product[out_ml.product_id].append(out_ml)

        res = []
        for data_list, excepted in [(pkg_type_list_by_product,False), (pkg_type_list_by_product_excepted,True)]:
            for p in data_list: # go by product
                data = data_list[p]
                res_data = {'primary':{},'electronics':{},'secondary':{},'hazardous':{},'tertiary':{}}
                out_qty = sum(map(lambda a: uom_obj._compute_price(cr, uid, a.product_uom.id, a.product_qty, a.product_id.uom_id.id), out_ml_by_product[p]))
                # primary calculation
                if excepted:
                    primary_weight_by_group = data['weight'] - data['weight_net']
                else:
                    primary_weight_by_group = (data['weight'] - data['weight_net']) / data['product_qty'] * out_qty
                group_key_primary = p.drn_prod_pack_categ_id or p.categ_id.drn_product_pack_category or False
                if primary_weight_by_group>0.0:
                    res_data['primary'][group_key_primary] = primary_weight_by_group

                # electronics calculation
                if p.is_eei == True or p.categ_id.is_eei == True:
                    hazard_weight = sum([
                             p.lubri_weight,
                             p.accu_lead_weight,
                             p.accu_nicd_weight,
                             p.accu_oth_weight,
                             p.accu_pri_weight,
                             p.tires_weight,
                             p.oil_filt_weight
                            ])
                    group_key_electronics = p.drn_prod_categ_id or p.categ_id.drn_product_category or False
                    weight_sum = sum(map(lambda ml: ml.weight_net - hazard_weight * ml.product_qty, out_ml_by_product[p]))
                    quantity_sum = sum(map(lambda ml: ml.product_qty, out_ml_by_product[p]))
                    res_data['electronics'][group_key_electronics] = {
                        'weight':weight_sum,
                        'quantity':quantity_sum,
                    }
                # secondary calculation
                for pkg in p.packaging:
                    group_key_secondary = pkg.qty!=0 and pkg.drn_cat_id or False
                    if group_key_secondary:
                        if excepted:
                            secondary_weight = math.ceil(data['product_qty'] / pkg.qty) * pkg.weight_ul
                        else:
                            secondary_weight = (math.ceil(data['product_qty'] / pkg.qty) * pkg.weight_ul) / data['product_qty'] * out_qty
                        res_data['secondary'][group_key_secondary] = secondary_weight
                # hazardous calculation
                for group_key_hazardous in ['lubri_weight','accu_lead_weight','accu_nicd_weight'\
                                    ,'accu_pri_weight','accu_oth_weight','tires_weight','oil_filt_weight']:
                    weight = getattr(p, group_key_hazardous)
                    if weight>0:
                        res_data['hazardous'][group_key_hazardous] = weight * (excepted and data['product_qty'] or out_qty)
                if not excepted:
                    # tertiary calculation
                    for group_key_tertiary in data['tertiary']:
                        res_data['tertiary'][group_key_tertiary] = data['tertiary'][group_key_tertiary] / data['product_qty'] * out_qty

                res.append(res_data)

        return self.make_xml(cr, uid, this, res, context=context)

    def make_xml(self, cr, uid, this, data, context={}):
        xmldoc = minidom.Document()
        rootNode = xmldoc.createElement('DRN_REPORTv1')
        categ_nodes = {}
        xmldoc.appendChild(rootNode)

        if this.performer:
            employee_obj = self.pool.get('hr.employee')
            employee_id = employee_obj.search(cr, uid, [('user_id','=',this.performer.id)], context=context)
            if employee_id:
                performer = employee_obj.read(cr, uid, employee_id[0], ['name'], context=context)['name']
            else:
                performer = ''
        else:
            performer = ''
        node = xmldoc.createElement('PERFORMER')
        textNode=xmldoc.createTextNode(performer)
        node.appendChild(textNode)
        rootNode.appendChild(node)

        if this.responsible:
            respons = self.pool.get('res.partner').browse(cr, uid, this.responsible.id, context=context)
            respons_name = respons.name
        else:
            respons_name = ''
        node = xmldoc.createElement('RESPONSIBLE')
        textNode=xmldoc.createTextNode(respons_name)
        node.appendChild(textNode)
        rootNode.appendChild(node)

        period_ids = self.pool.get('account.period').search(cr, uid, [('date_start','>=',this.date_start),('date_start','<=',this.date_stop)], context=context)
        period = self.pool.get('account.period').browse(cr, uid, period_ids[-1], context=context)
        node = xmldoc.createElement('YEAR')
        textNode=xmldoc.createTextNode(period.fiscalyear_id.code)
        node.appendChild(textNode)
        rootNode.appendChild(node)

        node = xmldoc.createElement('PERIOD')
        quartal = datetime.strptime(period.date_stop, '%Y-%m-%d').month / 3
        textNode=xmldoc.createTextNode(str(quartal))
        node.appendChild(textNode)
        rootNode.appendChild(node)

        categ_nodes['hazard'] = xmldoc.createElement('HAZARD')
        rootNode.appendChild(categ_nodes['hazard'])
        categ_nodes['packaging'] = xmldoc.createElement('PACKAGING')
        rootNode.appendChild(categ_nodes['packaging'])
        hazard_groups = {'lubri_weight':0.0,
                         'accu_lead_weight':0.0,
                         'accu_nicd_weight':0.0,
                         'accu_pri_weight':0.0,
                         'accu_oth_weight':0.0,
                         'tires_weight':0.0,
                         'oil_filt_weight':0.0,
                        }
        categ_nodes['electronics'] = xmldoc.createElement('ELECTRONICS')
        rootNode.appendChild(categ_nodes['electronics'])

        results = {'hazard':hazard_groups,'packaging':{},'electronics':{}}
        total_electr_sum = 0.0
        total_pack_sum = 0.0
        total_hazard_sum = 0.0
        for pkg in data:
            hazard = pkg.get('hazardous', {})
            for group in hazard:
                results['hazard'][group] += hazard[group]
                total_hazard_sum += hazard[group]
            electronics = pkg.get('electronics', {})
            for group in electronics:
                if group and group.code=='NO': # not the subject of reports
                    continue
                sum_val = electronics[group]['weight']
                qty = electronics[group]['quantity']
                if group and group not in results['electronics']:
                    results['electronics'][group.code] = {'sum':sum_val,'children':[],'qty':qty}
                    parent = group.parent_id
                    if parent:
                        if parent.code not in results['electronics']:
                            results['electronics'][parent.code] = {'sum':sum_val,'children':[(group.code,results['electronics'][group.code])],'qty':qty}
                        else:
                            results['electronics'][parent.code]['children'].append((group.code,results['electronics'][group.code]))
                            results['electronics'][parent.code]['sum'] += sum_val
                            results['electronics'][parent.code]['qty'] += qty
                        del results['electronics'][group.code]
                else:
                    if group:
                        results['electronics'][group.code]['sum'] += sum_val
                total_electr_sum += sum_val
            primary = pkg.get('primary', {})
            secondary = pkg.get('secondary', {})
            tertiary = pkg.get('tertiary', {})
            group_keys = set(primary.keys()+secondary.keys()+tertiary.keys())
            for group in group_keys:
                if any([primary.has_key(group), secondary.has_key(group), tertiary.has_key(group)]):
                    primary_val = primary.get(group, 0.0)
                    secondary_val = secondary.get(group, 0.0)
                    tertiary_val = tertiary.get(group, 0.0) 
                    sum_val = primary_val+secondary_val+tertiary_val

                    if group.code not in results['packaging']:
                        if group.code=='NO': # not the subject of reports
                            continue
                        results['packaging'][group.code] = {'sum':sum_val,'children':[]}
                        parent = group.parent_id
                        if parent:
                            if parent.code not in results['packaging']:
                                results['packaging'][parent.code] = {'sum':sum_val,'children':[(group.code,results['packaging'][group.code])]}
                            else:
                                results['packaging'][parent.code]['children'].append((group.code,results['packaging'][group.code]))
                                results['packaging'][parent.code]['sum'] += sum_val
                            del results['packaging'][group.code]
                    else:
                        results['packaging'][group.code]['sum'] += sum_val
                    total_pack_sum += sum_val
            categ_nodes['hazard'].setAttribute('total_sum', str(total_hazard_sum))
            categ_nodes['electronics'].setAttribute('total_sum', str(total_electr_sum))
            categ_nodes['packaging'].setAttribute('total_sum', str(total_pack_sum))

        if results['hazard']:
            hazard_labels = self.pool.get('product.product').fields_get(cr, uid, hazard_groups.keys(), context=context) # hazard group is fields connected with hazardous, so is group names is field labels
        drn_categ_labels = get_package_drn_categ(self, cr, uid, context=context)
        for res in results:
            curr_categ_node = categ_nodes[res]
            groups = results[res].keys()
            groups.sort()
            for group in groups:
                group_node = xmldoc.createElement('GROUP')
                if res=='hazard':
                    group_node.setAttribute('name', hazard_map_codes[group])
                    sum_val = results[res][group]
                    if not sum_val:
                        continue
                    group_node.setAttribute('string', hazard_labels[group]['string'])
                    children = False
                else:
                    group_node.setAttribute('name', group)
                    group_node.setAttribute('string', drn_categ_labels[group])
                    sum_val = results[res][group]['sum']
                    children = results[res][group].get('children',[])
                    children.sort()
                    qty = results[res][group].get('qty')
                    if qty:
                        group_node.setAttribute('quantity', str(int(qty)))
                group_node.setAttribute('sum', str(sum_val))
                if children:
                    prep = {}
                    for child in children:
                        if prep.has_key(child[0]):
                            prep[child[0]]['sum'] += child[1]['sum']
                            if 'qty' in prep[child[0]]:
                                prep[child[0]]['qty'] += child[1].get('qty')
                            prep[child[0]]['children'] += child[1]['children']
                        else:
                            prep[child[0]] = {'sum':child[1]['sum'], 'children':child[1]['children']}
                            if 'qty' in child[1]:
                                prep[child[0]]['qty'] = child[1]['qty']
                    children_node = xmldoc.createElement('SUBGROUPS')
                    group_node.appendChild(children_node)
                    for child in prep:
                        child_group_node = xmldoc.createElement('SUBGROUP')
                        child_group_node.setAttribute('name', child)
                        child_group_node.setAttribute('string', drn_categ_labels[child])
                        sum_val = prep[child]['sum'] #results[res][child]['sum']
                        child_group_node.setAttribute('sum', str(sum_val))
                        child_qty = prep[child].get('qty')
                        if child_qty:
                            child_group_node.setAttribute('quantity', str(int(child_qty)))
                        children_node.appendChild(child_group_node)

                curr_categ_node.appendChild(group_node)

        xml_file = base64.encodestring(xmldoc.toprettyxml())
        return_id = self.pool.get('sr.return').create(cr, uid, {
            'name':this.name+' '+this.date_start+' - '+this.date_stop,
            'type_id':this.type_id.id,
            'data_xml':xml_file,
            'date_start':this.date_start,
            'date_stop':this.date_stop,
        })

        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')
        ref = mod_obj.get_object_reference(cr, uid, 'base_returns', 'action_view_sr_return')
        id = ref and ref[1] or False

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sr.return',
            'view_type': 'form',
            'res_id': return_id,
            'views': [(False,'form')],
            'nodestroy': True
        }

class drn_return_log(osv.osv_memory):
    _name = 'drn.return.log'
    _rec_name = 'type'

    _columns = {
        'type': fields.selection([('error', 'Error'), ('warning','Warning'), ('warning2','Warning')], 'Type', size=64, required=True, readonly=True),
        'name': fields.text('Message'),
        'drn_return_id': fields.many2one('drn.return.wizard', 'NRT return', ondelete='set null'),
        'product_id': fields.many2one('product.product', 'Product', ondelete='set null'),
        'move_id': fields.many2one('stock.move', 'Stock Move', ondelete='set null')
    }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: