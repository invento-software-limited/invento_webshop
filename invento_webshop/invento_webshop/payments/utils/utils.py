import frappe
from frappe import _


def validate_integration_request(docname: str | None):
	if not docname:
		frappe.throw(_("Missing Token"))
	if not frappe.db.exists("Integration Request", docname):
		frappe.throw(_("Token not found: {0}").format(docname))
	status = frappe.db.get_value("Integration Request", docname, "status")
	if status == "Cancelled":
		frappe.throw(_("Expired Token"))


def get_payment_gateway_controller(payment_gateway: str):
	gateway = frappe.get_doc("Payment Gateway", payment_gateway)
	if not gateway.gateway_controller:
		try:
			return frappe.get_doc(f"{payment_gateway} Settings")
		except Exception:
			frappe.throw(_("{0} Settings not found").format(payment_gateway))
	else:
		try:
			return frappe.get_doc(gateway.gateway_settings, gateway.gateway_controller)
		except Exception:
			frappe.throw(_("{0} Settings not found").format(payment_gateway))


@frappe.whitelist(allow_guest=True, xss_safe=True)
def get_checkout_url(**kwargs):
	try:
		if kwargs.get("payment_gateway"):
			doc = frappe.get_doc("{} Settings".format(kwargs.get("payment_gateway")))
			return doc.get_payment_url(**kwargs)
		raise Exception
	except Exception:
		frappe.respond_as_web_page(
			_("Something went wrong"),
			_(
				"Looks like something is wrong with this site's payment gateway configuration. No payment has been made."
			),
			indicator_color="red",
			http_status_code=frappe.ValidationError.http_status_code,
		)


def create_payment_gateway(gateway: str, settings: str | None = None, controller: str | None = None):
	if not frappe.db.exists("Payment Gateway", gateway):
		payment_gateway = frappe.get_doc(
			{
				"doctype": "Payment Gateway",
				"gateway": gateway,
				"gateway_settings": settings,
				"gateway_controller": controller,
			}
		)
		payment_gateway.insert(ignore_permissions=True)
