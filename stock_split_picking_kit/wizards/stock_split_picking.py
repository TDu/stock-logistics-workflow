# Copyright 2020 Hunki Enterprises BV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models
from odoo.tools import groupby
from odoo.exceptions import UserError


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
        return self._picking_action(pickings)

    def _split_by_kit_quantity(self, picking):
        filters = {
            "incoming_moves": lambda m: m.location_id.usage == "supplier"
            and (
                not m.origin_returned_move_id
                # or (m.origin_returned_move_id and m.to_refund)
            ),
            "outgoing_moves": lambda m: m.location_id.usage != "supplier"
            # and m.to_refund,
        }
        all_pickings = picking
        current_picking = picking
        new_picking = self.env["stock.picking"]
        used_slots = 0
        for bom, bom_move_list in groupby(current_picking.move_lines, key=lambda move: move.bom_line_id.bom_id):
            if bom.type != "phantom":
                raise UserError("Should it not be allowed if not a full kit picking ?")
            moves = self.env["stock.move"].browse([move.id for move in bom_move_list])
            order_qty = max(moves.mapped("product_qty")) # Just give the maximum possible
            kit_quantity = moves._compute_kit_quantities(
                bom.product_id, order_qty, bom , filters
            )
            kit_quantity = abs(kit_quantity)

            if used_slots + kit_quantity > self.kit_split_quantity:
                # Split the picking for a smaller number of kits
                # It means splitting some moves quantity

                kit_to_split = kit_quantity - self.kit_split_quantity - used_slots
                nb_of_splits = int(kit_to_split / self.kit_split_quantity) + 1
                for n in range(nb_of_splits):
                    new_moves = self.env["stock.move"]
                    for move in moves:
                        new_move_vals = move._split(move.bom_line_id.product_qty * kit_to_split)
                        if new_move_vals:
                            new_moves |= self.env["stock.move"].create(new_move_vals)
                    new_picking = picking._create_split_backorder()
                    new_moves.write({"picking_id": new_picking.id})
                    new_moves.mapped("move_line_ids").write({"picking_id": new_picking.id})
                    all_pickings |= new_picking
                # FIXME Properly split the reminder !
            else:
                used_slots += kit_quantity
        return all_pickings
