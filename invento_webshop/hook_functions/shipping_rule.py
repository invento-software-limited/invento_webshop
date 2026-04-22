import frappe
from erpnext.accounts.doctype.shipping_rule.shipping_rule import ShippingRule
from frappe.utils import flt

class CustomShippingRule(ShippingRule):
    def apply(self, doc):
        """Override the default apply method to support custom costs like stepped weight."""
        from invento_webshop.api.shipping import calculate_cost

        # Calculate total weight and net total for the doc
        net_total = flt(doc.base_net_total)
        total_weight = 0
        
        # For Quotation/Sales Order, we need to calculate total weight if not already present
        if doc.doctype in ["Quotation", "Sales Order"]:
            for item in doc.items:
                weight = frappe.db.get_value("Item", item.item_code, "weight_per_unit") or 0
                total_weight += flt(weight) * item.qty
        else:
            total_weight = flt(doc.total_net_weight)

        shipping_amount = calculate_cost(self, net_total, total_weight)

        # convert to order currency if needed
        if doc.get("currency") and doc.get("company_currency") and doc.currency != doc.company_currency:
            shipping_amount = flt(shipping_amount / doc.get("conversion_rate", 1), 2)

        self.add_shipping_rule_to_tax_table(doc, shipping_amount)
