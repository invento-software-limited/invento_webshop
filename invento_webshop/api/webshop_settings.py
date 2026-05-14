import frappe

COLOR_DEFAULTS = {
	"primary_color": "#FFED00",
	"primary_color_hover": "#D5C600",
	"primary_color_light": "#FFF465",
	"primary_color_faint": "#FFFBC5",
	"primary_text_color": "#171307",
	"primary_text_hover": "#52504C",
	"light_bg_color": "#FFFDF5",
	"warm_bg_color": "#F8F6DF",
	"secondary_bg_color": "#F5F5F5",
	"btn_color": "#171307",
	"btn_bg_color": "#FFED00",
	"btn_hover_color": "#FFFFFF",
	"btn_hover_bg_color": "#D5C600",
}


@frappe.whitelist()
def reset_colors():
	settings = frappe.get_doc("Webshop Settings", "Webshop Settings")
	for field, default in COLOR_DEFAULTS.items():
		settings.set(field, default)
	settings.save()
	frappe.db.commit()


@frappe.whitelist()
def clear_all_cache():
	frappe.clear_cache()
	from frappe.website.utils import clear_cache
	clear_cache()


@frappe.whitelist()
def reset_to_applied_theme():
	"""Re-apply the currently active Webshop Theme, restoring all fields,
	images and builder assets to the theme's correct values."""
	applied = frappe.get_all(
		"Webshop Theme",
		filters={"status": "Applied"},
		pluck="name",
		limit=1,
	)
	if not applied:
		frappe.throw("No theme is currently applied. Please apply a theme from the Webshop Theme list first.")

	from invento_webshop.invento_webshop.doctype.webshop_theme.webshop_theme import apply_theme
	return apply_theme(applied[0])
