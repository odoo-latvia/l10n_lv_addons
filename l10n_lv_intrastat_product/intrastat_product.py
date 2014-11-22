# -*- encoding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2010-2011 Akretion (http://www.akretion.com). All Rights Reserved
#    @author Alexis de Lattre <alexis.delattre@akretion.com>
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
import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
import openerp.addons.decimal_precision as dp
from xml.dom import minidom
import base64
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

def createTextNode(xmldoc, pointer, nodeName, value):
    el = xmldoc.createElement(nodeName)
    pointer.appendChild(el)
    textNode=xmldoc.createTextNode(value)
    pointer.lastChild.appendChild(textNode)
    return pointer

intrastat_code_map = {
    'import_detailed':'Ievedums-1B', # A-J columns in report
    'import_simplified':'Ievedums-1A', # A-G columns in report
    'export_detailed':'Izvedums-2B', # A-I columns in report
    'export_simplified':'Izvedums-2A', # A-F columns in report
}

intrastat_columns_map = {
    'import_detailed':['A','B','C','D','E','F','G','H','I','J'], # 1B
    'import_simplified':['A','B','C','D','E','F','G'], # 1A
    'export_detailed':['A','B','C','D','E','F','G','H','I'], # 2B
    'export_simplified':['A','B','C','D','E','F'], # 2A
}

class report_instrastat_product_xml(osv.osv):
    _name = 'report.intrastat.product.xml'
    _description = 'Intrastat report for products in with XML representation'
    
    _columns = {
        'name':fields.char('Description', size=256, required=True, readonly=False),
        'filename':fields.char('Filename', size=64, required=True, readonly=True),
        'data_xml':fields.binary('Data', filters='*.xml', help="Intrastat report XML representation"),
        'company_id':fields.many2one('res.company', 'Company', help="Company, the report belongs to.",required=True),
        'type': fields.selection([
                ('import', 'Import'),
                ('export', 'Export')
            ], 'Type', required=True),
        'report_id': fields.many2one('report.intrastat.product', 'Report')
        
    }

