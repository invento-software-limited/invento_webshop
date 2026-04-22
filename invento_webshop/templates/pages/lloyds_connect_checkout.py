import json

import frappe

from invento_webshop.invento_webshop.doctype.lloyds_connect_settings.lloyds_connect_settings import (
	build_request_fields,
)
from invento_webshop.invento_webshop.payments.utils import validate_integration_request

no_cache = 1

expected_keys = (
	"amount",
	"title",
	"description",
	"reference_doctype",
	"reference_docname",
	"payer_name",
	"payer_email",
	"order_id",
	"currency",
	"payment_gateway",
	"txndatetime",
)


def get_context(context):
	context.no_cache = 1
	quotation_to_revert = None

	try:
		validate_integration_request(frappe.form_dict["token"])
		doc = frappe.get_doc("Integration Request", frappe.form_dict["token"])

		payment_details = json.loads(doc.data)
		payment_details["token"] = doc.name

		# Capture early so we can revert on failure
		if payment_details.get("reference_doctype") == "Quotation":
			quotation_to_revert = payment_details.get("reference_docname")

		for key in expected_keys:
			context[key] = payment_details.get(key)

		gateway = frappe.get_doc("Payment Gateway", payment_details.get("payment_gateway"))
		settings = frappe.get_doc(gateway.gateway_settings, gateway.gateway_controller)

		context.gateway_url = settings.get_gateway_processing_url()
		context.fields = build_request_fields(settings, payment_details)

	except Exception:
		frappe.log_error(
			message=frappe.get_traceback(),
			title="Lloyds Connect: Invalid Token",
		)

		# The Quotation was already submitted in place_order before redirect here.
		# If loading the checkout page failed, cancel it so the customer can re-order.
		if quotation_to_revert:
			try:
				quot = frappe.get_doc("Quotation", quotation_to_revert)
				if quot.docstatus == 1:  # still submitted
					quot.flags.ignore_permissions = True
					quot.cancel()
					frappe.db.commit()
			except Exception:
				frappe.log_error(
					message=frappe.get_traceback(),
					title="Lloyds Connect: Failed to Revert Quotation",
				)

		frappe.redirect_to_message(
			"Invalid Token",
			"Seems token you are using is invalid!",
			http_status_code=400,
			indicator_color="red",
		)
		frappe.local.flags.redirect_location = frappe.local.response.location
		raise frappe.Redirect

