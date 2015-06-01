# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 ITS-1 (<http://www.its1.lv/>)
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

from openerp.osv import osv
from openerp.report import report_sxw
from openerp.addons.hr_payroll.report import report_payslip_details

class payslip_details_report(report_payslip_details.payslip_details_report):

    def get_details_by_rule_category(self, obj):
        payslip_line = self.pool.get('hr.payslip.line')
        rule_cate_obj = self.pool.get('hr.salary.rule.category')

        def get_recursive_parent(rule_categories):
            if not rule_categories:
                return []
            # ----- fix for category hierarchy: insert is for list not object:
            if not isinstance(rule_categories,list):
                rule_categories = [rule_categories]
            # -----
            if rule_categories[0].parent_id:
                rule_categories.insert(0, rule_categories[0].parent_id)
                get_recursive_parent(rule_categories)
            return rule_categories

        # ----- new method for finding the index of an existing parent category:
        def check_parent(data_list, id):
            ind = 'False'
            for d in data_list:
                if 'id' in d and d['id'] == id:
                    ind = data_list.index(d)
            return ind
        # -----

        res = []
        result = {}
        ids = []

        for id in range(len(obj)):
            ids.append(obj[id].id)
        if ids:
            # ----- rc.parent_id and pl.sequence switched places in ORDER BY
            self.cr.execute('''SELECT pl.id, pl.category_id FROM hr_payslip_line as pl \
                LEFT JOIN hr_salary_rule_category AS rc on (pl.category_id = rc.id) \
                WHERE pl.id in %s \
                GROUP BY rc.parent_id, pl.sequence, pl.id, pl.category_id \
                ORDER BY rc.parent_id, pl.sequence''',(tuple(ids),))
            # -----
            keys = [] # ----- list for not losing the sequence
            for x in self.cr.fetchall():
                result.setdefault(x[1], [])
                result[x[1]].append(x[0])
                # ----- update sequence list
                if x[1] not in keys:
                    keys.append(x[1])
                # -----
            for key in keys: # ----- use key list instead of iteritems()
                value = result[key] # ----- set value variable from key
                rule_categories = rule_cate_obj.browse(self.cr, self.uid, [key])
                parents = get_recursive_parent(rule_categories)
                category_total = 0
                for line in payslip_line.browse(self.cr, self.uid, value):
                    category_total += line.total
                level = 0
                for parent in parents:
                    # ----- check for existing parent and sum totals if found:
                    exist_parent = check_parent(res, parent.id)
                    if exist_parent != 'False':
                        res[exist_parent]['total'] += category_total
                    else:
                        # -----
                        res.append({
                            'id': parent.id,
                            'rule_category': parent.name,
                            'name': parent.name,
                            'code': parent.code,
                            'level': level,
                            'total': category_total,
                        })
                    level += 1
                for line in payslip_line.browse(self.cr, self.uid, value):
                    res.append({
                        'rule_category': line.name,
                        'name': line.name,
                        'code': line.code,
                        'total': line.total,
                        'level': level
                    })
        return res

class wrapped_report_payslipdetails(osv.AbstractModel):
    _inherit = 'report.hr_payroll.report_payslipdetails'
    _wrapped_report_class = payslip_details_report

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: