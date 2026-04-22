import base64
from configparser import NoOptionError
import hashlib
import hmac
import json
from urllib.parse import urlencode

from werkzeug.wrappers import Response

import frappe
import pytz
from frappe.model.document import Document
from frappe.utils import get_url, now_datetime

from invento_webshop.invento_webshop.payments.utils import create_payment_gateway


class LloydsConnectSettings(Document):
	def validate(self):
		try:
			create_payment_gateway(
				"Lloyds Connect",
				settings="Lloyds Connect Settings",
				controller=self.name,
			)
		except Exception:
			frappe.log_error(
				message=frappe.get_traceback(),
				title="Lloyds Connect: Gateway Setup",
			)
			frappe.msgprint(
				(
					"Could not auto-create/update Payment Gateway 'Lloyds Connect'. "
					"This usually means the 'Payment Gateway' DocType is missing or misconfigured on this site. "
					"You can still save these settings; please create/configure the Payment Gateway manually."
				),
				indicator="orange",
			)

	def validate_transaction_currency(self, currency):
		get_numeric_currency_code(currency)

	def get_gateway_processing_url(self):
		if self.use_test_environment:
			return self.test_gateway_url
		return self.live_gateway_url

	def get_payment_url(self, **kwargs):
		from frappe.integrations.utils import create_request_log

		txndatetime = get_lloyds_txndatetime(self.timezone)
		kwargs = dict(kwargs)
		kwargs["txndatetime"] = txndatetime

		integration_request = create_request_log(kwargs, service_name="Lloyds Connect")
		return get_url(f"./lloyds_connect_checkout?token={integration_request.name}")


def _hmac_base64(hash_algorithm: str, key: str, message: str) -> str:
	algo_map = {
		"HMACSHA256": hashlib.sha256,
		"HMACSHA384": hashlib.sha384,
		"HMACSHA512": hashlib.sha512,
	}
	digestmod = algo_map.get((hash_algorithm or "").upper())
	if not digestmod:
		raise frappe.ValidationError(f"Unsupported hash algorithm: {hash_algorithm}")

	mac = hmac.new(key=key.encode("utf-8"), msg=message.encode("utf-8"), digestmod=digestmod)
	return base64.b64encode(mac.digest()).decode("utf-8")


def get_lloyds_txndatetime(timezone: str) -> str:
	dt = now_datetime()
	try:
		tz = pytz.timezone(timezone)
		dt = dt.astimezone(tz)
	except Exception:
		pass
	return dt.strftime("%Y:%m:%d-%H:%M:%S")


def get_numeric_currency_code(currency: str) -> str:
	mapping = {
		"BDT": "050",
		"USD": "840",
		"EUR": "978",
		"GBP": "826",
		"INR": "356",
		"AED": "784",
		"AUD": "036",
		"JPY": "392",
		"CNY": "156",
		"CHF": "756",
	}
	code = mapping.get((currency or "").upper())
	if not code:
		raise frappe.ValidationError(f"Unsupported currency for Lloyds Connect: {currency}")
	return code


def build_request_fields(settings: LloydsConnectSettings, payment_details: dict) -> dict:
	currency_numeric = get_numeric_currency_code(payment_details.get("currency"))

	fields = {
		"storename": settings.store_name,
		"txndatetime": payment_details.get("txndatetime"),
		"chargetotal": str(payment_details.get("amount")),
		"currency": currency_numeric,
		"checkoutoption": settings.checkout_option or "combinedpage",
		"timezone": settings.timezone,
		"txntype": (settings.txn_type or "sale").lower(),
		"hash_algorithm": settings.hash_algorithm,
		"responseSuccessURL": get_url(
			"/api/method/invento_webshop.invento_webshop.doctype.lloyds_connect_settings.lloyds_connect_settings.response_success"
		),
		"responseFailURL": get_url(
			"/api/method/invento_webshop.invento_webshop.doctype.lloyds_connect_settings.lloyds_connect_settings.response_fail"
		),
		"transactionNotificationURL": get_url(
			"/api/method/invento_webshop.invento_webshop.doctype.lloyds_connect_settings.lloyds_connect_settings.transaction_notification"
		),
		"merchantTransactionId": payment_details.get("token"),
		"oid": payment_details.get("order_id") or payment_details.get("reference_docname"),
	}

	if settings.payment_method:
		fields["paymentMethod"] = settings.payment_method

	hash_params = {k: v for k, v in fields.items() if v not in (None, "") and k != "hashExtended"}
	sorted_keys = sorted(hash_params.keys())
	string_to_hash = "|".join(str(hash_params[k]) for k in sorted_keys)
	fields["hashExtended"] = _hmac_base64(
		settings.hash_algorithm,
		settings.get_password(fieldname="shared_secret", raise_exception=True),
		string_to_hash,
	)

	return fields


def _get_settings_for_token(token: str) -> LloydsConnectSettings:
	integration_request = frappe.get_doc("Integration Request", token)
	data = json.loads(integration_request.data)
	payment_gateway = data.get("payment_gateway")
	if not payment_gateway:
		raise frappe.ValidationError("Missing payment_gateway in Integration Request")

	gateway = frappe.get_doc("Payment Gateway", payment_gateway)
	if gateway.gateway_settings != "Lloyds Connect Settings":
		raise frappe.ValidationError("Integration Request is not for Lloyds Connect")

	if not gateway.gateway_controller:
		raise frappe.ValidationError("Missing gateway controller for Lloyds Connect")

	return frappe.get_doc("Lloyds Connect Settings", gateway.gateway_controller)


def _finalize_payment(token: str, status: str, response_data: dict) -> str:
	_complete_payment_logic(token, status, response_data)

	integration_request = frappe.get_doc("Integration Request", token)
	request_data = json.loads(integration_request.data)

	reference_doctype = request_data.get("reference_doctype")
	reference_docname = request_data.get("reference_docname")

	redirect_to = request_data.get("redirect_to")
	redirect_message = request_data.get("redirect_message")

	if status == "Completed" and reference_doctype and reference_docname:
		if reference_doctype == "Quotation":
			# SO was created in _complete_payment_logic; name stored in frappe.flags
			so_name = getattr(frappe.flags, "card_payment_so_name", reference_docname)
			redirect_url = f"payment-success?doctype=Sales Order&docname={so_name}"
		else:
			redirect_url = f"payment-success?doctype={reference_doctype}&docname={reference_docname}"
	else:
		redirect_url = "payment-failed"

	if redirect_to:
		redirect_url += "&" + urlencode({"redirect_to": redirect_to})
	if redirect_message:
		redirect_url += "&" + urlencode({"redirect_message": redirect_message})

	return get_url(redirect_url)


def _complete_payment_logic(token: str, status: str, request_data: dict) -> None:
	if not token:
		return

	# Use row-level lock to prevent race conditions between browser and notification
	# This will make the second request wait until the first one commits
	current_status = frappe.db.get_value("Integration Request", token, "status", for_update=True)

	if current_status in ["Completed", "Failed"]:
		# Already processed by another worker/request
		return

	reference_doctype = frappe.db.get_value("Integration Request", token, "reference_doctype")
	reference_docname = frappe.db.get_value("Integration Request", token, "reference_docname")

	if status == "Completed" and reference_doctype and reference_docname:
		try:
			frappe.flags.data = request_data
			if reference_doctype == "Payment Request":
				original_user = frappe.session.user
				try:
					frappe.set_user("Administrator")
					# Lock the payment request as well
					pr_status = frappe.db.get_value("Payment Request", reference_docname, "status", for_update=True)
					if pr_status != "Paid":
						pr = frappe.get_doc("Payment Request", reference_docname)
						pr.set_as_paid()
						if getattr(pr, "make_sales_invoice", None) and pr.reference_doctype == "Sales Order":
							sales_order = pr.reference_name
							has_invoice = frappe.db.exists(
								"Sales Invoice Item",
								{"sales_order": sales_order, "docstatus": 1},
							)
							if not has_invoice:
								from erpnext.selling.doctype.sales_order.sales_order import (
									make_sales_invoice,
								)

								si = make_sales_invoice(sales_order, ignore_permissions=True)
								si.allocate_advances_automatically = True
								si = si.insert(ignore_permissions=True)
								si.submit()
				except Exception:
					frappe.log_error(
						message=frappe.get_traceback(),
						title="Lloyds Connect: Payment Entry Creation Failed",
					)
				finally:
					frappe.set_user(original_user)

			elif reference_doctype == "Quotation":
				# Card-payment flow: Quotation was submitted at checkout time.
				# Now that gateway confirmed payment, create and submit the Sales Order.
				original_user = frappe.session.user
				try:
					frappe.set_user("Administrator")
					_create_so_and_payment_from_quotation(reference_docname, request_data)
				except Exception:
					frappe.log_error(
						message=frappe.get_traceback(),
						title="Lloyds Connect: Card Payment SO Creation Failed",
					)
				finally:
					frappe.set_user(original_user)

			else:
				frappe.get_doc(reference_doctype, reference_docname).run_method(
					"on_payment_authorized",
					"Completed",
				)
		except Exception:
			frappe.log_error(frappe.get_traceback())


	# Update status to indicate processing is finished
	frappe.db.set_value("Integration Request", token, "status", status)
	frappe.db.commit()



def _create_so_and_payment_from_quotation(quotation_name: str, payment_data: dict) -> None:
	"""
	Called from _complete_payment_logic when reference_doctype == "Quotation".
	Creates and submits a Sales Order from the submitted Quotation, creates a
	Payment Entry (and Sales Invoice), then clears cart cookies.
	"""
	from erpnext.selling.doctype.quotation.quotation import make_sales_order as _make_so
	from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry
	from erpnext.selling.doctype.sales_order.sales_order import make_sales_invoice
	from frappe.utils import nowdate, flt

	quot = frappe.get_doc("Quotation", quotation_name)
	if quot.docstatus != 1:
		frappe.throw(f"Quotation {quotation_name} is not submitted")

	# ── Create and submit Sales Order ───────────────────────────────────────
	so_doc = frappe.get_doc(_make_so(quotation_name))
	so_doc.payment_schedule = []
	so_doc.flags.ignore_permissions = True
	so_doc.custom_quotation_owner = quot.owner
	so_doc.custom_quotation_reference = quot.name
	so_doc.check_credit_limit = lambda: None  # card payment = money already collected, skip credit check
	so_doc.insert()
	so_doc.submit()

	# ── Create Payment Entry ─────────────────────────────────────────────────
	pe = get_payment_entry("Sales Order", so_doc.name)

	# Fetch mode of payment from Payment Gateway Account
	token = payment_data.get("merchantTransactionId")
	mode_of_payment = None
	payment_account = None
	try:
		# Get the default Payment Gateway Account to find the mode of payment
		gateway_account = frappe.db.get_value("Payment Gateway Account", {"is_default": 1}, ["mode_of_payment", "payment_account"], as_dict=True)
		if gateway_account:
			mode_of_payment = gateway_account.mode_of_payment
			payment_account = gateway_account.payment_account
	except Exception:
		pass

	pe.update({
		"reference_no": (
			payment_data.get("merchantTransactionId")
			or payment_data.get("oid")
			or payment_data.get("order_id")
			or quotation_name
		),
		"reference_date": nowdate(),
		"remarks": f"Card payment for {quotation_name} → {so_doc.name}",
		"mode_of_payment": mode_of_payment,
		"paid_to": payment_account,
	})
	pe.flags.ignore_permissions = True
	pe.insert(ignore_permissions=True)
	pe.submit()

	# ── Create Sales Invoice ─────────────────────────────────────────────────
	has_invoice = frappe.db.exists(
		"Sales Invoice Item", {"sales_order": so_doc.name, "docstatus": 1}
	)
	if not has_invoice:
		si = make_sales_invoice(so_doc.name, ignore_permissions=True)
		si.allocate_advances_automatically = True
		si = si.insert(ignore_permissions=True)
		si.submit()

	# ── Clear cart cookies ───────────────────────────────────────────────────
	if hasattr(frappe.local, "cookie_manager"):
		frappe.local.cookie_manager.delete_cookie("cart_count")
		frappe.local.cookie_manager.delete_cookie("cart_total")

	# Pass SO name to _finalize_payment for the redirect URL
	frappe.flags.card_payment_so_name = so_doc.name


def get_redirect_html(url: str) -> str:
	return f"""
		<!DOCTYPE html>
		<html>
			<head>
				<meta charset="utf-8">
				<title>Redirecting...</title>
				<script type="text/javascript">
					window.location.replace("{url}");
				</script>
			</head>
			<body>
				<div style="display: flex; justify-content: center; align-items: center; height: 100vh; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; flex-direction: column; text-align: center;">
					<p style="font-size: 1.2rem; color: #333; margin-bottom: 0.5rem;">Processing your payment...</p>
					<p style="font-size: 0.9rem; color: #666;">You are being redirected to the confirmation page.</p>
					<p style="font-size: 0.8rem; color: #888; margin-top: 1.5rem;">
						If you are not redirected automatically, <a href="{url}" style="color: #007bff; text-decoration: none;">click here</a>.
					</p>
				</div>
			</body>
		</html>
	"""


