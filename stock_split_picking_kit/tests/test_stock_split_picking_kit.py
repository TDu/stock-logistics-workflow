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

        cls.src_location = cls.env.ref("stock.stock_location_stock")
        cls.dest_location = cls.env.ref("stock.stock_location_customers")
        cls.product = cls.env["product.product"].create({"name": "Test product"})
        cls.partner = cls.env["res.partner"].create({"name": "Test partner"})
        cls.picking = cls.env["stock.picking"].create(
            {
                "partner_id": cls.partner.id,
                "picking_type_id": cls.env.ref("stock.picking_type_out").id,
                "location_id": cls.src_location.id,
                "location_dest_id": cls.dest_location.id,
            }
        )
        cls.move = cls.env["stock.move"].create(
            {
                "name": "/",
                "picking_id": cls.picking.id,
                "product_id": cls.product.id,
                "product_uom_qty": 10,
                "product_uom": cls.product.uom_id.id,
                "location_id": cls.src_location.id,
                "location_dest_id": cls.dest_location.id,
            }
        )

        # cls.seller = cls.env.ref("base.res_partner_1")
        cls.customer = cls.env.ref("base.res_partner_2")
        # cls.sale_order_model = cls.env["sale.order"]
        # cls.purchase_order_model = cls.env["purchase.order"]
        cls.product_model = cls.env["product.product"]
        cls.mto_route = cls.env.ref("stock.route_warehouse0_mto")
        __import__("pdb").set_trace()

        cls.product_office_furniture = cls.product_model.create(
            {
                "name": "OFFICE FURNITURE",
                "type": "product",
                "sale_ok": True,
                "purchase_ok": True,
                # "seller_ids": [(0, 0, {"name": cls.seller.id, "price": 200.0})],
                # "route_ids": [(4, cls.mto_route.id), (4, cls.buy_route.id)],
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
                # "seller_ids": [(0, 0, {"name": cls.seller.id, "price": 5.0})],
                # "route_ids": [(4, cls.mto_route.id), (4, cls.buy_route.id)],
            }
        )
        cls.product_garden_furniture = cls.product_model.create(
            {
                "name": "GARDEN FURNITURE",
                "type": "product",
                "sale_ok": False,
                "purchase_ok": True,
                # "seller_ids": [(0, 0, {"name": cls.seller.id, "price": 200.0})],
            }
        )
        cls.tmpl_garden_furniture = cls.product_garden_furniture.product_tmpl_id
        cls.product_garden_chair = cls.product_model.create(
            {
                "name": "GARDEN CHAIR",
                "type": "product",
                "sale_ok": True,
                "purchase_ok": True,
                # "seller_ids": [(0, 0, {"name": cls.seller.id, "price": 30.0})],
                # "route_ids": [(4, cls.mto_route.id), (4, cls.buy_route.id)],
                "route_ids": [(4, cls.mto_route.id)],
            }
        )
        cls.product_garden_table = cls.product_model.create(
            {
                "name": "GARDEN TABLE",
                "type": "product",
                "sale_ok": True,
                "purchase_ok": True,
                # "seller_ids": [(0, 0, {"name": cls.seller.id, "price": 110.0})],
                # "route_ids": [(4, cls.mto_route.id), (4, cls.buy_route.id)],
                "route_ids": [(4, cls.mto_route.id)],
            }
        )
        cls.tmpl_garden_table = cls.product_garden_table.product_tmpl_id
        cls.product_garden_table_top = cls.product_model.create(
            {
                "name": "GARDEN TABLE TOP",
                "type": "product",
                "sale_ok": True,
                # "seller_ids": [(0, 0, {"name": cls.seller.id, "price": 50.0})],
                # "route_ids": [(4, cls.mto_route.id), (4, cls.buy_route.id)],
                "route_ids": [(4, cls.mto_route.id)],
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

    # @classmethod
    # def create_sale_order(cls, product):
    #     order_form = Form(cls.sale_order_model)
    #     order_form.partner_id = cls.customer
    #     with order_form.order_line.new() as line:
    #         line.product_id = product
    #         line.product_uom_qty = 5.0
    #     return order_form.save()

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
            # "warehouse_id": self.wh or False,
            "warehouse_id": False,
            "company_id": self.env.company,
        }
        procurement = proc_group.Procurement(
            product,
            proc_qty,
            proc_uom,
            self.src_location,
            product.name,
            "PROC TEST",
            self.env.company,
            values,
        )
        proc_group.run([procurement])

    def test_stock_split_picking_kit(self):
        self._update_qty_in_location(self.src_location, self.product_garden_table_top, 100)
        self._create_kit_picking(self.product_garden_furniture, 4)
        # self.assertTrue(True)
        # self.picking.action_assign()
        # wizard = (
        #     self.env["stock.split.picking"]
        #     .with_context(active_ids=self.picking.ids)
        #     .create({"mode": "kit_quantity", "kit_split_quantity": 3})
        # )
        # wizard.action_apply()

    # def test_stock_split_picking(self):
    #     # Picking state is draft
    #     self.assertEqual(self.picking.state, "draft")
    #     # We can't split a draft picking
    #     with self.assertRaises(UserError):
    #         self.picking.split_process()
    #     # Confirm picking
    #     self.picking.action_confirm()
    #     # We can't split an unassigned picking
    #     with self.assertRaises(UserError):
    #         self.picking.split_process()
    #     # We assign quantities in order to split
    #     self.picking.action_assign()
    #     move_line = self.env["stock.move.line"].search(
    #         [("picking_id", "=", self.picking.id)], limit=1
    #     )
    #     move_line.qty_done = 4.0
    #     # Split picking: 4 and 6
    #     # import pdb; pdb.set_trace()
    #     self.picking.split_process()

    #     # We have a picking with 4 units in state assigned
    #     self.assertAlmostEqual(move_line.qty_done, 4.0)
    #     self.assertAlmostEqual(move_line.product_qty, 4.0)
    #     self.assertAlmostEqual(move_line.product_uom_qty, 4.0)

    #     self.assertAlmostEqual(self.move.quantity_done, 4.0)
    #     self.assertAlmostEqual(self.move.product_qty, 4.0)
    #     self.assertAlmostEqual(self.move.product_uom_qty, 4.0)

    #     self.assertEqual(self.picking.state, "assigned")
    #     # An another one with 6 units in state assigned
    #     new_picking = self.env["stock.picking"].search(
    #         [("backorder_id", "=", self.picking.id)], limit=1
    #     )
    #     move_line = self.env["stock.move.line"].search(
    #         [("picking_id", "=", new_picking.id)], limit=1
    #     )

    #     self.assertAlmostEqual(move_line.qty_done, 0.0)
    #     self.assertAlmostEqual(move_line.product_qty, 6.0)
    #     self.assertAlmostEqual(move_line.product_uom_qty, 6.0)

    #     self.assertAlmostEqual(new_picking.move_lines.quantity_done, 0.0)
    #     self.assertAlmostEqual(new_picking.move_lines.product_qty, 6.0)
    #     self.assertAlmostEqual(new_picking.move_lines.product_uom_qty, 6.0)

    #     self.assertEqual(new_picking.state, "assigned")

    # def test_stock_split_picking_wizard_move(self):
    #     self.move2 = self.move.copy()
    #     self.assertEqual(self.move2.picking_id, self.picking)
    #     wizard = (
    #         self.env["stock.split.picking"]
    #         .with_context(active_ids=self.picking.ids)
    #         .create({"mode": "move"})
    #     )
    #     wizard.action_apply()
    #     self.assertNotEqual(self.move2.picking_id, self.picking)
    #     self.assertEqual(self.move.picking_id, self.picking)

    # def test_stock_split_picking_wizard_selection(self):
    #     self.move2 = self.move.copy()
    #     self.assertEqual(self.move2.picking_id, self.picking)
    #     wizard = (
    #         self.env["stock.split.picking"]
    #         .with_context(active_ids=self.picking.ids)
    #         .create({"mode": "selection", "move_ids": [(6, False, self.move2.ids)]})
    #     )
    #     wizard.action_apply()
    #     self.assertNotEqual(self.move2.picking_id, self.picking)
    #     self.assertEqual(self.move.picking_id, self.picking)

    # def test_stock_picking_split_off_moves(self):
    #     with self.assertRaises(UserError):
    #         # fails because we can't split off all lines
    #         self.picking._split_off_moves(self.picking.move_lines)
    #     with self.assertRaises(UserError):
    #         # fails because we can't split cancelled pickings
    #         self.picking.action_cancel()
    #         self.picking._split_off_moves(self.picking.move_lines)
