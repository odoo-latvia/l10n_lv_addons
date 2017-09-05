# -*- encoding: utf-8 -*-
##############################################################################
#
#    Part of Odoo.
#    Copyright (C) 2016 ITS-1 (<http://www.its1.lv/>)
#                       E-mail: <info@its1.lv>
#                       Address: <Vienibas gatve 109 LV-1058 Riga Latvia>
#                       Phone: +371 67289467
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

from odoo import api, fields, models, _

class AccountJournal(models.Model):
    _inherit = "account.journal"

    @api.model
    def _prepare_liquidity_account(self, name, company, currency_id, type):
        res = super(AccountJournal, self)._prepare_liquidity_account(name, company, currency_id, type)
        if type in ('bank', 'cash'):
            user_type = self.env.ref('l10n_lv.lv_account_type_2_5')
            if user_type:
                res['user_type_id'] = user_type.id
            tag_0 = self.env.ref('l10n_lv.lv_account_tag_0')
            tag_2 = self.env.ref('l10n_lv.lv_account_tag_2')
            tag_26 = self.env.ref('l10n_lv.lv_account_tag_26')
            tags = []
            if tag_0:
                tags.append(tag_0.id)
            if tag_2:
                tags.append(tag_2.id)
            if tag_26:
                tags.append(tag_26.id)
            if type == 'bank':
                tag_262 = self.env.ref('l10n_lv.lv_account_tag_262')
                if tag_262:
                    tags.append(tag_262.id)
            if type == 'cash':
                tag_261 = self.env.ref('l10n_lv.lv_account_tag_261')
                if tag_261:
                    tags.append(tag_261.id)
            if tags:
                res.update({'tag_ids': [(6, 0, tags)]})
        return res

class WizardMultiChartsAccounts(models.TransientModel):
    _inherit = 'wizard.multi.charts.accounts'

    @api.onchange('chart_template_id')
    def onchange_chart_template_id(self):
        res = super(WizardMultiChartsAccounts, self).onchange_chart_template_id()
        lv_chart_template = self.env.ref('l10n_lv.l10n_lv_chart_template')
        if lv_chart_template and self.chart_template_id.id == lv_chart_template.id:
#            lv_sale_tax = self.env.ref('l10n_lv.lv_tax_template_PVN-SR')
#            lv_purchase_tax = self.env.ref('l10n_lv.lv_tax_template_Pr-SR')
#            if lv_sale_tax:
#                self.sale_tax_id = lv_sale_tax.id
#            if lv_purchase_tax:
#                self.purchase_tax_id = lv_purchase_tax.id
            self.sale_tax_rate = 21.0
            self.purchase_tax_rate = 21.0
        return res

class AccountConfigSettings(models.TransientModel):
    _inherit = 'account.config.settings'

    @api.onchange('chart_template_id')
    def onchange_chart_template_id(self):
        res = super(AccountConfigSettings, self).onchange_chart_template_id()
        lv_chart_template = self.env.ref('l10n_lv.l10n_lv_chart_template')
        if self.chart_template_id and lv_chart_template and self.chart_template_id.id == lv_chart_template.id:
            lv_sale_tax = self.env.ref('l10n_lv.lv_tax_template_PVN-SR')
            lv_purchase_tax = self.env.ref('l10n_lv.lv_tax_template_Pr-SR')
            if lv_sale_tax:
                self.sale_tax_id = lv_sale_tax.id
            if lv_purchase_tax:
                self.purchase_tax_id = lv_purchase_tax.id
            self.sale_tax_rate = 21.0
            self.purchase_tax_rate = 21.0
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: