import frappe
from frappe import _

from invento_webshop.webshop_functions.cart import (
    add_new_address,
    create_contact,
    create_party,
    create_user,
    update_address_with_customer,
)
from invento_webshop.webshop_functions.checkout_auth import _merge_guest_cart, user_exists

REQUIRED_FIELDS = {
    "first_name": "First name",
    "last_name": "Last name",
    "phone": "Phone number",
    "email_id": "Email address",
    "address_line1": "Address line 1",
    "city": "Town / City",
    "country": "Country",
    "pincode": "Postcode",
}


@frappe.whitelist(allow_guest=True)
def register(doc, cart_items=None):
    """
    Self-service sign up: creates the website User (with the chosen password), logs them in,
    then creates their Customer, Contact and billing Address. No approval step.
    """
    doc = frappe.parse_json(doc)
    _validate(doc)

    create_user(data=doc)  # also logs the new user in

    party = _create_customer_records(doc)

    if cart_items:
        try:
            _merge_guest_cart(cart_items)
        except Exception:
            frappe.log_error(title="Register: guest cart merge failed")

    return {"customer": party.name, "full_name": party.customer_name}


def _validate(doc):
    missing = [label for field, label in REQUIRED_FIELDS.items() if not (doc.get(field) or "").strip()]
    if missing:
        frappe.throw(_("Please fill in: {0}").format(", ".join(missing)))

    doc["email_id"] = doc["email_id"].strip().lower()
    if user_exists(doc["email_id"]):
        frappe.throw(_("An account already exists with this email address. Please log in."))

    if not doc.get("password"):
        frappe.throw(_("Please choose a password."))


def _create_customer_records(doc):
    first_name = doc.get("first_name", "").strip()
    last_name = doc.get("last_name", "").strip()
    full_name = f"{first_name} {last_name}".strip()

    address = add_new_address(frappe.as_json({
        "address_title": full_name,
        "address_type": "Billing",
        "address_line1": doc.get("address_line1"),
        "address_line2": doc.get("address_line2"),
        "city": doc.get("city"),
        "country": doc.get("country"),
        "pincode": doc.get("pincode"),
        "phone": doc.get("phone"),
        "email_id": doc.get("email_id"),
    }))

    party = create_party(doc={
        "customer_name": doc.get("company_name") or full_name,
        "mobile_number": doc.get("phone"),
        "customer_email_address": doc.get("email_id"),
        # The profile page finds the customer (and its addresses) through this table.
        "portal_users": [{"user": doc.get("email_id")}],
    })
    create_contact(doc, party.name)
    update_address_with_customer(address.name, party.name)
    return party
