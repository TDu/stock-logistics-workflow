# Copyright 2025 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

# from odoo.exceptions import UserError
from odoo import fields
from odoo.tests import Form
from odoo.tests.common import SavepointCase


class TestStockSplitPickingKit(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        cls.warehouse = cls.env.ref("stock.warehouse0")
        cls.src_location = cls.env.ref("stock.stock_location_stock")
        cls.dest_location = cls.env.ref("stock.stock_location_customers")
        cls.product = cls.env["product.product"].create({"name": "Test product"})
        cls.partner = cls.env["res.partner"].create({"name": "Test partner"})
        cls.product_model = cls.env["product.product"]

        cls.product_office_furniture = cls.product_model.create(
            {
                "name": "OFFICE FURNITURE",
                "type": "product",
                "sale_ok": True,
                "purchase_ok": True,
            }
        )
        cls.tmpl_office_furniture = cls.product_office_furniture.product_tmpl_id
        cls.product_office_chair = cls.product_model.create(
            {
                "name": "OFFICE CHAIR",
                "type": "product",
                "sale_ok": False,
                "purchase_ok": False,
            }
        )
        cls.product_office_desk = cls.product_model.create(
            {
                "name": "OFFICE DESK",
                "type": "product",
                "sale_ok": False,
                "purchase_ok": False,
            }
        )
        cls.product_office_bin = cls.product_model.create(
            {
                "name": "OFFICE BIN",
                "type": "product",
                "sale_ok": False,
                "purchase_ok": True,
            }
        )
        cls.product_garden_furniture = cls.product_model.create(
            {
                "name": "GARDEN FURNITURE",
                "type": "product",
                "sale_ok": False,
                "purchase_ok": True,
            }
        )
        cls.tmpl_garden_furniture = cls.product_garden_furniture.product_tmpl_id
        cls.product_garden_chair = cls.product_model.create(
            {
                "name": "GARDEN CHAIR",
                "type": "product",
                "sale_ok": True,
                "purchase_ok": True,
            }
        )
        cls.product_garden_table = cls.product_model.create(
            {
                "name": "GARDEN TABLE",
                "type": "product",
                "sale_ok": True,
                "purchase_ok": True,
            }
        )
        cls.tmpl_garden_table = cls.product_garden_table.product_tmpl_id
        cls.product_garden_table_top = cls.product_model.create(
            {
                "name": "GARDEN TABLE TOP",
                "type": "product",
                "sale_ok": True,
            }
        )
        cls.product_garden_table_leg = cls.product_model.create(
            {
                "name": "GARDEN TABLE LEG",
                "type": "product",
                "sale_ok": False,
                "purchase_ok": False,
            }
        )
        cls.bom_model = cls.env["mrp.bom"]
        cls.bom_office_furniture = cls.bom_model.create(
            {
                "product_tmpl_id": cls.tmpl_office_furniture.id,
                "product_id": cls.product_office_furniture.id,
                "type": "phantom",
                "bom_line_ids": [
                    (
                        0,
                        0,
                        {"product_id": cls.product_office_desk.id, "product_qty": 1.0},
                    ),
                    (
                        0,
                        0,
                        {"product_id": cls.product_office_chair.id, "product_qty": 2.0},
                    ),
                    (
                        0,
                        0,
                        {"product_id": cls.product_office_bin.id, "product_qty": 3.0},
                    ),
                ],
            }
        )
        cls.bom_garden_table = cls.bom_model.create(
            {
                "product_tmpl_id": cls.tmpl_garden_table.id,
                "product_id": cls.product_garden_table.id,
                "type": "phantom",
                "bom_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": cls.product_garden_table_leg.id,
                            "product_qty": 4.0,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "product_id": cls.product_garden_table_top.id,
                            "product_qty": 1.0,
                        },
                    ),
                ],
            }
        )
        cls.bom_garden_furniture = cls.bom_model.create(
            {
                "product_tmpl_id": cls.tmpl_garden_furniture.id,
                "product_id": cls.product_garden_furniture.id,
                "type": "phantom",
                "bom_line_ids": [
                    (
                        0,
                        0,
                        {"product_id": cls.product_garden_chair.id, "product_qty": 4.0},
                    ),
                    (
                        0,
                        0,
                        {"product_id": cls.product_garden_table.id, "product_qty": 1.0},
                    ),
                ],
            }
        )

    @classmethod
    def _update_qty_in_location(
        cls, location, product, quantity, package=None, lot=None
    ):
        quants = cls.env["stock.quant"]._gather(
            product, location, lot_id=lot, package_id=package, strict=True
        )
        # this method adds the quantity to the current quantity, so remove it
        quantity -= sum(quants.mapped("quantity"))
        cls.env["stock.quant"]._update_available_quantity(
            product, location, quantity, package_id=package, lot_id=lot
        )


    def _create_kit_picking(self, product, quantity):
        proc_group = self.env["procurement.group"]
        uom = product.uom_id
        proc_qty, proc_uom = uom._adjust_uom_quantities(quantity, uom)
        today = fields.Date.today()
        proc_group = self.env["procurement.group"].create(
            {}
        )
        values = {
            "group_id": proc_group,
            "date_planned": today,
            "date_deadline": today,
            "warehouse_id": self.warehouse,
            "company_id": self.env.company,
        }
        procurement = proc_group.Procurement(
            product,
            proc_qty,
            proc_uom,
            self.dest_location,
            product.name,
            "PROC TEST",
            self.env.company,
            values,
        )
        proc_group.run([procurement])

    def test_split_picking_kit_single_split(self):
        self._update_qty_in_location(self.src_location, self.product_garden_table_top, 100)
        pickings_before = self.env["stock.picking"].search([])
        self._create_kit_picking(self.product_garden_table, 4)
        pickings_after = self.env["stock.picking"].search([])
        picking = pickings_after - pickings_before
        self.assertTrue(picking)
        picking.action_assign()
        self.assertEqual(picking.state, "assigned")
        wizard = (
            self.env["stock.split.picking"]
            .with_context(active_ids=picking.ids)
            .create({"mode": "kit_quantity", "kit_split_quantity": 3})
        )
        wizard.action_apply()
        new_picking = self.env["stock.picking"].search([]) - pickings_after
        self.assertTrue(new_picking)
