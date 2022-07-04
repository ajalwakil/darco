# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProjectDistrict(models.Model):
    _name = 'project.district'
    _description = 'District'

    name = fields.Char('District Name', required=True)


