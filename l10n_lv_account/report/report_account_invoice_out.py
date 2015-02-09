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

import time
from openerp.report import report_sxw
from openerp.osv import osv

class report_account_invoice_out(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(report_account_invoice_out, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'cr':cr,
            'uid': uid,
            'form_title': self.form_title,
            'form_address': self.form_address
        })

    def form_title(self, partner):
        title = False
        if partner and partner.title:
            if partner.title.shortcut:
                title = partner.title.shortcut.upper()
            else:
                title = partner.title.name
        return title

    def form_address(self, src):
        addr_list = []
        if src.street:
            addr_list.append(src.street)
        if src.street2:
            addr_list.append(src.street2)
        if src.city:
            addr_list.append(src.city)
        if src.state_id:
            addr_list.append(src.state_id.name)
        if src.zip:
            addr_list.append(src.zip)
        if src.country_id:
            addr_list.append(src.country_id.name)
        address = ''
        if addr_list:
            address = ', '.join(addr_list)
        return address

class iout_report(osv.AbstractModel):
    _name = 'report.l10n_lv_account.invoice_out'
    _inherit = 'report.abstract_report'
    _template = 'l10n_lv_account.invoice_out'
    _wrapped_report_class = report_account_invoice_out

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
