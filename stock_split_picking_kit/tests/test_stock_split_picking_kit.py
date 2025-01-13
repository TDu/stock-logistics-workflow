# Copyright 2025 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import fields
from odoo.tests.common import Form, SavepointCase


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

    def _create_kit_picking(self, product, quantity):
        proc_group = self.env["procurement.group"]
        uom = product.uom_id
        proc_qty, proc_uom = uom._adjust_uom_quantities(quantity, uom)
        today = fields.Date.today()
        proc_group = self.env["procurement.group"].create({})
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

    def _get_kit_quantity(self, picking, bom):
        """Returns the quantity of kits in a transfer."""
        filters = {
            "incoming_moves": lambda m: m.location_id.usage == "supplier",
            "outgoing_moves": lambda m: m.location_id.usage != "supplier",
        }
        kit_quantity = picking.move_lines._compute_kit_quantities(
            bom.product_id, 100, bom, filters
        )
        return abs(kit_quantity)

    def test_split_picking_kit_no_split(self):
        """Check number of kits is equal to the split limit.

        No split is needed.
        """
        pickings_before = self.env["stock.picking"].search([])
        self._create_kit_picking(self.product_garden_table, 3)
        pickings_after = self.env["stock.picking"].search([])
        picking = pickings_after - pickings_before
        self.assertTrue(picking)
        wizard = (
            self.env["stock.split.picking"]
            .with_context(active_ids=picking.ids)
            .create({"mode": "kit_quantity", "kit_split_quantity": 3})
        )
        wizard.action_apply()
        new_picking = self.env["stock.picking"].search([]) - pickings_after
        self.assertFalse(new_picking)
        np_kq = self._get_kit_quantity(picking, self.bom_garden_table)
        self.assertEqual(np_kq, 3)

    def test_split_picking_kit_single_split(self):
        """Check number of kits is 4 and the split limit is 3.

        New picking is created and one kit is moved to it.

        """
        pickings_before = self.env["stock.picking"].search([])
        self._create_kit_picking(self.product_garden_table, 4)
        pickings_after = self.env["stock.picking"].search([])
        picking = pickings_after - pickings_before
        self.assertTrue(picking)
        wizard = (
            self.env["stock.split.picking"]
            .with_context(active_ids=picking.ids)
            .create({"mode": "kit_quantity", "kit_split_quantity": 3})
        )
        wizard.action_apply()
        new_picking = self.env["stock.picking"].search([]) - pickings_after
        self.assertTrue(new_picking)
        self.assertEqual(len(new_picking), 1)
        np_kq = self._get_kit_quantity(new_picking, self.bom_garden_table)
        self.assertEqual(np_kq, 1)

    def test_split_picking_kit_multiple_split(self):
        """Check number of kits is 7 and splitting at 3."""
        pickings_before = self.env["stock.picking"].search([])
        self._create_kit_picking(self.product_garden_table, 7)
        pickings_after = self.env["stock.picking"].search([])
        picking = pickings_after - pickings_before
        self.assertTrue(picking)
        wizard = (
            self.env["stock.split.picking"]
            .with_context(active_ids=picking.ids)
            .create({"mode": "kit_quantity", "kit_split_quantity": 3})
        )
        wizard.action_apply()
        new_picking = self.env["stock.picking"].search([]) - pickings_after
        self.assertEqual(len(new_picking), 2)
        oo = [
            self._get_kit_quantity(pick, self.bom_garden_table) for pick in new_picking
        ]
        self.assertEqual(set(oo), {3.0, 1.0})



    @classmethod
    def _create_picking(cls, picking_type=None, lines=None, confirm=True, **kw):
        picking_form = Form(cls.env["stock.picking"])
        picking_form.picking_type_id = picking_type or cls.picking_type
        picking_form.partner_id = cls.partner
        for product, qty in lines:
            with picking_form.move_ids_without_package.new() as move:
                move.product_id = product
                move.product_uom_qty = qty
        for k, v in kw.items():
            setattr(picking_form, k, v)
        picking = picking_form.save()
        if confirm:
            picking.action_confirm()
        return picking

    def _get_picking_ids_from_action(self, res, expected_quantity):
        """Return the pickings found in the action returned by the wizard."""
        id_list = res["domain"][0][2]
        self.assertEqual(len(id_list), expected_quantity)
        return self.env["stock.picking"].browse(id_list)

    def test_split_picking_kit_with_no_kit(self):
        """Check split picking only has non kit product."""
        picking = self._create_picking(
            self.env.ref("stock.picking_type_out"),
            [
                (self.product_garden_table_top, 3),
                (self.product_garden_table_leg, 21)
            ]
        )
        wizard = (
            self.env["stock.split.picking"]
            .with_context(active_ids=picking.ids)
            .create({"mode": "kit_quantity", "kit_split_quantity": 7})
        )
        res = wizard.action_apply()
        new_picking = self._get_picking_ids_from_action(res, 1)
        self.assertEqual(len(new_picking.move_lines), 1)

    def test_split_picking_with_product_and_kit(self):
        picking = self._create_picking(
            self.env.ref("stock.picking_type_out"),
            [
                (self.product_garden_table_top, 3),
                (self.product_garden_table_leg, 21),
                (self.product_garden_table, 4),
            ]
        )
        wizard = (
            self.env["stock.split.picking"]
            .with_context(active_ids=picking.ids)
            .create({"mode": "kit_quantity", "kit_split_quantity": 6})
        )
        res = wizard.action_apply()
        new_picking = self._get_picking_ids_from_action(res, 1)
        self.assertEqual(len(new_picking.move_lines), 3)
