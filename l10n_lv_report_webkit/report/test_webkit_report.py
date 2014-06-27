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

from openerp.report import report_sxw
from openerp import netsvc
from openerp.tools.translate import _

class test_webkit_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context=None):
        super(test_webkit_report, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'cr': cr,
            'uid': uid,
            'user': self.pool.get("res.users").browse(cr, uid, uid),
            'set_font': self.set_font
        })

    def set_font(self):
        report = self.pool.get('ir.model.data').get_object(self.cr, self.uid, 'l10n_lv_report_webkit', 'test_webkit_report')
        font = 'Sans-serif'
        if report.__hasattr__('font'):
            if report.font:
                font = report.font + ',Sans-serif'
        return font

report_sxw.report_sxw('report.test.webkit.report', 'report.webkit.test', 'addons/l10n_lv_report_webkit/report/test_webkit_report.mako', parser=test_webkit_report)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: