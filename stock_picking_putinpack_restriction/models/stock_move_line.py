# Copyright 2023 Camptocamp (https://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, models
from odoo.exceptions import ValidationError


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    def _action_done(self):
        # TODO group lines by picking type
        for line in self:
            restriction = line.move_id.picking_type_id.put_in_pack_restriction
            if not restriction:
                continue
            line_has_package = bool(line.result_package_id)
            if restriction == "no_package" and line_has_package:
                raise ValidationError(
                    _("Using package on transfer type ? for product ? is not allowed.")
                )
            if restriction == "with_package" and not line_has_package:
                raise ValidationError(
                    _("A package is required with transfer type ? for product ?.")
                )
        return super()._action_done()

    # But what is the difference with the package restriction module ?
    #   * This more general solution relates to multiple location
