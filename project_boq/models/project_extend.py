# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class project_boq(models.Model):
    _inherit = 'project.project'

    name = fields.Char("Name", index=True, required=True, tracking=True, translate=True)
    project_line_ids = fields.One2many('project.project.line', 'boq_id', string="Material Planning Lines",
                                       track_visibility='onchange')
    stock_line_ids = fields.One2many('project.project.stock.line', 'move_id', string="Stock Move Lines")
    approval_count = fields.Integer(compute='_compute_approval_count')
    po_count = fields.Integer(compute='_compute_approval_count')
    ref = fields.Char('Reference Number')
    ref_check = fields.Boolean('Reference Check')
    district_id = fields.Many2one('project.district', 'District')
    region_manager = fields.Many2one('res.users', 'Region Manager')
    city_id = fields.Many2one('project.city', 'City')
    area_id = fields.Many2one('project.area', 'Area')
    region_id = fields.Many2one('project.region', 'Region')
    plot_number = fields.Char('Plot Number')
    number_of_flat = fields.Char('Number of Flat')
    number_of_roof = fields.Char('Number of Roof')
    number_of_apartment = fields.Char('Number of Apartment in Each Floor')
    state = fields.Selection(selection=[
        ('draft', 'Draft'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Stage', required=True, readonly=True, copy=False, tracking=True,
        default='draft')

    @api.model
    def create(self, vals):
        # vals['name'] = self.env['ir.sequence'].next_by_code('project.project') or _('New')
        vals['ref_check'] = True
        record = super(project_boq, self).create(vals)
        return record

    def action_confirm(self):
        self.write({'state': 'done'})

    def action_draft(self):
        self.write({'state': 'draft'})

    def _compute_approval_count(self):
        for project in self:
            approval = self.env['approval.request'].search([('project_id', '=', project.id)])
            project.approval_count = len(approval)
            purchase_order = self.env['purchase.order'].search([('project_id', '=', project.id)])
            project.po_count = len(purchase_order)

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

    def action_open_purchase_order(self):
        """ Return the list of Purchase Order created or
        affected in quantity. """
        self.ensure_one()
        purchase_orders = self.env['purchase.order'].search([('project_id', '=', self.id)])
        domain = [('id', 'in', purchase_orders.ids)]
        action = {
            'name': _('Purchase Order'),
            'view_type': 'tree',
            'view_mode': 'list,form',
            'res_model': 'purchase.order',
            'type': 'ir.actions.act_window',
            'context': self.env.context,
            'domain': domain,
        }
        return action


class project_boq_line(models.Model):
    _name = 'project.project.line'

    product_id = fields.Many2one('product.product', string='Product Name', required=True)
    name = fields.Char(string='Description')
    planned_quantity = fields.Float(string='Planned Qty', track_visibility='onchange')
    estimated_cost = fields.Float(string='Estimated Cost', track_visibility='onchange')
    estimated_amount = fields.Float(string='Estimated Amount', compute='get_difference')
    uom_id = fields.Many2one('uom.uom', string='UOM')
    boq_id = fields.Many2one('project.project', string='Material')
    issues_qty = fields.Float(string='Issued Qty', readonly=True)
    average_cost = fields.Float(string='Average Cost', readonly=True)
    amount = fields.Float(string='Amount', compute='get_difference')
    difference_qty = fields.Float(string='Diff. Qty', compute='get_difference')
    difference_amount = fields.Float(string='Diff. Amount', compute='get_difference')

    @api.depends('planned_quantity', 'issues_qty', 'estimated_amount', 'estimated_cost', 'average_cost', 'amount')
    def get_difference(self):
        for s in self:
            s.difference_qty = s.planned_quantity - s.issues_qty
            s.estimated_amount = s.planned_quantity * s.estimated_cost
            s.amount = s.issues_qty * s.average_cost
            s.difference_amount = s.estimated_amount - s.amount

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
