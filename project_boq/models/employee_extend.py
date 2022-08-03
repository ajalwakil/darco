# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class Employee_Extend(models.Model):
    _inherit = 'hr.employee'

    city_id = fields.Many2one('project.city', 'City')
    area_id = fields.Many2one('project.area', 'Area')
    english_name = fields.Char('English Name')
