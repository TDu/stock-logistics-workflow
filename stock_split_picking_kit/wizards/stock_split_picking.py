# Copyright 2025 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import fields, models
from odoo.exceptions import UserError
from odoo.tools import groupby


class StockSplitPicking(models.TransientModel):
    _inherit = "stock.split.picking"

    mode = fields.Selection(
        selection_add=[("kit_quantity", "Quantity of kits")],
        ondelete={"kit_quantity": "set default"},
    )
    kit_split_quantity = fields.Integer(string="Number of kits by transfer")

    def _apply_kit_quantity(self):
        pickings = self.env["stock.picking"]
        for picking in self.mapped("picking_ids"):
            pickings |= self._split_by_kit_quantity(picking)
        return self._picking_action(pickings)

    def _split_by_kit_quantity(self, picking):
        filters = {
            "incoming_moves": lambda m: m.location_id.usage == "supplier",
            "outgoing_moves": lambda m: m.location_id.usage != "supplier",
        }
        all_pickings = picking
        new_picking = self.env["stock.picking"]
        used_slots = 0
        max_slots = self.kit_split_quantity
        for bom, bom_move_list in groupby(
            picking.move_lines, key=lambda move: move.bom_line_id.bom_id
        ):

            moves = self.env["stock.move"].browse([move.id for move in bom_move_list])
            if bom.type != "phantom":
                new_moves = self.env["stock.move"]
                while used_slots < max_slots and moves:
                    available_slots = max_slots - used_slots
                    move = fields.first(moves)
                    quantity = move.product_qty
                    if available_slots >= quantity:
                        moves = moves - move
                        used_slots += quantity
                    else:
                        new_move_vals = move._split(quantity - available_slots)
                        moves = moves - move
                        if new_move_vals:
                            new_moves |= self.env["stock.move"].create(new_move_vals)
                            # It is full
                            new_picking = picking._create_split_backorder()
                            new_moves.write({"picking_id": new_picking.id})
                            new_moves.mapped("move_line_ids").write(
                                {"picking_id": new_picking.id}
                            )
                            # All remaining move needs to be move
                            moves.write({"picking_id": new_picking.id})
                            moves.mapped("move_line_ids").write(
                                {"picking_id": new_picking.id}
                            )
                        return new_picking


            if bom.type != "phantom":
                raise UserError("Only have kits in the transfer ?")
            moves = self.env["stock.move"].browse([move.id for move in bom_move_list])
            kit_quantity = moves._compute_kit_quantities(
                bom.product_id,
                max(moves.mapped("product_qty")),  # Just use max possible
                bom,
                filters,
            )
            kit_quantity = abs(kit_quantity)

            while kit_quantity > 0:
                if used_slots == max_slots:
                    # Current picking is full, create a new one
                    new_picking = picking._create_split_backorder()
                    all_pickings |= new_picking
                    used_slots = 0

                available_slots = max_slots - used_slots
                kit_to_split = (
                    available_slots if kit_quantity // available_slots else kit_quantity
                )
                if new_picking:
                    new_moves = self.env["stock.move"]
                    for move in moves:
                        new_move_vals = move._split(
                            move.bom_line_id.product_qty * kit_to_split
                        )
                        if new_move_vals:
                            new_moves |= self.env["stock.move"].create(new_move_vals)
                    new_moves.write({"picking_id": new_picking.id})
                    new_moves.mapped("move_line_ids").write(
                        {"picking_id": new_picking.id}
                    )

                used_slots += kit_to_split
                kit_quantity -= kit_to_split

        return all_pickings
