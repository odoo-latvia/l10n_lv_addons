# -*- encoding: utf-8 -*-
##############################################################################
#
#    Part of Odoo.
#    Copyright (C) 2017 Allegro IT (<http://www.allegro.lv/>)
#                       E-mail: <info@allegro.lv>
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
        return res


class WizardMultiChartsAccounts(models.TransientModel):
    _inherit = "wizard.multi.charts.accounts"

    @api.onchange('chart_template_id')
    def onchange_chart_template_id(self):
        res = super(WizardMultiChartsAccounts, self).onchange_chart_template_id()
        lv_chart_template = self.env.ref('l10n_lv.l10n_lv_chart_template')
        if lv_chart_template and self.chart_template_id.id == lv_chart_template.id:
            self.sale_tax_rate = 21.0
            self.purchase_tax_rate = 21.0
        return res

    @api.model
    def create(self, values):
        tax_values = [
            'default_sale_tax_rate',
            'default_purchase_tax_rate',
            'default_sale_tax_id',
            'default_purchase_tax_id'
        ]
        for tv in tax_values:
            if self.env.context.get(tv):
                values.update({tv[8:]: self.env.context[tv]})
        return super(WizardMultiChartsAccounts, self).create(values)


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    @api.onchange('chart_template_id')
    def onchange_chart_template_id(self):
        lv_chart_template = self.env.ref('l10n_lv.l10n_lv_chart_template')
        if self.chart_template_id and lv_chart_template and self.chart_template_id.id == lv_chart_template.id:
            lv_sale_tax_tmpl = self.env.ref('l10n_lv.lv_tax_template_PVN-SR')
            lv_purchase_tax_tmpl = self.env.ref('l10n_lv.lv_tax_template_Pr-SR')
            if lv_sale_tax_tmpl:
                self.default_sale_tax_id = False
            if lv_purchase_tax_tmpl:
                self.default_purchase_tax_id = False

    @api.multi
    def set_values(self):
        ctx = self.env.context.copy()
        lv_chart_template = self.env.ref('l10n_lv.l10n_lv_chart_template')
        if self.chart_template_id and lv_chart_template and self.chart_template_id.id == lv_chart_template.id:
            ctx.update({
                'default_sale_tax_rate': 21.0,
                'default_purchase_tax_rate': 21.0
            })
            lv_sale_tax_tmpl = self.env.ref('l10n_lv.lv_tax_template_PVN-SR')
            lv_purchase_tax_tmpl = self.env.ref('l10n_lv.lv_tax_template_Pr-SR')
            if lv_sale_tax_tmpl:
                ctx.update({'default_sale_tax_id': lv_sale_tax_tmpl.id})
            if lv_purchase_tax_tmpl:
                ctx.update({'default_purchase_tax_id': lv_purchase_tax_tmpl.id})
        return super(ResConfigSettings, self.with_context(ctx)).set_values()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: