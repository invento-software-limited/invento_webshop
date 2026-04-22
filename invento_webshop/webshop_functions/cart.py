import frappe
import json
from frappe import _
from frappe.contacts.doctype.contact.contact import get_contact_name
from frappe.contacts.doctype.address.address import get_address_display
from frappe.utils import cint, cstr, flt, get_fullname
from frappe.utils.nestedset import get_root_of
from erpnext.selling.doctype.quotation.quotation import _make_sales_order
from invento_webshop.api.shipping import calculate_cost


def _get_cart_quotation(party=None, contact=None):
    """
    Retrieve or create a "Shopping Cart" Quotation for the given party and contact.

    If no existing quotation is found, a new one is created with default values.

    Args:
        party (Optional[Party]): The party for the quotation. Defaults to the current user's party.
        contact (Optional[str]): The contact for the quotation. Defaults to the contact linked to the user's email.

    Returns:
        frappe.model.document.Document: The Quotation document.
    """
    if not party:
        party = get_party()

    quotation = frappe.get_all(
        "Quotation",
        fields=["name"],
        filters={
            "party_name": party.name,
            "contact_email": frappe.session.user,
            "order_type": "Shopping Cart",
            "docstatus": 0,
        },
        order_by="modified desc",
        limit_page_length=1,
    )

    if quotation:
        qdoc = frappe.get_doc("Quotation", quotation[0].name)
    else:
        company = frappe.defaults.get_defaults().company
        qdoc = frappe.get_doc(
            {
                "doctype": "Quotation",
                "naming_series": "QTN-CART-",
                "quotation_to": party.doctype,
                "company": company,
                "order_type": "Shopping Cart",
                "status": "Draft",
                "docstatus": 0,
                "__islocal": 1,
                "party_name": party.name,
                "tax_category": party.get("tax_category"),
            }
        )

        if not contact:
            contact_name = get_contact_name(frappe.session.user)
            if contact_name:
                contact = frappe.get_doc("Contact", contact_name)
            else:
                contact = None

        if contact:
            contact_name = getattr(contact, "name", contact)
            qdoc.contact_person = contact_name
            email = frappe.get_value("Contact Email", {"parent": contact_name, "is_primary": 1}, "email_id")
            if email: qdoc.contact_email = email

            phone = frappe.get_value("Contact Phone", {"parent": contact_name, "is_primary_phone": 1}, "phone")
            if phone: qdoc.contact_mobile = phone

        qdoc.flags.ignore_permissions = True
        qdoc.run_method("set_missing_values")

    return qdoc


@frappe.whitelist(allow_guest=True)
def update_cart(item_code, qty, additional_notes=None, cart_items=None):
    """
    Update the shopping cart for the guest or logged-in user.

    - For guest users, cart items are stored in cookies and updated accordingly.
    - For logged-in users, the cart is managed through an existing Quotation.

    Args:
        item_code (str): The code of the item to update.
        qty (int or float): The quantity of the item.
        additional_notes (Optional[str]): Additional notes for the item.
        cart_items (Optional[List[dict]]): The cart items (for guest users).

    Returns:
        dict: A dictionary containing the updated cart or quotation name.
    """

    if cart_items is None:
        cart_items = []
    if frappe.session.user == "Guest":
        """Updates the cart stored in cookies for guest users"""

        cart_items = json.loads(cart_items) if cart_items else []

        existing_item = next((item for item in cart_items if item["item_code"] == item_code), None)

        item_price = frappe.db.get_value("Item Price", {"item_code": item_code, "selling": 1}, "price_list_rate")
        if existing_item:
            existing_item["qty"] += int(qty)
        else:
            cart_items.append(
                {"item_code": item_code, "qty": int(qty),
                 "price": flt(item_price),
                 "notes": additional_notes})

        frappe.local.cookie_manager.set_cookie("cart_items", json.dumps(cart_items))
        set_cart_count(cart_items=cart_items)

        return {"name": cart_items}

    quotation = _get_cart_quotation()

    empty_card = False
    qty = flt(qty)
    if qty == 0:
        quotation_items = quotation.get("items", {"item_code": ["!=", item_code]})
        if quotation_items:
            quotation.set("items", quotation_items)
        else:
            empty_card = True

    else:
        quotation_items = quotation.get("items", {"item_code": item_code})
        if not quotation_items:
            quotation.append(
                "items",
                {
                    "doctype": "Quotation Item",
                    "item_code": item_code,
                    "qty": qty,
                    "additional_notes": additional_notes
                },
            )
        else:
            quotation_items[0].qty += qty
            quotation_items[0].additional_notes = additional_notes

    quotation.flags.ignore_permissions = True
    quotation.payment_schedule = []
    if not empty_card:
        quotation.save(ignore_version=True)
    else:
        quotation.delete()
        quotation = None

    set_cart_count(quotation=quotation)

    return {"name": quotation.name}


def get_party(user=None):
    """
    Retrieve the party (Customer or Supplier) associated with the given user.

    If the user doesn't have an associated party, a new Customer and Contact record is created.

    Args:
        user (Optional[str]): The user for whom the party is to be fetched. Defaults to the current session user.

    Returns:
        frappe.model.document.Document: The associated Customer or Supplier document, or a new Customer document if no existing party is found.
    """
    if not user:
        user = frappe.session.user

    contact_name = get_contact_name(user)
    party = None

    if contact_name:
        contact = frappe.get_doc("Contact", contact_name)
        if contact.links:
            party_doctype = contact.links[0].link_doctype
            party = contact.links[0].link_name

    if party:
        doc = frappe.get_doc(party_doctype, party)
        if doc.doctype in ["Customer", "Supplier"]:
            if not frappe.db.exists("Portal User", {"parent": doc.name, "user": user}):
                doc.append("portal_users", {"user": user})
                doc.flags.ignore_permissions = True
                doc.flags.ignore_mandatory = True
                doc.save()

        return doc

    else:

        customer = frappe.new_doc("Customer")
        fullname = get_fullname(user)
        customer.update(
            {
                "customer_name": fullname,
                "customer_type": "Individual",
                "territory": get_root_of("Territory"),
            }
        )

        customer.append("portal_users", {"user": user})

        customer.flags.ignore_mandatory = True
        customer.insert(ignore_permissions=True)

        contact = frappe.new_doc("Contact")
        contact.update(
            {"first_name": fullname, "email_ids": [{"email_id": user, "is_primary": 1}]}
        )
        contact.append("links", dict(link_doctype="Customer", link_name=customer.name))
        contact.flags.ignore_mandatory = True
        contact.insert(ignore_permissions=True)

        return customer


def set_cart_count(quotation=None, cart_items=None):
    """
    Set the cart item count in cookies for guest users or based on the Quotation for logged-in users.

    Args:
        quotation (Optional[frappe.model.document.Document]): The Quotation document for logged-in users.
        cart_items (Optional[List[dict]]): The cart items for guest users.

    Returns:
        int: The total item count in the cart.
    """

    if cart_items is None:
        cart_items = []
    if not quotation and frappe.session.user != "Guest":
        quotation = _get_cart_quotation()

    if frappe.session.user == "Guest":
        cart_count = sum(item.get("qty", 0) for item in cart_items)
        total_amount = sum(flt(item.get("qty", 0)) * flt(item.get("price", 0)) for item in cart_items)

    else:
        cart_count = cint(quotation.get("total_qty"))
        total_amount = flt(quotation.get("grand_total"))

    default_currency = frappe.db.get_single_value("Global Defaults", "default_currency")
    total_amount = frappe.utils.fmt_money(total_amount, currency=default_currency)
    if hasattr(frappe.local, "cookie_manager"):
        frappe.local.cookie_manager.set_cookie("cart_count", cstr(cart_count))
        frappe.local.cookie_manager.set_cookie("cart_total", cstr(total_amount))

    return cart_count




@frappe.whitelist(allow_guest=True)
def get_cart_items(quotation=None):
    """
    Retrieve the list of items in the cart for the guest or logged-in user.

    Args:
        quotation (Optional[frappe.model.document.Document]): The Quotation document for logged-in users.

    Returns:
        list: A list of dictionaries containing item details (name, code, quantity, image) for each cart item.
    """
    default_currency = frappe.db.get_single_value("Global Defaults", "default_currency")

    if frappe.session.user != "Guest":
        if not quotation:
            quotation = _get_cart_quotation()
            set_cart_count(quotation=quotation)
        return get_cart_items_for_logged_in_user(quotation, default_currency)

    elif frappe.session.user == "Guest":
        return get_cart_items_for_guest_user(default_currency)


@frappe.whitelist(allow_guest=True)
def get_order_details(quotation=None, cart_items=None):
    """
    Calculate and return the order details for both logged-in and guest users.

    Args:
        quotation (Optional[frappe.model.document.Document]): The Quotation document for logged-in users.
        cart_items (Optional[list]): List of cart items for guest users.

    Returns:
        dict: Order details such as taxes, totals, etc.
    """
    if frappe.session.user != "Guest":
        if not quotation:
            quotation = _get_cart_quotation()
        return calculate_taxes_and_totals(quotation=quotation) if len(quotation.get("items")) > 0 else None

    elif frappe.session.user == "Guest":
        if isinstance(cart_items, str):
            cart_items = frappe.parse_json(cart_items)
        return calculate_taxes_and_totals(cart_items=cart_items)


def get_cart_items_for_logged_in_user(quotation, default_currency):
    """Helper function to get cart items for logged-in users."""
    return [
        {
            "item_name": item.item_name,
            "item_code": item.item_code,
            "qty": item.qty,
            "image": item.image if item.image else '',
            "rate": frappe.utils.fmt_money(item.rate, currency=default_currency),
            "amount": frappe.utils.fmt_money(item.amount, currency=default_currency),
        }
        for item in quotation.get("items", [])
    ]


def get_cart_items_for_guest_user(default_currency):
    """Helper function to get cart items for guest users."""
    cart_items = frappe.local.request.args.get('cart_items')

    if cart_items:
        cart_items = json.loads(cart_items)
    else:
        cart_items = []

    modified_cart_items = []

    for item in cart_items:
        item_details = frappe.get_cached_doc("Item", item.get("item_code"))

        item_dict = {
            "item_name": item_details.item_name,
            "item_code": item_details.item_code,
            "qty": item.get("qty"),
            "image": item_details.image if item_details.image else '',
            "rate": frappe.utils.fmt_money(item.get("price", 0), currency=default_currency),
            "amount": frappe.utils.fmt_money(item.get("price", 0) * item.get('qty', 0), currency=default_currency),
        }

        modified_cart_items.append(item_dict)

    return modified_cart_items


@frappe.whitelist(allow_guest=True)
def update_cart_qty(item_code, qty, action, cart_items=None, quotation=None):
    """
    Update the quantity of an item in the cart for the guest or logged-in user.

    - For guest users, the cart is updated in cookies.
    - For logged-in users, the cart is updated in the associated Quotation.

    Args:
        item_code (str): The code of the item to update.
        qty (int): The quantity to add, remove, or set.
        action (str): The action to perform ("add", "remove", or "delete").
        cart_items (Optional[List[dict]]): The cart items for guest users.
        quotation (Optional[frappe.model.document.Document]): The Quotation document for logged-in users.

    Returns:
        list: The updated list of cart items.
    """
    if frappe.session.user == "Guest":
        if cart_items:
            cart_items = json.loads(cart_items)
        else:
            cart_items = []
        qty = int(qty)
        item_found = False
        for item in cart_items:
            if item["item_code"] == item_code:
                item_found = True
                if action == "add":
                    item["qty"] += qty
                elif action == "remove":
                    item["qty"] -= qty
                    if item["qty"] < 1:
                        cart_items.remove(item)
                elif action == "delete":
                    cart_items.remove(item)
                break

        if not item_found and action == "add":
            cart_items.append({
                "item_code": item_code,
                "qty": qty
            })
        frappe.local.cookie_manager.set_cookie("cart_items", json.dumps(cart_items))
    else:
        empty_card = False
        if not quotation:
            quotation = _get_cart_quotation()

        if not quotation:
            return []

        existing_item = next((item for item in quotation.items if item.item_code == item_code), None)

        if existing_item:
            if action == "add":
                existing_item.qty += int(qty)
            elif action == "remove":
                existing_item.qty -= qty
                if existing_item.qty < 1:
                    quotation.items.remove(existing_item)
            elif action == "delete":
                quotation.items.remove(existing_item)
        else:
            if action == "add":
                quotation.append("items", {
                    "item_code": item_code,
                    "qty": int(qty)
                })

        if len(quotation.get('items')) == 0:
            quotation.delete(ignore_permissions=True)
        else:
            quotation.save(ignore_version=True, ignore_permissions=True)
            frappe.db.commit()
            cart_items = quotation.items

    set_cart_count(cart_items=cart_items)
    return cart_items


@frappe.whitelist()
def get_shipping_addresses(party=None):
    """
    Retrieve the list of shipping addresses for the given party.

    Args:
        party (Optional[frappe.model.document.Document]): The party for whom the shipping addresses are fetched. Defaults to the current user's party.

    Returns:
        list: A list of dictionaries containing the name, title, and display of each shipping address.
    """
    if not party:
        party = get_party()
    addresses = get_address_docs(party=party)
    return [
        {
            "name": address.name,
            "title": address.address_title,
            "display": address.display,
        }
        for address in addresses
        if address.address_type == "Shipping"
    ]


@frappe.whitelist()
def get_billing_addresses(party=None):
    """
    Retrieve the list of billing addresses for the given party.

    Args:
        party (Optional[frappe.model.document.Document]): The party for whom the billing addresses are fetched. Defaults to the current user's party.

    Returns:
        list: A list of dictionaries containing the name, title, and display of each billing address.
    """
    if not party:
        party = get_party()
    addresses = get_address_docs(party=party)
    return [
        {
            "name": address.name,
            "title": address.address_title,
            "display": address.display,
        }
        for address in addresses
        if address.address_type == "Billing"
    ]


def get_address_docs(
    doctype=None,
    txt=None,
    filters=None,
    limit_start=0,
    limit_page_length=20,
    party=None,
):
    """
    Retrieve address documents associated with the given party.

    Args:
        doctype (Optional[str]): The doctype to filter the addresses by.
        txt (Optional[str]): Search term for filtering address fields.
        filters (Optional[dict]): Additional filters to apply to the address query.
        limit_start (int): The starting index for the address query.
        limit_page_length (int): The number of addresses to return.
        party (Optional[frappe.model.document.Document]): The party for which to retrieve the addresses. Defaults to the current user's party.

    Returns:
        list: A list of Address documents associated with the party.
    """
    if not party:
        party = get_party()

    if not party:
        return []

    address_names = frappe.db.get_all(
        "Dynamic Link",
        fields=("parent"),
        filters=dict(
            parenttype="Address", link_doctype=party.doctype, link_name=party.name
        ),
    )

    out = []

    for a in address_names:
        address = frappe.get_doc("Address", a.parent)
        address.display = get_address_display(address.as_dict())
        out.append(address)

    return out


@frappe.whitelist()
def add_new_address(doc):
    """
    Add a new address for the given document.

    Args:
        doc (str): The address data as a JSON string to be parsed and saved as an Address document.

    Returns:
        frappe.model.document.Document: The saved Address document.
    """
    doc = frappe.parse_json(doc)
    doc.update({"doctype": "Address"})
    address = frappe.get_doc(doc)
    address.save(ignore_permissions=True)

    return address


@frappe.whitelist()
def update_cart_address(address_type, address_name, quotation=None):
    """
    Update the billing or shipping address in the cart for the given quotation.

    Args:
        address_type (str): The type of address to update ("billing" or "shipping").
        address_name (str): The name of the address to set.
        quotation (Optional[frappe.model.document.Document]): The Quotation document. Defaults to the current cart quotation.

    Returns:
        None
    """
    if not quotation:
        quotation = _get_cart_quotation()
    address_doc = frappe.get_doc("Address", address_name).as_dict()
    address_display = get_address_display(address_doc)

    if address_type.lower() == "billing":
        quotation.customer_address = address_name
        quotation.address_display = address_display
        quotation.shipping_address_name = (
            quotation.shipping_address_name or address_name
        )
        address_doc = next(
            (doc for doc in get_billing_addresses() if doc["name"] == address_name),
            None,
        )
    elif address_type.lower() == "shipping":
        quotation.shipping_address_name = address_name
        quotation.shipping_address = address_display
        quotation.customer_address = quotation.customer_address or address_name
    
    quotation.run_method("calculate_taxes_and_totals")
    quotation.payment_schedule = []  # prevent set_payment_schedule crash when grand_total is None
    quotation.save(ignore_permissions=True)
    # Reload to keep the in-memory `modified` timestamp in sync with the DB.
    # Without this, a second call to update_cart_address (e.g. billing then shipping
    # in place_order) will fail Frappe's optimistic lock check with MySQL error 1020
    # (QueryDeadlockError: "Record has changed since last read").
    quotation.reload()
    return calculate_taxes_and_totals(quotation=quotation)


@frappe.whitelist(allow_guest=True)
def place_order(doc=None, cart_items=None):
    if frappe.session.user == "Guest" and doc:
        doc = frappe.parse_json(doc)
        create_user(data=doc)
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
            contact = create_contact(doc, party.name)
            quotation = _get_cart_quotation(party=party, contact=contact)
            if address:
                update_address_with_customer(address.name, party.name)
                update_cart_address(address_type=address.address_type, address_name=address.name,
                                    quotation=quotation)

            if not doc.get('deliver_same'):
                required_fields = ['deliver_address_line_1', 'deliver_town', 'deliver_country', 'deliver_postcode',
                                   'phone', 'email_id']

                # Ensure required fields are available
                missing_fields = [field for field in required_fields if not doc.get(field)]
                if missing_fields:
                    frappe.throw(
                        _("Missing required fields for delivery address: {0}").format(", ".join(missing_fields)))

                deliver_address_json = {
                    'address_title': address_title,
                    'address_line1': doc.get('deliver_address_line_1', ''),
                    'address_line2': doc.get('deliver_address_line_2', ''),
                    'city': doc.get('deliver_town', ''),
                    'country': doc.get('deliver_country', ''),
                    'pincode': doc.get('deliver_postcode', ''),
                    'state': doc.get('deliver_state', ''),
                    'address_type': 'Shipping',
                    'phone': doc.get('phone', ''),
                    'email_id': doc.get('email_id', '')
                }

                deliver_address = add_new_address(frappe.as_json(deliver_address_json))

                if deliver_address:
                    update_address_with_customer(deliver_address.name, party.name)
                    update_cart_address(
                        address_type=deliver_address.address_type,
                        address_name=deliver_address.name,
                        quotation=quotation
                    )
                else:
                    frappe.throw(_("Failed to create the delivery address."))

            cart_items = frappe.parse_json(cart_items) if cart_items else []
            if cart_items:
                add_items_to_quotation(quotation, cart_items)

    else:
        quotation = _get_cart_quotation()
        party = get_party()
        if doc.get('deliver_same'):
            update_cart_address('Billing', doc.get('billing_address'), quotation)
            update_cart_address('Shipping', doc.get('billing_address'), quotation)
        else:
            update_cart_address('Billing', doc.get('billing_address'), quotation)
            update_cart_address('Shipping', doc.get('shipping_address'), quotation)

    if not quotation:
        frappe.throw(_("Quotation could not be created"))

    set_price_list_and_rate(quotation)
    # Use custom calculate_taxes_and_totals function to apply both taxes and shipping
    calculate_taxes_and_totals(quotation=quotation)
    # _apply_shipping_rule(party, quotation)

    quotation.flags.ignore_permissions = True
    quotation.submit()

    # Card payment: SO is created AFTER payment is confirmed by the gateway.
    # Return now so the frontend can redirect to the payment page.
    if doc.get('mode_of_payment') == "Pay with Card":
        return {
            "quotation": quotation.name,
            "pending_card_payment": True,
        }

    if quotation.quotation_to == "Lead" and quotation.party_name:
        frappe.defaults.set_user_default("company", quotation.company)

    if not (quotation.shipping_address_name or quotation.customer_address):
        frappe.throw(_("Set Shipping Address or Billing Address"))

    sales_order = frappe.get_doc(
        _make_sales_order(
            quotation.name, ignore_permissions=True
        )
    )
    sales_order.payment_schedule = []

    sales_order.flags.ignore_permissions = True
    sales_order.insert()
    sales_order.submit()

    if hasattr(frappe.local, "cookie_manager"):
        frappe.local.cookie_manager.delete_cookie("cart_count")
        frappe.local.cookie_manager.delete_cookie("cart_total")

    return {
        "name": sales_order.name,
        "items": sales_order.items
    }

def create_party(doc):
    """
    Create and save a new Customer party based on the provided details.

    Args:
        doc (dict): The customer details to create the party.

    Returns:
        frappe.model.document.Document: The created Customer document.
    """
    doc.update({"doctype": "Customer"})
    party = frappe.get_doc(doc)
    party.save(ignore_permissions=True)

    return party


def update_address_with_customer(address_name, customer_name):
    """
    Link an existing Address to the specified Customer.

    Args:
        address_name (str): The name of the address to update.
        customer_name (str): The name of the customer to link the address to.

    Returns:
        None
    """
    address_doc = frappe.get_doc("Address", address_name)
    address_doc.append("links", {
        "link_doctype": "Customer",
        "link_name": customer_name
    })
    address_doc.save(ignore_permissions=True)


def create_contact(doc, customer_name):
    """
    Create a Contact and link it to the specified Customer.

    Args:
        doc (dict): The contact details (full name, email, and phone).
        customer_name (str): The name of the customer to link the contact to.

    Returns:
        frappe.model.document.Document: The created Contact document.
    """
    contact_doc = frappe.get_doc({
        "doctype": "Contact",
        "first_name": doc.get("first_name"),
        "last_name": doc.get("last_name"),
        "company_name": doc.get("company_name"),
        "is_primary_contact": 1,
        "email_ids": [{
            "email_id": doc.get("email_id"),
            "is_primary": 1
        }],
        "phone_nos": [{
            "phone": doc.get("phone"),
            "is_primary_phone": 1,
            "is_primary_mobile_no": 1
        }],
        "links": [{
            "link_doctype": "Customer",
            "link_name": customer_name
        }]
    })
    contact_doc.insert(ignore_permissions=True)
    return contact_doc


def add_items_to_quotation(quotation, cart_items):
    """
    Add items from the cart to a Quotation document.

    Args:
        quotation (frappe.model.document.Document): The Quotation to add items to.
        cart_items (list): A list of cart items, each containing item code and quantity.

    Returns:
        None
    """
    for item in cart_items:
        quotation.append(
            "items",
            {
                "doctype": "Quotation Item",
                "item_code": item.get("item_code"),
                "qty": item.get("qty", 1),
            },
        )
    quotation.run_method("set_missing_values")
    quotation.save(ignore_permissions=True, ignore_version=True)
    frappe.local.cookie_manager.set_cookie("cart_items", [])
    set_cart_count(cart_items=[])


def set_price_list_and_rate(quotation):
    """
    Set the price list and rates for the given Quotation based on the billing territory.

    Args:
        quotation (frappe.model.document.Document): The Quotation document to update.

    Returns:
        None
    """

    set_default_price_list(quotation)

    quotation.price_list_currency = (
        quotation.currency
    ) = quotation.plc_conversion_rate = quotation.conversion_rate = None

    for item in quotation.get("items"):
        item.price_list_rate = item.discount_percentage = item.rate = item.amount = None

    quotation.run_method("set_price_list_and_item_details")

    if hasattr(frappe.local, "cookie_manager"):
        frappe.local.cookie_manager.set_cookie(
            "selling_price_list", quotation.selling_price_list
        )


def set_default_price_list(quotation=None):
    """
    Set the default price list for the given Quotation based on the customer's defaults.

    Args:
        quotation (Optional[frappe.model.document.Document]): The Quotation document to update.

    Returns:
        str: The name of the selling price list.
    """
    from erpnext.accounts.party import get_default_price_list

    party_name = quotation.get("party_name") if quotation else get_party().get("name")
    selling_price_list = None

    if party_name and frappe.db.exists("Customer", party_name):
        selling_price_list = get_default_price_list(frappe.get_doc("Customer", party_name))

    if not selling_price_list:
        selling_price_list = frappe.defaults.get_defaults().get("selling_price_list")

    if quotation:
        quotation.selling_price_list = selling_price_list

    return selling_price_list


def set_taxes(quotation):
    """
    Set taxes for the given Quotation based on the billing territory.

    Args:
        quotation (frappe.model.document.Document): The Quotation document to set taxes for.

    Returns:
        None
    """
    from erpnext.accounts.party import set_taxes

    customer_group = frappe.db.get_value(
        "Customer", quotation.party_name, "customer_group"
    )

    quotation.taxes_and_charges = set_taxes(
        quotation.party_name,
        "Customer",
        quotation.transaction_date,
        quotation.company,
        customer_group=customer_group,
        supplier_group=None,
        tax_category=quotation.tax_category,
        billing_address=quotation.customer_address,
        shipping_address=quotation.shipping_address_name,
        use_for_shopping_cart=1,
    )
    #
    # 	# clear table
    quotation.set("taxes", [])
    #
    # 	# append taxes
    quotation.append_taxes_from_master()
    quotation.append_taxes_from_item_tax_template()


def get_shipping_rules(quotation=None):
    """
    Get applicable shipping rules based on the shipping address of the given Quotation.

    Args:
        quotation (Optional[frappe.model.document.Document]): The Quotation document to check for shipping rules.

    Returns:
        list: A list of applicable shipping rule names.
    """
    if not quotation:
        quotation = _get_cart_quotation()

    shipping_rules = []
    if quotation.shipping_address_name:
        country = frappe.db.get_value(
            "Address", quotation.shipping_address_name, "country"
        )
        if country:
            sr_country = frappe.qb.DocType("Shipping Rule Country")
            sr = frappe.qb.DocType("Shipping Rule")
            query = (
                frappe.qb.from_(sr_country)
                .join(sr)
                .on(sr.name == sr_country.parent)
                .select(sr.name)
                .distinct()
                .where((sr_country.country == country) & (sr.disabled != 1))
            )
            result = query.run(as_list=True)
            shipping_rules = [x[0] for x in result]

    return shipping_rules


def _apply_shipping_rule(party=None, quotation=None):
    if not quotation.shipping_rule:
        from invento_webshop.api.shipping import get_shipping_methods
        shipping_address = frappe.get_doc("Address", quotation.shipping_address_name) if quotation.shipping_address_name else None
        postcode = shipping_address.pincode if shipping_address else None
        
        if postcode:
            methods = get_shipping_methods(postcode)
            if methods:
                # Default to the first one if none selected
                quotation.shipping_rule = methods[0]["name"]

    if quotation.shipping_rule:
        rule_doc = frappe.get_doc("Shipping Rule", quotation.shipping_rule)
        net_total = flt(quotation.total)
        
        total_weight = 0
        for item in quotation.items:
            weight = frappe.db.get_value("Item", item.item_code, "weight_per_unit") or 0
            total_weight += flt(weight) * item.qty
            
        actual_cost = calculate_cost(rule_doc, net_total, total_weight)

        # Row 1: Shipping Cost
        quotation.append("taxes", {
            "charge_type": "Actual",
            "account_head": rule_doc.account,
            "tax_amount": actual_cost,
            "base_tax_amount": actual_cost,
            "description": rule_doc.label,
            "cost_center": rule_doc.cost_center or "Main - SWF"
        })

        # Row 2: VAT on Shipping (On Previous Row Total)
        quotation.append("taxes", {
            "charge_type": "On Previous Row Total",
            "row_id": len(quotation.taxes),
            "account_head": "VAT - SWF",
            "description": f"VAT",
            "cost_center": rule_doc.cost_center or "Main - SWF"
        })


