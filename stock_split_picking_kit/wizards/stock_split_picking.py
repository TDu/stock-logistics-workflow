# Copyright 2020 Hunki Enterprises BV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockSplitPicking(models.TransientModel):
    _inherit = "stock.split.picking"

    mode = fields.Selection(
        selection_add=[("kit_quantity", "Quantity of kits")],
        ondelete={"kit_quantity": "set default"}
    )
    kit_split_quantity = fields.Integer()


    def _apply_kit_quantity(self):
        # TODO: split by the kit quantity set in the ui
        # Questions ?
        # - What if there is move for products that are not kits ?
        # - Should we have a default or fail if the split quanity is zero ?
        pickings = self.env["stock.picking"]
        for picking in self.mapped("picking_ids"):
            pickings |= self._split_by_kit_quantity(picking)
        return pickings

    def _split_by_kit_quantity(self, picking):
        return picking


    # def _apply_done(self):
    #     return self.mapped("picking_ids").split_process()

    # def _apply_move(self):
    #     """Create new pickings for every move line, keep first
    #     move line in original picking
    #     """
    #     new_pickings = self.env["stock.picking"]
    #     for picking in self.mapped("picking_ids"):
    #         for move in picking.move_lines[1:]:
    #             new_pickings += picking._split_off_moves(move)
    #     return self._picking_action(new_pickings)

    # def _apply_selection(self):
    #     """Create one picking for all selected moves"""
    #     moves = self.mapped("move_ids")
    #     new_picking = moves.mapped("picking_id")._split_off_moves(moves)
    #     return self._picking_action(new_picking)
