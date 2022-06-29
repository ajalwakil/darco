# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProjectArea(models.Model):
    _name = 'project.area'
    _description = 'Area'

    name = fields.Char('Area Name', required=True)


