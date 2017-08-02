# -*- encoding: utf-8 -*-
from odoo import api, models, fields, _
from odoo.exceptions import UserError

from .. import lursoft_client


class LursoftAccountWizard(models.TransientModel):
    _name = 'lursoft.account.wizard'

    msg = fields.Char('Message')
    lursoft_username = fields.Char(
            'Username', required=True,
            default=lambda s: s.env.user.lursoft_username)
    lursoft_password = fields.Char('Password', required=True)
    user = fields.Many2one('res.users')

    @api.multi
    def validate_lursoft_credentials(self):
        if self.env.context.get('active_model') == 'res.users':
            self.user = self.env.context.get('active_id')

        if not self.user:
            raise UserError('User not present')

        client = lursoft_client.LursoftClient(self.lursoft_username,
                                              self.lursoft_password)
        try:
            client.auth(retry=0)
        except lursoft_client.AuthError:

            self.remove_lursoft_account()
            action = self.env['ir.actions.act_window'].for_xml_id(
                     'l10n_lv_partner_data_lursoft', 'lursoft_account_setup')

            action.update(context={
                    'default_lursoft_username': self.lursoft_username,
                    'default_lursoft_lastname': self.lursoft_password,
                    'default_msg': _('Invalid credentials.'),
                    'default_user': self.user.id,
                    })
            return action

        else:
            self.activate_lursoft_account()
            return self.env['ir.actions.act_window'].for_xml_id(
                    'l10n_lv_partner_data_lursoft', 'lursoft_account_success')

    @api.model
    def remove_lursoft_account(self):
        self.user.lursoft_enabled = False
        self.user.lursoft_username = False
        self.user.lursoft_password = False

    @api.model
    def activate_lursoft_account(self):
        self.user.lursoft_username = self.lursoft_username
        self.user.lursoft_password = self.lursoft_password
        self.user.lursoft_enabled = True


class LursofAccountSuccess(models.TransientModel):
    _name = 'lursoft.account.success.wizard'
