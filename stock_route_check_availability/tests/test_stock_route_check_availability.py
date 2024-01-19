from odoo.tests import Form
from odoo.tests.common import SavepointCase


class TestPacking(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestPacking, cls).setUpClass()
        cls.stock_location = cls.env.ref("stock.stock_location_stock")
        cls.loc_customer = cls.env.ref("stock.stock_location_customers")
        cls.loc_supplier = cls.env.ref("stock.stock_location_suppliers")

        cls.warehouse = cls.env["stock.warehouse"].search(
            [("lot_stock_id", "=", cls.stock_location.id)], limit=1
        )
        cls.warehouse.delivery_steps = "pick_ship"

        delivery_pick_rule = cls.warehouse.delivery_route_id.rule_ids.filtered(
            lambda r: r.location_src_id == cls.stock_location
        )
        delivery_pick_rule.group_propagation_option = "fixed"

        cls.productA = cls.env["product.product"].create(
            {"name": "Product A", "type": "product"}
        )
        cls.env["stock.quant"]._update_available_quantity(cls.productA, cls.stock_location, 3)

        # lets create a buy route
        cls.drop_transfer_type = cls.env["stock.picking.type"].create(
            {
                "name": "Dropship",
                "code": "internal",
                "sequence_code": "DRP",
                "default_location_dest_id": cls.loc_customer.id,
                "default_location_src_id": cls.loc_supplier.id,
            }
        )
        cls.route = cls.env["stock.location.route"].create(
            {
                "name": "Dropship",
                "product_selectable": True,
                "rule_ids": [
                    (0, 0, {
                        "name": "Vendors -> Customers",
                        "action": "buy",
                        "picking_type_id": cls.drop_transfer_type.id,
                        "location_id": cls.loc_customer.id,
                        "location_src_id": cls.loc_supplier.id,
                     }),
                ],
            }
        )
        # Add the new route to the product
        cls.productA.route_ids = [(4, cls.route.id, 0)]
        # OK: check sequence is lower than pick rule

    def test_one(self):
        deliver_form = Form(self.env["stock.picking"])
        deliver_form.picking_type_id = self.warehouse.out_type_id
        with deliver_form.move_ids_without_package.new() as move_line:
            move_line.product_id = self.productA
            move_line.product_uom_qty = 1
        transfer = deliver_form.save()
        transfer.move_lines.procure_method = "make_to_order"
        transfer.action_confirm()
        # Pick has been created
        # Fixme: there should be no move_orig_ids now that dropship route is used.
        # But is it ?
        self.assertTrue(transfer.move_lines.move_orig_ids)