class report_intrastat_product(osv.osv):
    _name = "report.intrastat.product"
    _description = "Intrastat report for products"
    _rec_name = "start_date"
    _order = "start_date desc, type"

    def _compute_end_date(self, cr, uid, ids, name, arg, context=None):
        result = {}
        for intrastat in self.browse(cr, uid, ids, context=context):
            start_date_datetime = datetime.strptime(intrastat.start_date, '%Y-%m-%d')
            end_date_str = datetime.strftime(start_date_datetime + relativedelta(day=31), '%Y-%m-%d')
            result[intrastat.id] = end_date_str
        return result

    def _compute_numbers(self, cr, uid, ids, name, arg, context=None):
        result = {}
        for intrastat in self.browse(cr, uid, ids, context=context):
            total_amount = 0.0
            num_lines = 0
            for line in intrastat.intrastat_line_ids:
                total_amount += line.amount_company_currency
                num_lines += 1
            result[intrastat.id] = {
                'num_lines': num_lines,
                'total_amount': total_amount,
            }
        return result

    def _compute_total_fiscal_amount(self, cr, uid, ids, name, arg, context=None):
        result = {}
        for intrastat in self.browse(cr, uid, ids, context=context):
            total_fiscal_amount = 0.0
            for line in intrastat.intrastat_line_ids:
                total_fiscal_amount += line.amount_company_currency
            result[intrastat.id] = total_fiscal_amount
        return result

    def _xml_count(self, cr, uid, ids, name, arg, context=None):
        result = {}
        for intrastat in self.browse(cr, uid, ids, context=context):
            xml_ids = self.pool.get('report.intrastat.product.xml').search(cr, uid, [('report_id','=',intrastat.id)], context=context)
            result[intrastat.id] = len(xml_ids)
        return result

    def _get_intrastat_from_product_line(self, cr, uid, ids, context=None):
        return self.pool.get('report.intrastat.product').search(cr, uid, [('intrastat_line_ids', 'in', ids)], context=context)

    _columns = {
        'company_id': fields.many2one('res.company', 'Company', required=True,
            states={'done':[('readonly',True)]}, help="Related company."),
        'start_date': fields.date('Start date', required=True,
            states={'done':[('readonly',True)]},
            help="Start date of the declaration. Must be the first day of a month."),
        'end_date': fields.function(_compute_end_date, method=True, type='date',
            string='End date', store={
                'report.intrastat.product': (lambda self, cr, uid, ids, c={}: ids, ['start_date'], 10),
                },
            help="End date for the declaration. Is the last day of the month of the start date."),
        'type': fields.selection([
                ('import', 'Import'),
                ('export', 'Export')
            ], 'Type', required=True, states={'done':[('readonly',True)]},
            help="Select the type of Intrastat."),
        'obligation_level': fields.selection([
                ('detailed', 'Intrastat-1B/2B'),
                ('simplified', 'Intrastat-1A/2A')
            ], 'CBS defined limiting values for a reporting year', required=True,
            states={'done':[('readonly',True)]},
            help="Your obligation level for a certain type of Intrastat (Import or Export) depends on the total value that you export or import per year."),
        'intrastat_line_ids': fields.one2many('report.intrastat.product.line',
            'parent_id', 'Report intrastat product lines',
            states={'done':[('readonly',True)]}),
        'num_lines': fields.function(_compute_numbers, method=True, type='integer',
            multi='numbers', string='Number of lines', store={
                'report.intrastat.product.line': (_get_intrastat_from_product_line, ['parent_id'], 20),
            },
            help="Number of lines in this declaration."),
        'total_amount': fields.function(_compute_numbers, method=True,
            digits_compute=dp.get_precision('Account'), multi='numbers',
            string='Total amount', store={
                'report.intrastat.product.line': (_get_intrastat_from_product_line, ['amount_company_currency', 'parent_id'], 20),
            },
            help="Total amount in company currency of the declaration."),
        'total_fiscal_amount': fields.function(_compute_total_fiscal_amount,
            method=True, digits_compute=dp.get_precision('Account'),
            string='Total fiscal amount', store={
                'report.intrastat.product.line': (_get_intrastat_from_product_line, ['amount_company_currency', 'parent_id'], 20),
            },
            help="Total fiscal amount in company currency of the declaration."),
        'currency_id': fields.related('company_id', 'currency_id', readonly=True,
            type='many2one', relation='res.currency', string='Currency'),
        'state': fields.selection([
                ('draft','Draft'),
                ('done','Done'),
            ], 'State', select=True, readonly=True,
            help="State of the declaration. When the state is set to 'Done', the parameters become read-only."),
        'date_done': fields.datetime('Date done', readonly=True,
            help="Last date when the intrastat declaration was converted to 'Done' state."),
        'notes' : fields.text('Notes',
            help="You can add some comments here if you want."),
        'xml_count': fields.function(_xml_count, type="integer", string="XML File Count")
    }

    _defaults = {
        # By default, we propose 'current month -1', because you prepare in
        # February the Intrastat of January
        'start_date': lambda *a: datetime.strftime(datetime.today() + relativedelta(day=1, months=-1), '%Y-%m-%d'),
        'state': lambda *a: 'draft',
        'company_id': lambda self, cr, uid, context: \
        self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id,
    }

    def type_on_change(self, cr, uid, ids, company_id=False, type=False):
        result = {}
        result['value'] = {}
        if type and company_id:
            if type == 'import':
                company = self.pool.get('res.company').read(cr, uid, company_id, ['import_obligation_level'])
                if company['import_obligation_level']:
                    result['value'].update({'obligation_level': company['import_obligation_level']}) 
            if type == 'export':
                company = self.pool.get('res.company').read(cr, uid, company_id, ['export_obligation_level'])
                if company['export_obligation_level']:
                    result['value'].update({'obligation_level': company['export_obligation_level']})
        return result

    def onchange_start_date(self, cr, uid, ids, start_date, context=None):
        res = {}
        if start_date:
            start_date_datetime = datetime.strptime(start_date, '%Y-%m-%d')
            end_date_str = datetime.strftime(start_date_datetime + relativedelta(day=31), '%Y-%m-%d')
            res = {'value': {'end_date': end_date_str}}
        return res

    def _check_start_date(self, cr, uid, ids, context=None):
        '''Check that the start date is the first day of the month'''
        for date_to_check in self.read(cr, uid, ids, ['start_date'], context=context):
            datetime_to_check = datetime.strptime(date_to_check['start_date'], '%Y-%m-%d')
            if datetime_to_check.day != 1:
                return False
        return True

    _constraints = [
        (_check_start_date, "Start date must be the first day of a month", ['start_date']),
    ]

    _sql_constraints = [
        ('date_uniq', 'unique(start_date, company_id, type)', 'A Intrastat of the same type already exists for this month !'),
    ]

    # ---------------LINE-GENERATION---------------

    def remove_intrastat_product_lines(self, cr, uid, ids, field, context=None):
        '''Get current lines that were generated from invoices/picking and delete them'''
        line_obj = self.pool.get('report.intrastat.product.line')
        line_remove_ids = line_obj.search(cr, uid, [('parent_id', 'in', ids), (field, '!=', False)], context=context)
        if line_remove_ids:
            line_obj.unlink(cr, uid, line_remove_ids, context=context)
        return True


    def common_compute_invoice_picking(self, cr, uid, intrastat, parent_obj, parent_values, context=None):
        intrastat_type = self.pool.get('report.intrastat.type').read(cr, uid, parent_values['intrastat_type_id_to_write'], context=context)
        parent_values['transaction_code_to_write'] = intrastat_type['transaction_code']
        if parent_obj._name == 'account.invoice':
            src = 'invoice'
            parent_name = parent_obj.number
        elif parent_obj._name == 'stock.picking':
            src = 'picking'
            parent_name = parent_obj.name
        else: raise osv.except_osv(_('Error :'), 'The function build_intrastat_product_lines() should have parent_obj as invoice or picking')
        if not parent_obj.intrastat_transport:
            if not intrastat.company_id.default_intrastat_transport:
                raise osv.except_osv(_('Error :'), _("The mode of transport is not set on %s '%s' nor the default mode of transport on the company '%s'.") %(src, parent_name, intrastat.company_id.name))
            else:
                parent_values['transport_to_write'] = intrastat.company_id.default_intrastat_transport
        else:
            parent_values['transport_to_write'] = parent_obj.intrastat_transport
        return parent_values


    def _get_id_from_xmlid(self, cr, uid, module, xml_id, model_name, context=None):
        irdata_obj = self.pool.get('ir.model.data')
        res = irdata_obj.get_object_reference(cr, uid, module, xml_id)
        if res[0] == model_name:
            res_id = res[1]
        else:
            raise osv.except_osv(_('Error :'), 'ID for XML-ID "%s" not found!' % xml_id)
        return res_id


    def create_intrastat_product_lines(self, cr, uid, ids, intrastat, parent_obj, parent_values, context=None):
        """This function is called for each invoice and for each picking"""

        if len(ids) != 1: raise osv.except_osv(_('Error :'), 'Lines should be generated for one document at a time.')
        line_obj = self.pool.get('report.intrastat.product.line')

        weight_uom_categ_id = self._get_id_from_xmlid(cr, uid, 'product', 'product_uom_categ_kgm', 'product.uom.categ', context=context)

        kg_uom_id = self._get_id_from_xmlid(cr, uid, 'product', 'product_uom_kgm', 'product.uom', context=context)

        pce_uom_categ_id = self._get_id_from_xmlid(cr, uid, 'product', 'product_uom_categ_unit', 'product.uom.categ', context=context)

        pce_uom_id = self._get_id_from_xmlid(cr, uid, 'product', 'product_uom_unit', 'product.uom', context=context)

        if parent_obj._name == 'account.invoice':
            src = 'invoice'
            browse_on = parent_obj.invoice_line
            parent_name = parent_obj.number
            product_line_ref_field = 'invoice_id'
            currency_obj = parent_obj.currency_id
        elif parent_obj._name == 'stock.picking':
            src = 'picking'
            browse_on = parent_obj.move_lines
            parent_name = parent_obj.name
            product_line_ref_field = 'picking_id'
            currency_obj = intrastat.company_id.statistical_pricelist_id.currency_id
        else: raise osv.except_osv(_('Error :'), 'The function build_intrastat_product_lines() should have parent_obj as invoice or picking')

        lines_to_create = []
        total_invoice_cur_accessory_cost = 0.0
        total_invoice_cur_product_value = 0.0
        for line in browse_on:
            if src == 'invoice':
                line_qty = line.quantity
                source_uom = line.uos_id
            elif src == 'picking':
                line_qty = line.product_qty
                source_uom = line.product_uom

            # We don't do anything when there is no product_id...
            # this may be a problem... but i think a raise would be too violent
            if not line.product_id:
                continue

            if line.product_id.exclude_from_intrastat:
                continue

            if not line_qty:
                continue

            # If type = "service" and is_accessory_cost=True, then we keep
            # the line (it will be skipped later on)
            if line.product_id.type not in ('product', 'consu') and not line.product_id.is_accessory_cost:
                continue

            if src == 'picking':
                if line.state <> 'done':
                    continue
                if parent_obj.picking_type_id.code == 'incoming' and line.location_dest_id.usage <> 'internal':
                    continue
                if parent_obj.picking_type_id.code == 'outgoing' and line.location_dest_id.usage == 'internal':
                    continue

            if src == 'invoice':
                skip_this_line = False
                for line_tax in line.invoice_line_tax_id:
                    if line_tax.exclude_from_intrastat_if_present:
                        skip_this_line = True
                if skip_this_line:
                    continue
                if line.product_id.is_accessory_cost and line.product_id.type == 'service':
                    total_invoice_cur_accessory_cost += line.price_subtotal
                    continue
                # END OF "continue" instructions
                ## AFTER THIS POINT, we are sure to have real products that have to be declared to Intrastat
                amount_product_value_inv_cur_to_write = line.price_subtotal
                total_invoice_cur_product_value += line.price_subtotal
                invoice_currency_id_to_write = currency_obj.id

            elif src == 'picking':
                invoice_currency_id_to_write = currency_obj.id
                unit_stat_price = self.pool.get('product.pricelist').price_get(cr, uid, [intrastat.company_id.statistical_pricelist_id.id], line.product_id.id, 1.0)[intrastat.company_id.statistical_pricelist_id.id]
                if not unit_stat_price:
                    raise osv.except_osv(_('Error :'), _("The Pricelist for statistical value '%s' that is set for the company '%s' gives a price of 0 for the product '%s'.") %(intrastat.company_id.statistical_pricelist_id.name, intrastat.company_id.name, line.product_id.name))
                else:
                    amount_product_value_inv_cur_to_write = unit_stat_price * line_qty

            if not source_uom:
                raise osv.except_osv(_('Error :'), _("Missing unit of measure on the line with %d product(s) '%s' on %s '%s'.") %(line_qty, line.product_id.name, src, parent_name))
            else:
                source_uom_id_to_write = source_uom.id

            if source_uom.id == kg_uom_id:
                weight_to_write = line_qty
            elif source_uom.category_id.id == weight_uom_categ_id:
                dest_uom_kg = self.pool.get('product.uom').browse(cr, uid,
                    kg_uom_id, context=context)
                weight_to_write = self.pool.get('product.uom')._compute_qty_obj(cr, uid,
                    source_uom, line_qty, dest_uom_kg, context=context)
            elif source_uom.category_id.id == pce_uom_categ_id:
                if not line.product_id.weight_net:
                    raise osv.except_osv(_('Error :'), _("Missing net weight on product '%s'.") %(line.product_id.name))
                if source_uom.id == pce_uom_id:
                    weight_to_write = line.product_id.weight_net * line_qty
                else:
                    dest_uom_pce = self.pool.get('product.uom').browse(cr, uid,
                        pce_uom_id, context=context)
                    # Here, I suppose that, on the product, the weight is per PCE and not per uom_id
                    weight_to_write = line.product_id.weight_net * self.pool.get('product.uom')._compute_qty_obj(cr, uid, source_uom, line_qty, dest_uom_pce, context=context)

            else:
                raise osv.except_osv(_('Error :'), _("Conversion from unit of measure '%s' to 'Kg' is not implemented yet.") %(source_uom.name))

            product_intrastat_code = line.product_id.intrastat_id
            if not product_intrastat_code:
                # If the H.S. code is not set on the product, we check if it's set
                # on it's related category
                product_intrastat_code = line.product_id.categ_id.intrastat_id
                if not product_intrastat_code:
                    raise osv.except_osv(_('Error :'), _("Missing H.S. code on product '%s' or on it's related category '%s'.") %(line.product_id.name, line.product_id.categ_id.complete_name))
            intrastat_code_id_to_write = product_intrastat_code.id

            if not product_intrastat_code.intrastat_code:
                raise osv.except_osv(_('Error :'), _("Missing intrastat code on H.S. code '%s' (%s).") %(product_intrastat_code.name, product_intrastat_code.description))
            else:
                intrastat_code_to_write = product_intrastat_code.intrastat_code

            if not product_intrastat_code.intrastat_uom_id:
                intrastat_uom_id_to_write = False
                quantity_to_write = False
            else:
                intrastat_uom_id_to_write = product_intrastat_code.intrastat_uom_id.id
                if intrastat_uom_id_to_write == source_uom_id_to_write:
                    quantity_to_write = line_qty
                elif source_uom.category_id == product_intrastat_code.intrastat_uom_id.category_id:
                    quantity_to_write = self.pool.get('product.uom')._compute_qty_obj(cr,
                        uid, source_uom, line_qty,
                        product_intrastat_code.intrastat_uom_id, context=context)
                else:
                    raise osv.except_osv(_('Error :'), _("On %s '%s', the line with product '%s' has a unit of measure (%s) which can't be converted to UoM of it's intrastat code (%s).") %(src, parent_name, line.product_id.name, source_uom_id_to_write, intrastat_uom_id_to_write))

            # The origin country should only be declated on Import
            if intrastat.type == 'export':
                product_country_origin_id_to_write = False
            elif line.product_id.country_id:
            # If we have the country of origin on the product -> take it
                product_country_origin_id_to_write = line.product_id.country_id.id
            else:
                # If we don't, look on the product supplier info
                # We only have parent_values['origin_partner_id'] when src = invoice
                origin_partner_id = parent_values.get('origin_partner_id', False)
                if origin_partner_id:
                    supplieri_obj = self.pool.get('product.supplierinfo')
                    supplier_ids = supplieri_obj.search(cr, uid, [
                        ('name', '=', origin_partner_id),
                        ('product_tmpl_id', '=', line.product_id.product_tmpl_id.id),
                        ('origin_country_id', '!=', 'null')
                        ], context=context)
                    if not supplier_ids:
                        raise osv.except_osv(_('Error :'),
                            _("Missing country of origin on product '%s' or on it's supplier information for partner '%s'.")
                            %(line.product_id.name, parent_values.get('origin_partner_name', 'none')))
                    else:
                        product_country_origin_id_to_write = supplieri_obj.read(cr, uid,
                            supplier_ids[0], ['origin_country_id'],
                            context=context)['origin_country_id'][0]
                else:
                    raise osv.except_osv(_('Error :'),
                        _("Missing country of origin on product '%s' (it's not possible to get the country of origin from the 'supplier information' in this case because we don't know the supplier of this product for the %s '%s').")
                        %(line.product_id.name, src, parent_name))

            create_new_line = True
            for line_to_create in lines_to_create:
                if line_to_create.get('intrastat_code_id', False) == intrastat_code_id_to_write \
                    and line_to_create.get('source_uom_id', False) == source_uom_id_to_write \
                    and line_to_create.get('intrastat_type_id', False) == parent_values['intrastat_type_id_to_write'] \
                    and line_to_create.get('product_country_origin_id', False) == product_country_origin_id_to_write:
                    create_new_line = False
                    line_to_create['quantity'] += quantity_to_write
                    line_to_create['weight'] += weight_to_write
                    line_to_create['amount_product_value_inv_cur'] += amount_product_value_inv_cur_to_write
                    break
            incoterm_code = ''
            if hasattr(parent_obj, 'incoterm') and parent_obj.incoterm:
                if isinstance(parent_obj.incoterm, str) or isinstance(parent_obj.incoterm, unicode):
                    incoterm_code = parent_obj.incoterm
                else:
                    incoterm_code = parent_obj.incoterm.code
            if hasattr(parent_obj, 'incoterm_id') and parent_obj.incoterm_id:
                incoterm_code = parent_obj.incoterm_id.code
            if create_new_line == True:
                lines_to_create.append({
                    'parent_id': ids[0],
                    product_line_ref_field: parent_obj.id,
                    'quantity': quantity_to_write,
                    'source_uom_id': source_uom_id_to_write,
                    'intrastat_uom_id': intrastat_uom_id_to_write,
                    'partner_country_id': parent_values['partner_country_id_to_write'],
                    'intrastat_code': intrastat_code_to_write,
                    'intrastat_code_id': intrastat_code_id_to_write,
                    'weight': weight_to_write,
                    'product_country_origin_id': product_country_origin_id_to_write,
                    'transport': parent_values['transport_to_write'],
                    'intrastat_type_id': parent_values['intrastat_type_id_to_write'],
                    'transaction_code': parent_values['transaction_code_to_write'],
                    'partner_id': parent_values['partner_id_to_write'],
                    'invoice_currency_id': invoice_currency_id_to_write,
                    'amount_product_value_inv_cur': amount_product_value_inv_cur_to_write,
                    'incoterm_code': incoterm_code,
                })
        # End of the loop on invoice/picking lines

        for line_to_create in lines_to_create:
            if src == 'picking':
                context['date'] = parent_obj.date_done # for currency conversion
                line_to_create['amount_accessory_cost_inv_cur'] = 0
            elif src == 'invoice':
                context['date'] = parent_obj.date_invoice # for currency conversion
                if not total_invoice_cur_accessory_cost:
                    line_to_create['amount_accessory_cost_inv_cur'] = 0
                else:
                    # The accessory costs are added at the pro-rata of value
                    line_to_create['amount_accessory_cost_inv_cur'] = total_invoice_cur_accessory_cost * line_to_create['amount_product_value_inv_cur'] / total_invoice_cur_product_value

            line_to_create['amount_invoice_currency'] = line_to_create['amount_product_value_inv_cur'] + line_to_create['amount_accessory_cost_inv_cur']

            # We do currency conversion NOW
            if currency_obj.id != intrastat.company_id.currency_id.id:
                line_to_create['amount_company_currency'] = self.pool.get('res.currency').compute(cr, uid, currency_obj.id, intrastat.company_id.currency_id.id, line_to_create['amount_invoice_currency'], context=context)
            else:
                line_to_create['amount_company_currency'] = line_to_create['amount_invoice_currency']
            # We round
            line_to_create['amount_company_currency'] = int(round(line_to_create['amount_company_currency']))
            if line_to_create['amount_company_currency'] == 0:
                # p20 of the BOD : lines with value rounded to 0 mustn't be declared
                continue
            for value in ['quantity', 'weight']: # These 2 fields are char
                if line_to_create[value]:
                    line_to_create[value] = str(int(round(line_to_create[value], 0)))
            line_obj.create(cr, uid, line_to_create, context=context)

        return True

    def _check_generate_lines(self, cr, uid, intrastat, context=None):
        if not intrastat.company_id.country_id:
            raise orm.except_orm(
                _('Error :'),
                _("The country is not set on the company '%s'.")
                % intrastat.company_id.name)
        if not intrastat.currency_id.name == 'EUR':
            raise orm.except_orm(
                _('Error :'),
                _("The company currency must be 'EUR', but is currently '%s'.")
                % intrastat.currency_id.name)
        return True

    # ---------------LINE-GENERATION-BUTTON-INVOICE---------------

    def generate_product_lines_from_invoice(self, cr, uid, ids, context=None):
        intrastat = self.browse(cr, uid, ids[0], context=context)
        self._check_generate_lines(cr, uid, intrastat, context=context)
        self.remove_intrastat_product_lines(cr, uid, ids, 'invoice_id', context=context)

        invoice_obj = self.pool.get('account.invoice')
        invoice_type = False
        if intrastat.type == 'import':
            # Les régularisations commerciales à l'HA ne sont PAS
            # déclarées dans la DEB, cf page 50 du BOD 6883 du 06 janvier 2011
            invoice_type = ('in_invoice', 'POUET') # I need 'POUET' to make it a tuple
        invoice_ids = invoice_obj.search(cr, uid, [
            ('type', 'in', invoice_type),
            ('date_invoice', '<=', intrastat.end_date),
            ('date_invoice', '>=', intrastat.start_date),
            ('state', 'in', ('open', 'paid')),
            ('company_id', '=', intrastat.company_id.id)
        ], order='date_invoice', context=context)
        if intrastat.type == 'export':
            invoice_type = ('out_invoice', 'out_refund')
        invoice_ids = invoice_obj.search(cr, uid, [
            ('type', 'in', invoice_type),
            ('date_invoice', '<=', intrastat.end_date),
            ('date_invoice', '>=', intrastat.start_date),
            ('state', 'in', ('open', 'paid')),
            ('company_id', '=', intrastat.company_id.id)
        ], order='date_invoice', context=context)
        for invoice in invoice_obj.browse(cr, uid, invoice_ids, context=context):
            parent_values = {}

            # We should always have a country on partner_id
            if not invoice.partner_id.country_id:
                raise osv.except_osv(_('Error :'), _("Missing country on partner's '%s' address.") %(invoice.partner_id.name))

            # If I have no invoice.intrastat_country_id, which is the case the first month
            # of the deployment of the module, then I use the country on invoice address
            if not invoice.intrastat_country_id:
                if not invoice.partner_id.country_id.intrastat:
                    continue
                else:
                    parent_values['partner_country_id_to_write'] = invoice.partner_id.country_id.id

            # If I have invoice.intrastat_country_id, which should be the case after the
            # first month of use of the module, then I use invoice.intrastat_country_id
            else:
                if not invoice.intrastat_country_id.intrastat:
                    continue
                else:
                    parent_values['partner_country_id_to_write'] = invoice.intrastat_country_id.id
            if not invoice.intrastat_type_id:
                if invoice.type == 'out_invoice':
                    if intrastat.company_id.default_intrastat_type_out_invoice:
                        parent_values['intrastat_type_id_to_write'] = intrastat.company_id.default_intrastat_type_out_invoice.id
                    else:
                        raise osv.except_osv(_('Error :'), _("The intrastat type hasn't been set on invoice '%s' and the 'default intrastat type for customer invoice' is missing for the company '%s'.") %(invoice.number, intrastat.company_id.name))
                elif invoice.type == 'out_refund':
                    if intrastat.company_id.default_intrastat_type_out_refund:
                        parent_values['intrastat_type_id_to_write'] = intrastat.company_id.default_intrastat_type_out_refund.id
                    else:
                        raise osv.except_osv(_('Error :'), _("The intrastat type hasn't been set on refund '%s' and the 'default intrastat type for customer refund' is missing for the company '%s'.") %(invoice.number, intrastat.company_id.name))
                elif invoice.type == 'in_invoice':
                    if intrastat.company_id.default_intrastat_type_in_invoice:
                        parent_values['intrastat_type_id_to_write'] = intrastat.company_id.default_intrastat_type_in_invoice.id
                    else:
                        raise osv.except_osv(_('Error :'), _("The intrastat type hasn't been set on invoice '%s' and the 'Default intrastat type for supplier invoice' is missing for the company '%s'.") %(invoice.number, intrastat.company_id.name))
                else: raise osv.except_osv(_('Error :'), "Hara kiri... we can't have a supplier refund")

            else:
                parent_values['intrastat_type_id_to_write'] = invoice.intrastat_type_id.id

            if invoice.intrastat_country_id and not invoice.partner_id.country_id.intrastat and invoice.partner_id.intrastat_fiscal_representative:
                # fiscal rep
                parent_values['partner_id_to_write'] = invoice.partner_id.intrastat_fiscal_representative.id
            else:
                parent_values['partner_id_to_write'] = invoice.partner_id.id

            # Get partner on which we will check the 'country of origin' on product_supplierinfo
            parent_values['origin_partner_id'] = invoice.partner_id.id
            parent_values['origin_partner_name'] = invoice.partner_id.name

            parent_values = self.common_compute_invoice_picking(cr, uid, intrastat, invoice, parent_values, context=context)

            if intrastat.type == 'export' and invoice.intrastat_country_id.code == 'LV':
                continue
            elif intrastat.type == 'import' and invoice.intrastat_country_id.code == 'LV':
                continue
            else:
                self.create_intrastat_product_lines(cr, uid, ids, intrastat, invoice, parent_values, context=context)

        return True

    # ---------------LINE-GENERATION-BUTTON-PICKING---------------

    def generate_product_lines_from_picking(self, cr, uid, ids, context=None):
        '''Function used to have the Intrastat lines corresponding to repairs'''
        intrastat = self.browse(cr, uid, ids[0], context=context)
        self._check_generate_lines(cr, uid, intrastat, context=context)
        # not needed when type = export and oblig_level = simplified, cf p26 du BOD
        if intrastat.type == 'export' and intrastat.obligation_level == 'simplified':
            raise osv.except_osv(_('Error :'), _("You don't need to get lines from picking for an export Intrastat in 'Intrastat-1A/2A' obligation level."))

        # Remove existing lines
        self.remove_intrastat_product_lines(cr, uid, ids, 'picking_id', context=context)

        # Check pricelist for stat value
        if not intrastat.company_id.statistical_pricelist_id:
            raise osv.except_osv(_('Error :'), _("You must select a 'Pricelist for statistical value' for the company %s.") %intrastat.company_id.name)

        pick_obj = self.pool.get('stock.picking')
        pick_type = False
        if intrastat.type == 'import':
            pick_type = 'incoming'
        if intrastat.type == 'export':
            pick_type = 'outgoing'
        pick_type_ids = self.pool.get('stock.picking.type').search(cr, uid, [('code','=',pick_type)], context=context)
        picking_ids = pick_obj.search(cr, uid, [
            ('picking_type_id', 'in', pick_type_ids),
            ('date_done', '<=', intrastat.end_date),
            ('date_done', '>=', intrastat.start_date),
            ('invoice_state', '=', 'none'),
            ('company_id', '=', intrastat.company_id.id),
            ('state', 'not in', ('draft', 'waiting', 'confirmed', 'assigned', 'cancel'))
        ], order='date_done', context=context)
        for picking in pick_obj.browse(cr, uid, picking_ids, context=context):
            saleorder_ids = self.pool['sale.order'].search(cr, uid, [('procurement_group_id' ,'=', picking.group_id.id)], context=context)
            purchaseline_ids = []
            for sm in picking.move_lines:
                if sm.purchase_line_id:
                    purchaseline_ids.append(sm.purchase_line_id.id)
            if saleorder_ids or purchaseline_ids:
                continue
            parent_values = {}
            if not picking.partner_id:
                continue

            if not picking.partner_id.country_id:
                raise osv.except_osv(_('Error :'), _("Missing country in partner's '%s' address used on picking '%s'.") %(picking.partner_id.name, picking.name))
            elif not picking.partner_id.country_id.intrastat:
                continue
            else:
                parent_values['partner_country_id_to_write'] = picking.partner_id.country_id.id
                parent_values['partner_id_to_write'] = picking.partner_id.id

            # TODO : check = 29 /19 ???
            if not picking.intrastat_type_id:
                if picking.picking_type_id.code == 'outgoing':
                    if intrastat.company_id.default_intrastat_type_out_picking:
                        parent_values['intrastat_type_id_to_write'] = intrastat.company_id.default_intrastat_type_out_picking.id
                    else:
                        raise osv.except_osv(_('Error :'), _("The intrastat type hasn't been set on picking '%s' and the 'default intrastat type for outgoing products' is missing for the company '%s'.") %(picking.name, intrastat.company_id.name))
                elif picking.picking_type_id.code == 'incoming':
                    if intrastat.company_id.default_intrastat_type_in_picking:
                        parent_values['intrastat_type_id_to_write'] = intrastat.company_id.default_intrastat_type_in_picking.id
                    else:
                        raise osv.except_osv(_('Error :'), _("The intrastat type hasn't been set on picking '%s' and the 'default intrastat type for incoming products' is missing for the company '%s'.") %(picking.name, intrastat.company_id.name))
                else:
                    continue
            else:
                parent_values['intrastat_type_id_to_write'] = picking.intrastat_type_id.id


            parent_values = self.common_compute_invoice_picking(cr, uid, intrastat, picking, parent_values, context=context)

            self.create_intrastat_product_lines(cr, uid, ids, intrastat, picking, parent_values, context=context)

        return True

    # ---------------XML-GENERATION---------------

    def _form_address(self, cr, uid, partner, context=None):
        if context is None:
            context = {}
        addr_list = []
        if partner.street:
            addr_list.append(partner.street)
        if partner.street2:
            addr_list.append(partner.street2)
        if partner.city:
            addr_list.append(partner.city)
        if partner.state_id:
            addr_list.append(partner.state_id.name)
        if partner.zip:
            addr_list.append(partner.zip)
        if partner.country_id:
            addr_list.append(partner.country_id.name)
        address = ''
        c = 0
        for addr in addr_list:
            c += 1
            address += addr
            if c != len(addr_list):
                address += ', '
        return address

    def generate_xml(self, cr, uid, ids, context={}):
        def create_cell(xmldoc, pointer, column, value, sheet_number, row_number):
            cell_value_node = xmldoc.createElement("CellValue")
            pointer.appendChild(cell_value_node)
            pointer = pointer.lastChild
            pointer = createTextNode(xmldoc, pointer, "RowNumber", "1")
            pointer = createTextNode(xmldoc, pointer, "ColumnNumber", column)
            pointer = createTextNode(xmldoc, pointer, "Value", value)
            pointer = createTextNode(xmldoc, pointer, "Code", "%%0%sd/%%0%sd" % (3, 2) % (sheet_number, row_number))
            return pointer

        ROW_COUNT_ON_SHEET = 15
        start_time = time.time()
        this = self.browse(cr, uid, ids[0], context=context)
        xmldoc = minidom.Document()
        rootNode = xmldoc.createElement('Survey')
        rootNode.setAttribute("xmlns","https://eparskats.csb.gov.lv/eSurvey/XMLSchemas/Survey/v1-0")
        rootNode.setAttribute("xmlns:xsi","http://www.w3.org/2001/XMLSchema-instance")
        rootNode.setAttribute("xsi:schemaLocation","https://eparskats.csb.gov.lv/eSurvey/XMLSchemas/Survey/v1-0 Survey.xsd")
        xmldoc.appendChild(rootNode)
        ##### Set Respondent Info #####
        respNode = xmldoc.createElement('RespondentInfo')
        rootNode.appendChild(respNode)
        currNode = respNode

        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        company = user.company_id
        currNode = createTextNode(xmldoc, currNode, "RegistrationNumber", (company.partner_id.ref or ''))
        currNode = createTextNode(xmldoc, currNode, "Name", company.name[:200])

        legal_address = self._form_address(cr, uid, company.partner_id, context=context)
        currNode = createTextNode(xmldoc, currNode, "LegalAddress", legal_address)

        contact = company.partner_id
        if company.partner_id.child_ids and len(company.partner_id.child_ids) == 1:
            contact = company.partner_id.child_ids[0]
        contact_address = self._form_address(cr, uid, contact, context=context)
        currNode = createTextNode(xmldoc, currNode, "ContactAddress", contact_address)
        currNode = contact.phone and createTextNode(xmldoc, currNode, "Phone", contact.phone) or currNode
        currNode = contact.fax and createTextNode(xmldoc, currNode, "Fax", contact.fax) or currNode
        currNode =  contact.email and createTextNode(xmldoc, currNode, "Email", contact.email) or currNode
        employee_id = self.pool.get('hr.employee').search(cr, uid, [('user_id','=',uid),('company_id','=',company.id)], context=context)
        if employee_id:
            employee = self.pool.get('hr.employee').browse(cr, uid, employee_id[0], context=context)
            submitter = xmldoc.createElement("Submitter")
            currNode.appendChild(submitter)
            currNode = currNode.lastChild
            currNode = createTextNode(xmldoc, currNode, "FirstName", employee.name)
            currNode = createTextNode(xmldoc, currNode, "LastName", employee.name)
            currNode = employee.work_phone and createTextNode(xmldoc, currNode, "Phone", employee.work_phone) or currNode
            currNode = employee.work_email and createTextNode(xmldoc, currNode, "Email", employee.work_email) or currNode
        ########## Set Survey Info ##########
        currNode = rootNode
        survey_info_node = xmldoc.createElement("SurveyInfo")
        currNode.appendChild(survey_info_node)
        currNode = currNode.lastChild
        obligation_level = dict(self.fields_get(cr, uid, allfields=['obligation_level'], context=context)['obligation_level']['selection']).get(this.obligation_level)
        currNode = createTextNode(xmldoc, currNode, "Code", intrastat_code_map.get(this.type+'_'+this.obligation_level))
        pariod_node = xmldoc.createElement("Period")
        currNode.appendChild(pariod_node)
        currNode = currNode.lastChild
        date_struct = time.strptime(this.start_date, '%Y-%m-%d')
        currNode = createTextNode(xmldoc, currNode, "Year", str(date_struct.tm_year))
        currNode = createTextNode(xmldoc, currNode, "Month", 'M%%0%sd' % 2 % date_struct.tm_mon)
        #####################################
        currNode = rootNode
        value_list_node = xmldoc.createElement("CellValueList")
        currNode.appendChild(value_list_node)
        currNode = currNode.lastChild
        sheet_number = 1
        row_number = 1
        for line in this.intrastat_line_ids:
            if row_number>ROW_COUNT_ON_SHEET:
                sheet_number += 1
                row_number = 1

            if this.type=='export':
                if this.obligation_level=='simplified':
                    e_value = line.partner_country_id.code
                    f_value = line.transaction_code        
                    g_value = False
                    h_value = False
                    i_value = False
                    j_value = False
                elif this.obligation_level=='detailed':
                    e_value = line.partner_country_id.code
                    f_value = line.transaction_code
                    g_value = str(line.transport)
                    h_value = line.incoterm_code
                    i_value = str(int(line.amount_company_currency))
                    j_value = False
            elif this.type=='import':
                if this.obligation_level=='simplified':
                    e_value = line.partner_country_id.code
                    f_value = line.product_country_origin_id.code
                    g_value = line.transaction_code
                    h_value = False
                    i_value = False
                    j_value = False
                elif this.obligation_level=='detailed':
                    e_value = line.partner_country_id.code
                    f_value = line.product_country_origin_id.code
                    g_value = line.transaction_code
                    h_value = str(line.transport)
                    i_value = line.incoterm_code
                    j_value = str(int(line.amount_company_currency))

            processed_cells = intrastat_columns_map.get(this.type+'_'+this.obligation_level,[])
            if "A" in processed_cells:
                create_cell(xmldoc, value_list_node, "A", line.intrastat_code, sheet_number, row_number)
            if "B" in processed_cells:
                create_cell(xmldoc, value_list_node, "B", str(int(line.amount_product_value_inv_cur)), sheet_number, row_number)
            if "C" in processed_cells:
                create_cell(xmldoc, value_list_node, "C", line.weight or '0', sheet_number, row_number)
            if "D" in processed_cells:
                pass
            if "E" in processed_cells and e_value:
                create_cell(xmldoc, value_list_node, "E", e_value, sheet_number, row_number)
            if "F" in processed_cells and f_value:
                create_cell(xmldoc, value_list_node, "F", f_value, sheet_number, row_number)
            if "G" in processed_cells and g_value:
                create_cell(xmldoc, value_list_node, "G", g_value, sheet_number, row_number)
            if "H" in processed_cells and h_value:
                create_cell(xmldoc, value_list_node, "H", h_value, sheet_number, row_number)
            if "I" in processed_cells and i_value:
                create_cell(xmldoc, value_list_node, "I", i_value, sheet_number, row_number)
            if "J" in processed_cells and j_value:
                create_cell(xmldoc, value_list_node, "J", j_value, sheet_number, row_number)

            row_number += 1

        cell_value_node = xmldoc.createElement("CellValue")
        currNode.appendChild(cell_value_node)
        currNode = currNode.lastChild
        currNode = createTextNode(xmldoc, currNode, "RowNumber", "Laiks")
        currNode = createTextNode(xmldoc, currNode, "ColumnNumber", "2")
        currNode = createTextNode(xmldoc, currNode, "Value", str(round((time.time() - start_time)/60, 4)))

        data_xml = base64.encodestring(xmldoc.toprettyxml())
        res_id = self.pool.get('report.intrastat.product.xml').create(cr, uid, {
            'name': obligation_level + ' (%%0%sd.%%0%sd.)' % (2, 4) % (date_struct.tm_mon,date_struct.tm_year), 
            'filename': obligation_level.replace('/', '_') + '_%%0%sd-%%0%sd.xml' % (2, 4) % (date_struct.tm_mon,date_struct.tm_year),
            'data_xml': data_xml,
            'company_id': company.id,
            'type': this.type,
            'report_id': this.id
        }, context=context)

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'report.intrastat.product.xml',
            'view_type': 'form',
            'res_id': res_id,
            'views': [(False,'form')],
            'nodestroy': True
        }

    def open_xml_files(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        return {
            'name': _('XML Files'),
            'type': 'ir.actions.act_window',
            'res_model': 'report.intrastat.product.xml',
            'view_type': 'form',
            'views': [(False,'tree'), (False,'form')],
            'nodestroy': True,
            'domain': [('report_id','in',ids)]
        }

    # ---------------STATES---------------

    def done(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'done', 'date_done': datetime.strftime(datetime.today(), '%Y-%m-%d %H:%M:%S')}, context=context)

    def back2draft(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'draft'}, context=context)

