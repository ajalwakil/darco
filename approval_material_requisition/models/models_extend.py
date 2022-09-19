# See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from odoo.exceptions import UserError


class ApprovalCategory(models.Model):
    _inherit = 'approval.category'

    is_measurement = fields.Boolean('Is Requisition')

    @api.onchange('is_measurement')
    def _onchange_approval(self):
        if self.is_measurement:
            self.approval_type = 'purchase'
            self.update({'approval_type': 'purchase'})
            self.write({'approval_type': 'purchase'})
        else:
            self.approval_type = False


class ExtendApproval(models.Model):
    _inherit = "approval.request"

    project_id = fields.Many2one('project.project', 'Project Number')
    transfer = fields.Boolean('Is Transfer', compute='check_transfer')
    rfq = fields.Boolean('Is RFQ', compute='check_transfer')
    internal_transfer_count = fields.Integer(compute='_compute_internal_transfer_count')
    is_measurement = fields.Boolean('Is Measurement')
    operation_type_id = fields.Many2one('stock.picking.type', 'Operation Type', related='project_id.operation_type_id')
    region_manager = fields.Many2one('res.users', 'Region Manager', related='project_id.region_manager')
    approver_rights = fields.Boolean(string='Approver rights')

    @api.onchange('project_id')
    def get_values_def(self):
        for s in self:
            s.approver_rights = False
            if s.env.user.has_group('approval_material_requisition.group_approvers'):
                s.approver_rights = True

    @api.onchange('project_id')
    def onchange_project_id(self):
        if self.project_id:
            self.operation_type_id = self.project_id.operation_type_id.id
            self.region_manager = self.project_id.region_manager.id
            if self.region_manager:
                self.approver_ids = False
                approver = self.env['approval.approver'].create({
                    'user_id': self.region_manager.id,
                    'request_id': self.id,
                    'required': True,
                    'status': 'new'
                })
                for app in self.category_id.approver_ids:
                    approver = self.env['approval.approver'].create({
                        'user_id': app.user_id.id,
                        'request_id': self.id,
                        'required': True,
                        'status': 'new'
                    })

    @api.onchange('category_id')
    def _onchange_category(self):
        if self.category_id.is_measurement:
            self.is_measurement = True
        else:
            self.is_measurement = False

    @api.onchange('is_measurement')
    def _onchange_measurement(self):
        if self.is_measurement:
            self.is_measurement = True
        else:
            self.is_measurement = False

    def action_confirm(self):
        for request in self:
            for line in request.product_line_ids:
                if line.on_hand_quantity > 0:
                    material_planning = self.env['project.project.line'].search(
                        [('product_id', '=', line.product_id.id),
                         ('boq_id', '=', request.project_id.id)
                         ], limit=1)
                    if material_planning:
                        material_quantity = material_planning.issues_qty + line.quantity
                        material_cost = material_planning.average_cost + line.product_id.standard_price
                        if material_quantity > material_planning.planned_quantity:
                            raise UserError(_('The Approval quantity of the {0} increased the plan quantity.'.format(
                                line.product_id.name)))
                    else:
                        raise UserError(
                            _('The {0} not is in Material Planing.'.format(line.product_id.name)))
        return super().action_confirm()

    def action_approve(self, approver=None):
        if self.is_measurement:
            if self.transfer:
                self.create_transfer()
            if self.rfq:
                self.action_create_purchase_orders()
        if not isinstance(approver, models.BaseModel):
            approver = self.mapped('approver_ids').filtered(
                lambda approver: approver.user_id == self.env.user
            )
        approver.write({'status': 'approved'})

        self.sudo()._get_user_approval_activities(user=self.env.user).action_feedback()

    # def _get_purchase_order_values(self, vendor):
    #     vals = super()._get_purchase_order_values(vendor)
    #     # picking_type = self._get_picking_type()
    #     if self.project_id.id:
    #         vals['project_id'] = self.project_id.id
    #     return vals

    def action_cancel(self):
        """ Override to notify Purchase Orders when the Approval Request is cancelled. """
        res = super().action_cancel()
        purchases = self.product_line_ids.purchase_order_line_id.order_id
        for purchase in purchases:
            product_lines = self.product_line_ids.filtered(
                lambda line: line.purchase_order_line_id.order_id.id == purchase.id
            )
            purchase._activity_schedule_with_view(
                'mail.mail_activity_data_warning',
                views_or_xmlid='approvals_purchase.exception_approval_request_canceled',
                user_id=self.env.user.id,
                render_context={
                    'approval_requests': self,
                    'product_lines': product_lines,
                }
            )
        for line in self.product_line_ids:
            material_planning = self.env['project.project.line'].search([('product_id', '=', line.product_id.id),
                                                                         ('boq_id', '=', self.project_id.id)
                                                                         ], limit=1)
            if material_planning:
                material_quantity = material_planning.issues_qty - line.quantity
                material_cost = material_planning.average_cost - line.product_id.standard_price
                material_planning.issues_qty = material_quantity
                material_planning.average_cost = material_cost
        return res

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
                    if self.project_id:
                        po_vals['project_id'] = self.project_id.id
                        po_vals['picking_type_id'] = self.project_id.operation_po_type_id.id
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
                material_planning = self.env['project.project.line'].search([('product_id', '=', line.product_id.id),
                                                                             ('boq_id', '=', self.project_id.id)
                                                                             ], limit=1)
                if material_planning:
                    material_quantity = material_planning.issues_qty + line.quantity
                    material_cost = material_planning.average_cost + line.product_id.standard_price
                    if material_quantity > material_planning.planned_quantity:
                        raise UserError(_('The Approval quantity of the {0} increased the plan quantity.'.format(
                            line.product_id.name)))
                    else:
                        material_planning.issues_qty = material_quantity
                        material_planning.average_cost = material_cost
                    val = {
                        'product_id': line.product_id.id,
                        'quantity_done': line.quantity,
                        'name': line.product_id.name,
                        'product_uom': line.product_id.uom_id.id,
                        'product_uom_qty': line.quantity,
                        'procure_method': 'make_to_stock',
                        'location_id': self.project_id.operation_type_id.default_location_src_id.id,
                        'location_dest_id': self.project_id.operation_type_id.default_location_dest_id.id
                    }
                    lines_list.append((0, 0, val))
                else:
                    raise UserError(
                        _('The {0} not is in Material Planing.'.format(line.product_id.name)))

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
    source_location_id = fields.Many2one('stock.location', 'Location')

    @api.onchange('product_id', 'location_id')
    def onchange_product_id(self):
        if self.approval_request_id.operation_type_id:
            self.source_location_id = self.approval_request_id.operation_type_id.default_location_src_id.id
        if self.product_id:
            quant = self.env['stock.quant'].search(
                [('product_id', '=', self.product_id.id), ('location_id', '=', self.source_location_id.id)])
            quantity = 0
            for s in quant:
                quantity += s.quantity
            self.on_hand_quantity = quantity
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

    project_id = fields.Many2one('project.project', 'Project Number')

    @api.onchange('project_id')
    def onchange_project_id(self):
        if self.project_id:
            self.picking_type_id = self.project_id.operation_po_type_id.id
        else:
            self.picking_type_id = False


