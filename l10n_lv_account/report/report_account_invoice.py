import time
from openerp import netsvc
from openerp.report import report_sxw
from openerp.osv import osv

class custom_parser(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(custom_parser, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'cr':cr,
            'uid': uid,
        })

# class test(osv):
#     pass
#     print '\n\n\n%r' % 'this is it'

# netsvc.Service._services['report.account.invoice'].parser = custom_parser
# netsvc.Service._services['report.account.invoice'].tmpl = 'addons/l10_lv_account/report/report_account_invoice.html'

# print 'I am not loaded'
        
# report_sxw.report_sxw('report.l10n_lv_account.invoice',
#                        'account.invoice', 
#                        'addons/l10n_lv_account/report/report_account_invoice.html',
#                        parser=custom_parser)
report_sxw.report_sxw(
    'report.account.invoice.webkit',
    'account.invoice',
    'l10n_lv_account/report/report_account_invoice_out_html.mako',
    parser=custom_parser
)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