class report_intrastat_product_line(osv.osv):
    _name = "report.intrastat.product.line"
    _description = "Lines of intrastat product declaration (Intrastat)"
    _order = 'id'

    _columns = {
        'parent_id': fields.many2one('report.intrastat.product', 'Intrastat product ref', ondelete='cascade', select=True, readonly=True),
        'state': fields.related('parent_id', 'state', type='char', relation='report.intrastat.product', string='State', readonly=True),
        'type': fields.related('parent_id', 'type', type='char', relation='report.intrastat.product', string='Type', readonly=True),
        'company_id': fields.related('parent_id', 'company_id', type='many2one', relation='res.company', string="Company", readonly=True),
        'company_currency_id': fields.related('company_id', 'currency_id', type='many2one', relation='res.currency', string="Company currency", readonly=True),
        'invoice_id': fields.many2one('account.invoice', 'Invoice ref', readonly=True),
        'picking_id': fields.many2one('stock.picking', 'Picking ref', readonly=True),
        'quantity': fields.char('Quantity', size=10, states={'done':[('readonly',True)]}),
        'source_uom_id': fields.many2one('product.uom', 'Source UoM', readonly=True),
        'intrastat_uom_id': fields.many2one('product.uom', 'Intrastat UoM', states={'done':[('readonly',True)]}),
        'partner_country_id': fields.many2one('res.country', 'Partner country', states={'done':[('readonly',True)]}),
        'partner_country_code': fields.related('partner_country_id', 'code', type='char', relation='res.country', string='Partner country', readonly=True),
        'intrastat_code': fields.char('Intrastat code', size=9, states={'done':[('readonly',True)]}),
        'intrastat_code_id': fields.many2one('report.intrastat.code', 'Intrastat code (not used in XML)', states={'done':[('readonly',True)]}),
        # Weight should be an integer... but I want to be able to display nothing in
        # tree view when the value is False (if weight is an integer, a False value would
        # be displayed as 0), that's why weight is a char !
        'weight': fields.char('Weight', size=10, states={'done':[('readonly',True)]}),
        'amount_company_currency': fields.integer('Fiscal value in company currency',
            required=True, states={'done':[('readonly',True)]},
            help="Amount in company currency to write in the declaration. Amount in company currency = amount in invoice currency converted to company currency with the rate of the invoice date (for pickings : with the rate of the 'date done') and rounded at 0 digits"),
        'amount_invoice_currency': fields.float('Fiscal value in invoice currency',
            digits_compute=dp.get_precision('Account'), readonly=True,
            help="Amount in invoice currency = amount of product value in invoice currency + amount of accessory cost in invoice currency (not rounded)"),
        'amount_accessory_cost_inv_cur': fields.float(
            'Amount of accessory costs in invoice currency',
            digits_compute=dp.get_precision('Account'), readonly=True,
            help="Amount of accessory costs in invoice currency = total amount of accessory costs of the invoice broken down into each product line at the pro-rata of the value"),
        'amount_product_value_inv_cur': fields.float(
            'Amount of product value in invoice currency',
            digits_compute=dp.get_precision('Account'), readonly=True,
            help="Amount of product value in invoice currency. For invoices, it is the amount of the invoice line or group of invoice lines. For pickings, it is the value of the product given by the pricelist for statistical value of the company."),
        'invoice_currency_id': fields.many2one('res.currency', "Invoice currency", readonly=True),
        'product_country_origin_id': fields.many2one('res.country', 'Product country of origin', states={'done':[('readonly',True)]}),
        'product_country_origin_code': fields.related('product_country_origin_id', 'code', type='char', relation='res.country', string='Product country of origin', readonly=True),
        'transport': fields.selection([
            (1, 'Maritime transport'),
            (2, 'Rail transport'),
            (3, 'Road transport'),
            (4, 'Air transport'),
            (5, 'Post'),
            (7, 'Fixed transport systems (pipelines)'),
            (8, 'Inland waterway transport'),
            (9, 'Carrying without means of transport')
            ], _('Type of transport'), states={'done':[('readonly',True)]}),
        'intrastat_type_id': fields.many2one('report.intrastat.type', 'Intrastat type', states={'done':[('readonly',True)]}),
        'transaction_code': fields.char('Transaction code', size=2),
        'incoterm_code': fields.char('Incoterm code', size=3),
        'partner_id': fields.many2one('res.partner', 'Partner', states={'done':[('readonly',True)]}),
    }

    def intrastat_code_on_change(self, cr, uid, ids, intrastat_code_id=False):
        result = {}
        result['value'] = {}
        if intrastat_code_id:
            intrastat_code = self.pool.get('report.intrastat.code').browse(cr, uid, intrastat_code_id)
            if intrastat_code.intrastat_uom_id:
                result['value'].update({'intrastat_code': intrastat_code.intrastat_code, 'intrastat_uom_id': intrastat_code.intrastat_uom_id.id})
            else:
                result['value'].update({'intrastat_code': intrastat_code.intrastat_code, 'intrastat_uom_id': False})
        return result

    def intrastat_type_on_change(self, cr, uid, ids, intrastat_type_id=False, type=False, obligation_level=False):
        result = {}
        result['value'] = {}
        if intrastat_type_id:
            intrastat_type = self.pool.get('report.intrastat.type').read(cr, uid, intrastat_type_id, ['transaction_code'])
            result['value'].update({'transaction_code': intrastat_type['transaction_code']})
        return result

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: