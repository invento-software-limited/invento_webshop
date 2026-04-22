import frappe
from frappe.utils import flt


def _get_existing_payment_request(sales_order: str) -> str | None:
	return frappe.db.get_value(
		"Payment Request",
		{
			"reference_doctype": "Sales Order",
			"reference_name": sales_order,
			"docstatus": 1,
			"status": ("not in", ["Cancelled"]),
		},
		"name",
	)


@frappe.whitelist(allow_guest=True)
def ensure_payment_request(sales_order: str) -> str:
	if not sales_order:
		frappe.throw("Missing sales_order")

	so = frappe.get_doc("Sales Order", sales_order)
	if so.docstatus != 1:
		frappe.throw("Sales Order must be submitted")

	if existing := _get_existing_payment_request(so.name):
		return existing

	from invento_webshop.api.payment_request import make_payment_request

	cart_settings = None
	payment_gateway_account = None
	try:
		cart_settings = frappe.get_doc("Webshop Settings")
		payment_gateway_account = getattr(cart_settings, "payment_gateway_account", None)
	except Exception:
		pass

	if not payment_gateway_account:
		payment_gateway_account = frappe.db.get_value(
			"Payment Gateway Account",
			{"is_default": 1},
			"name",
		)

	if not payment_gateway_account:
		frappe.throw(
			"Payment Gateway Account is not configured. Please create a Payment Gateway Account for 'Lloyds Connect' and set it as Default (is_default=1), or set it in Webshop Settings.",
			title="Payment Gateway Account Missing",
		)

	args = {
		"dt": "Sales Order",
		"dn": so.name,
		"order_type": getattr(so, "order_type", None) or "Shopping Cart",
		"submit_doc": 1,
		"mute_email": 1,
		"return_doc": 1,
	}

	args["payment_gateway_account"] = payment_gateway_account

	recipient_id = getattr(so, "contact_email", None) or getattr(so, "owner", None)
	if recipient_id:
		args["recipient_id"] = recipient_id

	pr = make_payment_request(**args)
	if pr.docstatus == 1 and not getattr(pr, "make_sales_invoice", None):
		frappe.db.set_value(
			"Payment Request",
			pr.name,
			"make_sales_invoice",
			1,
			update_modified=False,
		)
		pr.make_sales_invoice = 1
	elif pr.docstatus == 0:
		pr.make_sales_invoice = 1
		pr.flags.ignore_permissions = True
		pr.save(ignore_permissions=True)
		pr.submit()
	if not getattr(pr, "payment_gateway", None):
		frappe.throw(
			"Payment Request was created without a Payment Gateway. Please ensure the selected Payment Gateway Account is linked to a Payment Gateway (e.g., 'Lloyds Connect').",
			title="Payment Gateway Missing",
		)
	return pr.name


@frappe.whitelist(allow_guest=True)
def get_payment_url(sales_order: str) -> str:
	pr_name = ensure_payment_request(sales_order)
	pr = frappe.get_doc("Payment Request", pr_name)
	return pr.get_payment_url()


@frappe.whitelist(allow_guest=True)
def initiate_quotation_payment(quotation: str) -> None:
	"""
	Create an Integration Request against a submitted Quotation and redirect the
	browser to the Lloyds Connect checkout page.

	Called after place_order returns { pending_card_payment: True, quotation: "QUOT-XXX" }.
	The Sales Order will be created inside _complete_payment_logic once the gateway
	confirms the payment.
	"""
	quot = frappe.get_doc("Quotation", quotation)
	if quot.docstatus != 1:
		frappe.throw("Quotation must be submitted before initiating payment")

	# Resolve Lloyds Connect gateway settings
	gateway_name = frappe.db.get_value("Payment Gateway", {"gateway": "Lloyds Connect"}, "name")
	if not gateway_name:
		frappe.throw("Lloyds Connect Payment Gateway not configured")

	gw_doc = frappe.get_doc("Payment Gateway", gateway_name)
	settings = frappe.get_doc(gw_doc.gateway_settings, gw_doc.gateway_controller)

	from invento_webshop.invento_webshop.doctype.lloyds_connect_settings.lloyds_connect_settings import (
		get_lloyds_txndatetime,
	)
	from frappe.integrations.utils import create_request_log
	from frappe.utils import get_url

	# Resolve payer details
	payer_name = quot.customer_name or quot.party_name or "Guest"
	payer_email = ""
	if quot.contact_person:
		payer_email = frappe.db.get_value(
			"Contact Email", {"parent": quot.contact_person}, "email_id"
		) or ""
	if not payer_email and frappe.session.user != "Guest":
		payer_email = frappe.session.user

	payment_details = {
		"amount": flt(quot.rounded_total or quot.grand_total),
		"title": quot.company,
		"description": f"Payment for {quotation}",
		"reference_doctype": "Quotation",
		"reference_docname": quotation,
		"payer_name": payer_name,
		"payer_email": payer_email,
		"order_id": quotation,
		"currency": quot.currency,
		"payment_gateway": "Lloyds Connect",
		"txndatetime": get_lloyds_txndatetime(settings.timezone),
	}

	integration_request = create_request_log(payment_details, service_name="Lloyds Connect")
	checkout_url = get_url(f"./lloyds_connect_checkout?token={integration_request.name}")

	frappe.local.response["type"] = "redirect"
	frappe.local.response["location"] = checkout_url
