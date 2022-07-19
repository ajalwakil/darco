# See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from odoo.exceptions import UserError


class StockPickingMethodExtend(models.Model):
    _inherit = 'stock.picking'

    @api.model
    def create(self, vals):
        if 'origin' in vals:
            purchase_order = self.env['purchase.order'].search([('name', '=', vals['origin'])])
            if purchase_order.project_id:
                vals['project_id'] = purchase_order.project_id.id
        defaults = self.default_get(['name', 'picking_type_id'])
        picking_type = self.env['stock.picking.type'].browse(
            vals.get('picking_type_id', defaults.get('picking_type_id')))
        if vals.get('name', '/') == '/' and defaults.get('name', '/') == '/' and vals.get('picking_type_id',
                                                                                          defaults.get(
                                                                                                  'picking_type_id')):
            if picking_type.sequence_id:
                vals['name'] = picking_type.sequence_id.next_by_id()

        # make sure to write `schedule_date` *after* the `stock.move` creation in
        # order to get a determinist execution of `_set_scheduled_date`
        scheduled_date = vals.pop('scheduled_date', False)
        res = super(StockPickingMethodExtend, self).create(vals)
        if scheduled_date:
            res.with_context(mail_notrack=True).write({'scheduled_date': scheduled_date})
        res._autoconfirm_picking()

        # set partner as follower
        if vals.get('partner_id'):
            for picking in res.filtered(
                    lambda p: p.location_id.usage == 'supplier' or p.location_dest_id.usage == 'customer'):
                picking.message_subscribe([vals.get('partner_id')])
        if vals.get('picking_type_id'):
            for move in res.move_lines:
                if not move.description_picking:
                    move.description_picking = move.product_id.with_context(lang=move._get_lang())._get_description(
                        move.picking_id.picking_type_id)

        return res
