import frappe

no_cache = 1

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


def get_context(context):
	settings = frappe.get_cached_doc("Webshop Settings", "Webshop Settings")
	for field, default in COLOR_DEFAULTS.items():
		context[field] = settings.get(field) or default
