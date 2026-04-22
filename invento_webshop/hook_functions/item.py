import re
import frappe
from frappe.utils.data import slug
from erpnext.stock.doctype.item.item import Item


class CustomItem(Item):
    def validate(self):
        super().validate()

        if not self.custom_route:
            clean_name = self.item_name.replace("/", " ")
            self.custom_route = "/shop/" + slug(clean_name)


@frappe.whitelist()
def enqueue_update_products_route():
    frappe.enqueue("invento_webshop.hook_functions.item.update_products_route", queue='long', timeout=300)
    return "Queued background job to update product routes."


def update_products_route():
    items = frappe.get_all("Item", fields=["name", "item_group", "item_name"])
    existing_routes = set(x[0] for x in frappe.db.get_all("Item", fields=["custom_route"], as_list=True))

    for item in items:
        if not item.item_name:
            continue

        name = item.item_name.replace("/", " ")
        name_slug = clean_slug(name)
        base_route = f"/shop/{name_slug}"
        route = base_route

        suffix = 1
        while route in existing_routes:
            suffix += 1
            route = f"{base_route}-{suffix}"
        existing_routes.add(route)

        frappe.db.set_value("Item", item.name, "custom_route", route)

    frappe.db.commit()
    return "success"

def clean_slug(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    text = text.strip('-')
    return text