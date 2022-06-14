# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class project_boq(models.Model):
    _inherit = 'project.project'

    project_line_ids = fields.One2many('project.project.line', 'boq_id', string="Material Planning Lines")
    stock_line_ids = fields.One2many('project.project.stock.line', 'move_id', string="Stock Move Lines")
    approval_count = fields.Integer(compute='_compute_approval_count')

    def _compute_approval_count(self):
        for project in self:
            approval = self.env['approval.request'].search([('project_id', '=', project.id)])
            project.approval_count = len(approval)


    def action_open_approvals(self):
        """ Return the list of approval request created or
        affected in quantity. """
        self.ensure_one()
        approvals = self.env['approval.request'].search([('project_id', '=', self.id)])
        domain = [('id', 'in', approvals.ids)]
        action = {
            'name': _('Approval Request'),
            'view_type': 'tree',
            'view_mode': 'list,form',
            'res_model': 'approval.request',
            'type': 'ir.actions.act_window',
            'context': self.env.context,
            'domain': domain,
        }
        return action


class project_boq_line(models.Model):
    _name = 'project.project.line'

    product_id = fields.Many2one('product.product', string='Product Name', required=True)
    name = fields.Char(string='Description')
    quantity = fields.Float(string='Quantity')
    uom_id = fields.Many2one('uom.uom', string='UOM')
    boq_id = fields.Many2one('project.project', string='Material')
    consume_material = fields.Float(string='Consumed Materials')
    difference = fields.Float(string='Difference', compute='get_difference')

    @api.depends('quantity', 'consume_material')
    def get_difference(self):
        for s in self:
            s.difference = s.quantity - s.consume_material

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
