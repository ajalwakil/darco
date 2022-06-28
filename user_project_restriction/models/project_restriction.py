# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ResUsersProject(models.Model):
    _inherit = 'res.users'

    user_project_ids = fields.Many2many(
        'project.project', String='Allowed Projects')

    restrict = fields.Boolean('Restrict Project')


class ProjectProjectExtend(models.Model):
    _inherit = 'project.project'

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        """ Override search() to always show inactive children when searching via ``child_of`` operator. The ORM will
        always call search() with a simple domain of the form [('parent_id', 'in', [ids])]. """
        # a special ``domain`` is set on the ``child_ids`` o2m to bypass this logic, as it uses similar domain expressions
        if self.env.user.restrict:
            args += [('id', '=', self.env.user.user_project_ids.ids)]
        # if self.env.user.has_group('branch.group_branch_user_manager'):
        #     args += ['|', ('branch_id', '=', False), ('branch_id.id', 'in', self.env.user.branch_ids.ids)]
        return super(ProjectProjectExtend, self)._search(args, offset=offset, limit=limit, order=order,
                                                         count=count, access_rights_uid=access_rights_uid)


class ApprovalRequestRestriction(models.Model):
    _inherit = 'approval.request'

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        """ Override search() to always show inactive children when searching via ``child_of`` operator. The ORM will
        always call search() with a simple domain of the form [('parent_id', 'in', [ids])]. """
        # a special ``domain`` is set on the ``child_ids`` o2m to bypass this logic, as it uses similar domain expressions
        if self.env.user.restrict:
            args += ['|', ('project_id', '=', False), ('project_id', '=', self.env.user.user_project_ids.ids)]
        # if self.env.user.has_group('branch.group_branch_user_manager'):
        #     args += ['|', ('branch_id', '=', False), ('branch_id.id', 'in', self.env.user.branch_ids.ids)]
        return super(ApprovalRequestRestriction, self)._search(args, offset=offset, limit=limit, order=order,
                                                               count=count, access_rights_uid=access_rights_uid)


# class PurchaseOrderProjectRestriction(models.Model):
#     _inherit = 'purchase.order'
#
#     @api.model
#     def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
#         """ Override search() to always show inactive children when searching via ``child_of`` operator. The ORM will
#         always call search() with a simple domain of the form [('parent_id', 'in', [ids])]. """
#         # a special ``domain`` is set on the ``child_ids`` o2m to bypass this logic, as it uses similar domain expressions
#         if self.env.user.restrict:
#             args += ['|', ('project_id', '=', False), ('project_id', '=', self.env.user.user_project_ids.ids)]
#         # if self.env.user.has_group('branch.group_branch_user_manager'):
#         #     args += ['|', ('branch_id', '=', False), ('branch_id.id', 'in', self.env.user.branch_ids.ids)]
#         return super(PurchaseOrderProjectRestriction, self)._search(args, offset=offset, limit=limit, order=order,
#                                                                     count=count, access_rights_uid=access_rights_uid)
#
#
# class StockPickingProjectRestriction(models.Model):
#     _inherit = 'stock.picking'
#
#     @api.model
#     def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
#         """ Override search() to always show inactive children when searching via ``child_of`` operator. The ORM will
#         always call search() with a simple domain of the form [('parent_id', 'in', [ids])]. """
#         # a special ``domain`` is set on the ``child_ids`` o2m to bypass this logic, as it uses similar domain expressions
#         if self.env.user.restrict:
#             args += ['|', ('project_id', '=', False), ('project_id', '=', self.env.user.user_project_ids.ids)]
#         # if self.env.user.has_group('branch.group_branch_user_manager'):
#         #     args += ['|', ('branch_id', '=', False), ('branch_id.id', 'in', self.env.user.branch_ids.ids)]
#         return super(StockPickingProjectRestriction, self)._search(args, offset=offset, limit=limit, order=order,
#                                                                    count=count, access_rights_uid=access_rights_uid)
#
#
# class StockPickingTypeProjectRestriction(models.Model):
#     _inherit = 'stock.picking.type'
#
#     @api.model
#     def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
#         """ Override search() to always show inactive children when searching via ``child_of`` operator. The ORM will
#         always call search() with a simple domain of the form [('parent_id', 'in', [ids])]. """
#         # a special ``domain`` is set on the ``child_ids`` o2m to bypass this logic, as it uses similar domain expressions
#         if self.env.user.restrict:
#             args += ['|', ('project_id', '=', False), ('project_id', '=', self.env.user.user_project_ids.ids)]
#         # if self.env.user.has_group('branch.group_branch_user_manager'):
#         #     args += ['|', ('branch_id', '=', False), ('branch_id.id', 'in', self.env.user.branch_ids.ids)]
#         return super(StockPickingTypeProjectRestriction, self)._search(args, offset=offset, limit=limit, order=order,
#                                                                        count=count, access_rights_uid=access_rights_uid)
#
#
# class StockLocationProjectRestriction(models.Model):
#     _inherit = 'stock.location'
#
#     @api.model
#     def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
#         """ Override search() to always show inactive children when searching via ``child_of`` operator. The ORM will
#         always call search() with a simple domain of the form [('parent_id', 'in', [ids])]. """
#         # a special ``domain`` is set on the ``child_ids`` o2m to bypass this logic, as it uses similar domain expressions
#         if self.env.user.restrict:
#             args += ['|', ('project_id', '=', False), ('project_id', '=', self.env.user.user_project_ids.ids)]
#         # if self.env.user.has_group('branch.group_branch_user_manager'):
#         #     args += ['|', ('branch_id', '=', False), ('branch_id.id', 'in', self.env.user.branch_ids.ids)]
#         return super(StockLocationProjectRestriction, self)._search(args, offset=offset, limit=limit, order=order,
#                                                                        count=count, access_rights_uid=access_rights_uid)
#
#
# class StockPickingExtend(models.Model):
#     _inherit = 'stock.picking.type'
#
#     @api.model
#     def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
#         """ Override search() to always show inactive children when searching via ``child_of`` operator. The ORM will
#         always call search() with a simple domain of the form [('parent_id', 'in', [ids])]. """
#         # a special ``domain`` is set on the ``child_ids`` o2m to bypass this logic, as it uses similar domain expressions
#         if self.env.user.restrict:
#             args += ['|', ('warehouse_id', '=', False), ('warehouse_id', '=', self.env.user.user_warehouse_ids.ids)]
#         # if self.env.user.has_group('branch.group_branch_user_manager'):
#         #     args += ['|', ('branch_id', '=', False), ('branch_id.id', 'in', self.env.user.branch_ids.ids)]
#         return super(StockPickingExtend, self)._search(args, offset=offset, limit=limit, order=order,
#                                                        count=count, access_rights_uid=access_rights_uid)

# class StockPickingLocation(models.Model):
#     _inherit = 'stock.picking'
#
#     @api.onchange('location_id')
#     def product_id_change(self):
#         if self.env.user.login != 'admin':
#             domain = {'location_id': [('id', 'in', self.env.user.user_location_ids.ids)]}
#             return {'domain': domain}
