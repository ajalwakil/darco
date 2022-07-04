# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ApprovalPrint(models.Model):
    _inherit = 'approval.request'
    _description = 'Approval Request report print'