def calculate_taxes_and_totals(quotation=None, cart_items=None):
    total_weight = total_price = 0
    total_excluded_tax = total_included_tax = 0
    order_summary = []
    default_currency = frappe.db.get_single_value("Global Defaults", "default_currency")
    tax_template_name = None
    if quotation:
        if quotation.tax_category:
            tax_template_name = quotation.taxes_and_charges or frappe.db.get_value("Sales Taxes and Charges Template", {"is_default": 1})
        else:
            tax_template_name = None
    else:
        tax_template_name = frappe.db.get_value("Sales Taxes and Charges Template", {"is_default": 1})

    tax_template = frappe.get_cached_doc("Sales Taxes and Charges Template", tax_template_name) if tax_template_name else None
    tax_template_taxes = tax_template.taxes if tax_template else []

    shipping_rule_data = frappe.get_all(
        "Shipping Rule",
        filters={
            "shipping_rule_type": "Selling",
            "calculate_based_on": "Net Weight",
            "disabled": 0
        },
        fields=["name"],
        limit=1
    )

    shipping_rule = None
    if shipping_rule_data:
        shipping_rule = frappe.get_cached_doc("Shipping Rule", shipping_rule_data[0].name)

    if frappe.session.user == "Guest":
        if not cart_items:
            cart_items = []

        for item in cart_items:
            item_code = item.get("item_code")
            qty = item.get("qty", 1)
            price = item.get("price", 0)

            weight_per_unit = frappe.db.get_value("Item", item_code, "weight_per_unit") or 0
            total_weight += flt(weight_per_unit) * qty
            total_price += flt(price) * qty

        # Apply shipping rule for guest
        if shipping_rule:
            for condition in shipping_rule.conditions:
                if condition.from_value <= total_weight <= condition.to_value:
                    shipping_charge = condition.shipping_amount
                    total_excluded_tax += shipping_charge
                    order_summary.append({
                        "description": shipping_rule.name,
                        "tax_amount": frappe.utils.fmt_money(shipping_charge, currency=default_currency),
                        "included_in_price": 0
                    })
                    break

        # Apply tax template
        for tax_row in tax_template_taxes:
            if tax_row.charge_type == "On Net Total":
                tax_rate = flt(tax_row.rate) / 100

                if tax_row.included_in_print_rate:
                    included_tax = total_price - (total_price / (1 + tax_rate))
                    total_included_tax += included_tax
                else:
                    excluded_tax = total_price * tax_rate
                    total_excluded_tax += excluded_tax

                order_summary.append({
                    "description": tax_row.description,
                    "tax_amount": frappe.utils.fmt_money(
                        included_tax if tax_row.included_in_print_rate else excluded_tax,
                        currency=default_currency
                    ),
                    "included_in_price": tax_row.included_in_print_rate
                })

        grand_total = total_price + total_excluded_tax

    else:
        if not quotation:
            quotation = _get_cart_quotation()

        quotation.set("taxes", [])

        # Always apply tax template
        for tax_row in tax_template_taxes:
            tax_row_dict = {
                "charge_type": tax_row.charge_type,
                "account_head": tax_row.account_head,
                "rate": tax_row.rate,
                "description": tax_row.description,
                "included_in_print_rate": tax_row.included_in_print_rate,
                "tax_amount": tax_row.tax_amount,
            }
            quotation.append("taxes", tax_row_dict)

        # Apply custom shipping rule logic (appends two more rows if rule exists)
        _apply_shipping_rule(quotation=quotation)

        quotation.run_method("calculate_taxes_and_totals")
        quotation.save(ignore_permissions=True, ignore_version=True)
        frappe.db.commit()

        total_price = flt(quotation.get("total"))
        grand_total = flt(quotation.get("grand_total"))

        shipping_account = None
        if quotation and quotation.shipping_rule:
            shipping_account = frappe.db.get_value("Shipping Rule", quotation.shipping_rule, "account")

        for tax_row in quotation.get('taxes'):
            item = {
                "description": tax_row.description,
                "tax_amount": frappe.utils.fmt_money(tax_row.base_tax_amount, currency=default_currency),
                "included_in_price": tax_row.included_in_print_rate
            }
            if shipping_account and tax_row.account_head == shipping_account:
                item["is_shipping"] = True
            
            order_summary.append(item)

    # Get available shipping rules for selection
    from invento_webshop.api.shipping import get_shipping_methods
    shipping_address_name = quotation.shipping_address_name if quotation else None
    postcode = None
    if shipping_address_name:
        postcode = frappe.db.get_value("Address", shipping_address_name, "pincode")
    
    available_shipping_rules = []
    if postcode:
        available_shipping_rules = get_shipping_methods(postcode)

    return {
        "total_price": frappe.utils.fmt_money(total_price, currency=default_currency),
        "grand_total": frappe.utils.fmt_money(grand_total, currency=default_currency),
        "order_summary": order_summary,
        "available_shipping_rules": available_shipping_rules,
        "selected_shipping_rule": quotation.shipping_rule if quotation else None
    }

def create_user(data):
    password = data.get('password')
    confirm_password = data.get('confirm_password')

    if password != confirm_password:
        frappe.throw("Passwords do not match.")

    if len(password) < 8:
        frappe.throw("Password must be at least 8 characters long.")

    user = frappe.get_doc({
        "doctype": "User",
        "first_name": data.get('first_name'),
        "last_name": data.get('last_name'),
        "email": data.get('email_id'),
        "phone": data.get('phone'),
        "mobile_no": data.get('mobile_no'),
        "enabled": 1,
        "user_type": "Website User",
        "new_password": password
    })

    # Insert the user document
    user.insert(ignore_permissions=True)
    frappe.db.commit()
    if user.get("email") and hasattr(frappe.local, "login_manager"):
        frappe.local.login_manager.login_as(user.get("email"))
    return user