def _validate_response_hash(settings: LloydsConnectSettings, response: dict, expected_txndatetime: str):
	approval_code = response.get("approval_code")
	chargetotal = response.get("chargetotal")
	currency = response.get("currency")
	txndatetime = response.get("txndatetime")
	storename = response.get("storename") or settings.store_name

	if txndatetime != expected_txndatetime:
		raise frappe.PermissionError("Invalid txndatetime")

	provided = response.get("response_hash")
	message = f"{approval_code}|{chargetotal}|{currency}|{txndatetime}|{storename}"
	expected = _hmac_base64(
		settings.hash_algorithm,
		settings.get_password(fieldname="shared_secret", raise_exception=True),
		message,
	)

	if not provided or not hmac.compare_digest(provided, expected):
		raise frappe.PermissionError("Invalid response_hash")


def _validate_notification_hash(settings: LloydsConnectSettings, payload: dict, expected_txndatetime: str):
	chargetotal = payload.get("chargetotal")
	currency = payload.get("currency")
	txndatetime = payload.get("txndatetime")
	storename = payload.get("storename") or settings.store_name
	approval_code = payload.get("approval_code")

	if txndatetime != expected_txndatetime:
		raise frappe.PermissionError("Invalid txndatetime")

	provided = payload.get("notification_hash")
	message = f"{chargetotal}|{currency}|{txndatetime}|{storename}|{approval_code}"
	expected = _hmac_base64(
		settings.hash_algorithm,
		settings.get_password(fieldname="shared_secret", raise_exception=True),
		message,
	)

	if not provided or not hmac.compare_digest(provided, expected):
		raise frappe.PermissionError("Invalid notification_hash")


@frappe.whitelist(allow_guest=True, xss_safe=True)
def response_success():
	return _handle_response()


@frappe.whitelist(allow_guest=True, xss_safe=True)
def response_fail():
	return _handle_response()


def _handle_response():
	response = frappe._dict(frappe.local.form_dict)
	token = response.get("merchantTransactionId")
	if not token:
		frappe.log_error(
			message=f"Missing merchantTransactionId in response. Payload: {frappe.as_json(dict(response), indent=2)}",
			title="Lloyds Connect: Missing Token",
		)
		frappe.throw("Missing merchantTransactionId")

	try:
		settings = _get_settings_for_token(token)
		integration_request = frappe.get_doc("Integration Request", token)
		frappe.db.set_value(
			"Integration Request",
			token,
			"output",
			frappe.as_json(dict(response)),
			update_modified=False,
		)
		request_data = json.loads(integration_request.data)
		expected_txndatetime = request_data.get("txndatetime")

		_validate_response_hash(settings, response, expected_txndatetime)

		approval_code = response.get("approval_code") or ""
		status = "Completed" if approval_code.startswith("Y") else "Failed"
		redirect_url = _finalize_payment(token, status, dict(response))

		frappe.db.commit()

		# Return a raw Werkzeug Response to bypass Frappe's JSON wrapping and KeyError: 'html'
		# Also clear cookie manager to prevent 'Guest' session cookie from overwriting the user session
		if hasattr(frappe.local, "cookie_manager"):
			frappe.local.cookie_manager.cookies = {}
			frappe.local.cookie_manager.to_delete = []

		return Response(
			get_redirect_html(redirect_url),
			mimetype="text/html",
			status=200,
		)
	except Exception:
		frappe.log_error(
			message=(
				f"Token: {token}\n"
				f"Payload: {frappe.as_json(dict(response), indent=2)}\n\n"
				+ frappe.get_traceback()
			),
			title="Lloyds Connect: Response Handling Failed",
		)
		frappe.respond_as_web_page(
			"Payment Response Error",
			"We could not verify or process the payment response. Please contact support.",
			indicator_color="red",
			http_status_code=400,
		)


@frappe.whitelist(allow_guest=True, xss_safe=True)
def transaction_notification():
	payload = frappe._dict(frappe.local.form_dict)
	token = payload.get("merchantTransactionId")
	if not token:
		return ""

	try:
		settings = _get_settings_for_token(token)
		integration_request = frappe.get_doc("Integration Request", token)
		request_data = json.loads(integration_request.data)
		expected_txndatetime = request_data.get("txndatetime")

		_validate_notification_hash(settings, payload, expected_txndatetime)

		approval_code = payload.get("approval_code") or ""
		status = "Completed" if approval_code.startswith("Y") else "Failed"

		_complete_payment_logic(token, status, dict(payload))

		frappe.db.commit()
	except Exception:
		frappe.log_error(
			message=(
				f"Token: {token}\n"
				f"Payload: {frappe.as_json(dict(payload), indent=2)}\n\n"
				+ frappe.get_traceback()
			),
			title="Lloyds Connect: Notification Handling Failed",
		)

	return ""
