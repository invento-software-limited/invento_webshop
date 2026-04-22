import frappe
from frappe.utils import get_url


@frappe.whitelist()
def start_test_payment():
	from frappe.integrations.utils import create_request_log
	from our_media.our_media.doctype.our_media_lloyds_connect_settings.our_media_lloyds_connect_settings import (
		get_lloyds_txndatetime,
	)

	timezone = frappe.db.get_single_value("System Settings", "time_zone") or "UTC"
	txndatetime = get_lloyds_txndatetime(timezone)

	payment_details = {
		"amount": 1.00,
		"title": "Lloyds Connect Test",
		"description": "Test payment",
		"reference_doctype": "",
		"reference_docname": "",
		"payer_name": "Test User",
		"payer_email": "test@example.com",
		"order_id": "TEST-ORDER",
		"currency": "GBP",
		"payment_gateway": "Lloyds Connect",
		"txndatetime": txndatetime,
	}

	integration_request = create_request_log(payment_details, service_name="Lloyds Connect")
	return get_url(f"/lloyds_connect_checkout?token={integration_request.name}")
