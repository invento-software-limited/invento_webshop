import frappe

no_cache = 1


def get_context(context):
	context.no_cache = 1
	context.doctype = frappe.form_dict.get("doctype")
	context.docname = frappe.form_dict.get("docname")
	context.redirect_to = frappe.form_dict.get("redirect_to")
	context.redirect_message = frappe.form_dict.get("redirect_message")
