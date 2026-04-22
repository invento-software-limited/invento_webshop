import frappe
from invento_webshop.webshop_functions.cart import create_user, add_new_address, create_party, create_contact, update_address_with_customer


@frappe.whitelist(allow_guest=True)
def register(doc):
    doc = frappe.parse_json(doc)
    first_name = doc.get("first_name", "")
    last_name = doc.get("last_name", "")
    address_title = f"{first_name} {last_name}".strip()
    doc["address_title"] = address_title
    address = add_new_address(frappe.as_json(doc))

    customer = {
        "customer_name": doc.get("company_name") or (doc.first_name + " " + doc.last_name),
        "mobile_number": doc.telephone,
        "customer_email_address": doc.email
    }

    party = create_party(doc=customer)
    if party:
        create_contact(doc, party.name)
        if address:
            update_address_with_customer(address.name, party.name)

    return party.name