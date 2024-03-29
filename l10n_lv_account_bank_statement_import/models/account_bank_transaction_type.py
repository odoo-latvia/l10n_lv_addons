# -*- encoding: utf-8 -*-
##############################################################################
#
#    Part of Odoo.
#    Copyright (C) 2019 Allegro IT (<http://www.allegro.lv/>)
#                       E-mail: <info@allegro.lv>
#                       Address: <Vienibas gatve 109 LV-1058 Riga Latvia>
#                       Phone: +371 67289467
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import api, fields, models, _

class AccountBankTransactionType(models.Model):
    _name = 'account.bank.transaction.type'
    _description = 'Bank Transaction Types'

    name = fields.Char(string='Name', required=True)
    io = fields.Selection([('+','+'), ('-','-')], string='I/O', help="Controls, whether the Amount of the transaction is positive or negative.")
    account_id = fields.Many2one('account.account', string='Account', required=True, help="The account for the transaction.")
    description = fields.Text(string='Description')


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
