import frappe


@frappe.whitelist(allow_guest=True)
def get_webshop_assets():
	settings = frappe.get_cached_doc("Webshop Settings", "Webshop Settings")
	assets = {
		"logo": settings.logo or "",
		"favicon": settings.favicon or "",
		"hero_banner": settings.hero_banner or "",
		"hero_banner_mobile": settings.hero_banner_mobile or "",
	}
	for row in settings.get("custom_images") or []:
		if row.image_key and row.image_file:
			assets[row.image_key] = row.image_file
	return assets
