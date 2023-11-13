# Copyright 2023 Camptocamp (https://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, fields, models
from odoo.exceptions import ValidationError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    put_in_pack_restriction = fields.Selection(
        related="picking_type_id.put_in_pack_restriction"
    )

    def _pre_put_in_pack_hook(self, move_line_ids):
        # FIXME we should have only one picking type...
        if self.picking_type_id.put_in_pack_restriction == "no_package":
            # TODO Maybe the button should be hidden, then ?
            raise ValidationError(
                _("You are not allowed to use packages with this transfer type.")
            )

        return super()._pre_put_in_pack_hook(move_line_ids)
