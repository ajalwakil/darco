# -*- coding: utf-8 -*-

from odoo import models, fields, api


class project_boq(models.Model):
    _inherit = 'project.project'

    project_line_ids = fields.One2many('project.project.line', 'boq_id', string="Material Planning Lines")
    stock_line_ids = fields.One2many('project.project.stock.line', 'move_id', string="Stock Move Lines")

class project_boq_line(models.Model):
    _name = 'project.project.line'

    product_id = fields.Many2one('product.product', string='Product Name', required=True)
    name = fields.Char(string='Description')
    quantity = fields.Float(string='Quantity')
    uom_id = fields.Many2one('uom.uom', string='UOM')
    boq_id = fields.Many2one('project.project', string='Material')
    consume_material = fields.Float(string='Consumed Materials')



    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.name = self.product_id.name
            self.uom_id = self.product_id.uom_id.id

class project_boq_stockline(models.Model):
    _name = 'project.project.stock.line'

    product_uom_id = fields.Many2one('uom.uom', 'Unit of Measure', )
    quantity = fields.Float(string='Quantity')
    date = fields.Datetime('Date', default=fields.Datetime.now, required=True)
    expected_date = fields.Datetime('Expected Date', default=fields.Datetime.now, required=True)
    product_id = fields.Many2one('product.product', string='Product', required=True)
    # state = fields.Selection()
    move_id = fields.Many2one('project.project', string='Stock Move')

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.product_uom_id = self.product_id.uom_id.id