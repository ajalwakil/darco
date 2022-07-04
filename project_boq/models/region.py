# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProjectRegion(models.Model):
    _name = 'project.region'
    _description = 'Region'

    name = fields.Char('Region Name', required=True)