class ExtendPicking(models.Model):
    _inherit = "stock.picking"

    project_id = fields.Many2one('project.project', 'Project Number')
    approval_id = fields.Many2one('approval.request', 'Approval ID')


class ProjectExtend(models.Model):
    _inherit = 'project.project'

    operation_type_id = fields.Many2one('stock.picking.type', 'Operation Type')
    operation_po_type_id = fields.Many2one('stock.picking.type', 'Operation Type Po')


class StockPickingTypeExtend(models.Model):
    _inherit = 'stock.picking.type'

    project_id = fields.Many2one('project.project', string='Project Number', compute='onchange_operation_id')

    @api.onchange('operation_type_id')
    def onchange_operation_id(self):
        for s in self:
            project = self.env['project.project'].search([('operation_type_id', '=', s.id)], limit=1)
            if project:
                s.project_id = project.id
            else:
                s.project_id = False


class StockPickingTypeExtend(models.Model):
    _inherit = 'stock.picking.type'

    project_id = fields.Many2one('project.project', string='Project Number', compute='onchange_operation_id')

    def onchange_operation_id(self):
        for s in self:
            project = self.env['project.project'].search([('operation_type_id', '=', s.id)], limit=1)
            if project:
                s.project_id = project.id
            else:
                s.project_id = False


class StockLocationExtend(models.Model):
    _inherit = 'stock.location'

    project_id = fields.Many2one('project.project', string='Project Number', compute='onchange_operation_id')

    def onchange_operation_id(self):
        for s in self:
            s.project_id = False
            project_src = self.env['project.project'].search([('operation_type_id.default_location_src_id', '=', s.id)],
                                                             limit=1)
            project_des = self.env['project.project'].search(
                [('operation_type_id.default_location_dest_id', '=', s.id)], limit=1)
            if project_src:
                s.project_id = project_src.id
            if project_des:
                s.project_id = project_des.id
