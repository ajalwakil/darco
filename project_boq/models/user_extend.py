# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class UsersName_Extend(models.Model):
    _inherit = 'res.users'

    english_name = fields.Char('English Name')
