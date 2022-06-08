# See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from odoo.exceptions import UserError


class ExtendApproval(models.Model):
    _inherit = "approval.request"

    project_id = fields.Many2one('project.project', 'Project')
    transfer = fields.Boolean('Is Transfer', compute='check_transfer')
    rfq = fields.Boolean('Is RFQ', compute='check_transfer')
    internal_transfer_count = fields.Integer(compute='_compute_internal_transfer_count')

    def action_approve(self, approver=None):
        if not isinstance(approver, models.BaseModel):
            approver = self.mapped('approver_ids').filtered(
                lambda approver: approver.user_id == self.env.user
            )
        approver.write({'status': 'approved'})
        if self.transfer:
            self.create_transfer()
        if self.rfq:
            self.action_create_purchase_orders()
        self.sudo()._get_user_approval_activities(user=self.env.user).action_feedback()

    def action_create_purchase_orders(self):
        """ Create and/or modifier Purchase Orders. """
        self.ensure_one()
        self.product_line_ids._check_products_vendor()

        for line in self.product_line_ids:
            if line.on_hand_quantity <= 0:
                seller = line._get_seller_id()
                vendor = seller.name
                po_domain = line._get_purchase_orders_domain(vendor)
                purchase_orders = self.env['purchase.order'].search(po_domain)

                if purchase_orders:
                    # Existing RFQ found: check if we must modify an existing
                    # purchase order line or create a new one.
                    purchase_line = self.env['purchase.order.line'].search([
                        ('order_id', 'in', purchase_orders.ids),
                        ('product_id', '=', line.product_id.id),
                        ('product_uom', '=', line.product_id.uom_po_id.id),
                    ], limit=1)
                    purchase_order = self.env['purchase.order']
                    if purchase_line:
                        # Compatible po line found, only update the quantity.
                        line.purchase_order_line_id = purchase_line.id
                        purchase_line.product_qty += line.po_uom_qty
                        purchase_order = purchase_line.order_id
                    else:
                        # No purchase order line found, create one.
                        purchase_order = purchase_orders[0]
                        po_line_vals = self.env['purchase.order.line']._prepare_purchase_order_line(
                            line.product_id,
                            line.quantity,
                            line.product_uom_id,
                            line.company_id,
                            seller,
                            purchase_order,
                        )
                        new_po_line = self.env['purchase.order.line'].create(po_line_vals)
                        line.purchase_order_line_id = new_po_line.id
                        purchase_order.order_line = [(4, new_po_line.id)]

                    # Add the request name on the purchase order `origin` field.
                    new_origin = set([self.name])
                    if purchase_order.origin:
                        missing_origin = new_origin - set(purchase_order.origin.split(', '))
                        if missing_origin:
                            purchase_order.write({'origin': purchase_order.origin + ', ' + ', '.join(missing_origin)})
                    else:
                        purchase_order.write({'origin': ', '.join(new_origin)})
                else:
                    # No RFQ found: create a new one.
                    po_vals = line._get_purchase_order_values(vendor)
                    new_purchase_order = self.env['purchase.order'].create(po_vals)
                    po_line_vals = self.env['purchase.order.line']._prepare_purchase_order_line(
                        line.product_id,
                        line.quantity,
                        line.product_uom_id,
                        line.company_id,
                        seller,
                        new_purchase_order,
                    )
                    new_po_line = self.env['purchase.order.line'].create(po_line_vals)
                    line.purchase_order_line_id = new_po_line.id
                    new_purchase_order.order_line = [(4, new_po_line.id)]

    def _compute_internal_transfer_count(self):
        for request in self:
            transfers = self.env['stock.picking'].search([('approval_id', '=', request.id)])
            request.internal_transfer_count = len(transfers)

    def check_transfer(self):
        for s in self:
            count = 0
            count1 = 0
            for line in s.product_line_ids:
                if line.on_hand_quantity > 0:
                    count = 1
                if line.on_hand_quantity <= 0:
                    count1 = 1
            if count == 0:
                s.transfer = False
            else:
                s.transfer = True
            if count1 == 0:
                s.rfq = False
            else:
                s.rfq = True

    def create_transfer(self):
        lines_list = []
        for line in self.product_line_ids:
            if line.on_hand_quantity > 0:
                val = {
                    'product_id': line.product_id.id,
                    'quantity_done': line.quantity,
                    'name': '/',
                    'product_uom': line.product_id.uom_id.id,
                    'product_uom_qty': line.quantity,
                    'procure_method': 'make_to_stock',
                    'location_id': self.project_id.operation_type_id.default_location_src_id.id,
                    'location_dest_id': self.project_id.operation_type_id.default_location_dest_id.id
                }
                lines_list.append((0, 0, val))

        picking_vals = {
            'project_id': self.project_id.id,
            'approval_id': self.id,
            'picking_type_id': self.project_id.operation_type_id.id,
            'move_lines': lines_list,
            'location_id': self.project_id.operation_type_id.default_location_src_id.id,
            'location_dest_id': self.project_id.operation_type_id.default_location_dest_id.id
        }

        picking = self.env['stock.picking'].create(picking_vals)
        print(picking.name)

    def action_open_internal_transfer(self):
        """ Return the list of Internal Transfer the approval request created or
        affected in quantity. """
        self.ensure_one()
        transfers = self.env['stock.picking'].search([('approval_id', '=', self.id)])
        domain = [('id', 'in', transfers.ids)]
        action = {
            'name': _('Internal Transfer Orders'),
            'view_type': 'tree',
            'view_mode': 'list,form',
            'res_model': 'stock.picking',
            'type': 'ir.actions.act_window',
            'context': self.env.context,
            'domain': domain,
        }
        return action


class ExtendApprovalProductLine(models.Model):
    _inherit = "approval.product.line"

    on_hand_quantity = fields.Float('On Hand')
    short_excess = fields.Float('Short/Excess Qty', compute='compute_qty')

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id:
            self.on_hand_quantity = self.product_id.qty_available
            self.short_excess = self.on_hand_quantity - self.quantity

    @api.depends('quantity')
    def compute_qty(self):
        for s in self:
            if s.product_id:
                s.short_excess = s.on_hand_quantity - s.quantity
            else:
                s.short_excess = 0


class ExtendPurchase(models.Model):
    _inherit = "purchase.order"

    project_id = fields.Many2one('project.project', 'Project')


class ExtendPicking(models.Model):
    _inherit = "stock.picking"

    project_id = fields.Many2one('project.project', 'Project')
    approval_id = fields.Many2one('approval.request', 'Approval ID')


class ProjectExtend(models.Model):
    _inherit = 'project.project'

    operation_type_id = fields.Many2one('stock.picking.type', 'Operation Type')
