# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models
from odoo.osv import expression

class ProcurementGroup(models.Model):
    _inherit = "procurement.group"

    def _get_rule(self, product_id, location_id, values):
        # Get the ordered quantity from the sale line id
        disable_dropshiping = False
        sale_line_id = values.get("sale_line_id")
        if sale_line_id:
            sale_line = self.env["sale.order.line"].browse(sale_line_id)
            if sale_line and sale_line.product_uom_qty <= product_id.immediately_usable_qty:
                disable_dropshiping = True
        # __import__("pdb").set_trace()
        return super(ProcurementGroup, self.with_context(no_dropship_rule=disable_dropshiping))._get_rule(product_id, location_id, values)

    def _search_rule(self, route_ids, product_id, warehouse_id, domain):
        disable_dropshiping = self.env.context.get("no_dropship_rule", False)
        if disable_dropshiping:
            domain = expression.AND([[("route_id.disable_if_stock_exists", "=", False)], domain])
        # __import__("pdb").set_trace()

        return super()._search_rule(route_ids, product_id, warehouse_id, domain)
