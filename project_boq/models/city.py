# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProjectCity(models.Model):
    _name = 'project.city'
    _description = 'City'

    name = fields.Char('City Name', required=True)


