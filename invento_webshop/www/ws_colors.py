import colorsys
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

def _anim_color(btn_bg):
	"""
	Pick the complementary hue of the button background at full vibrancy.
	Opposite hue on the colour wheel → always maximally distinct and attractive
	regardless of the applied theme.
	"""
	try:
		h = btn_bg.lstrip("#")
		r, g, b = int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255
		hue, lightness, _ = colorsys.rgb_to_hls(r, g, b)

		# Opposite hue, forced to high saturation + mid-vibrant lightness
		comp_hue = (hue + 0.5) % 1.0
		comp_sat = 0.90
		# Keep lightness in a visible mid-range regardless of source
		comp_light = 0.55 if lightness < 0.5 else 0.45

		r2, g2, b2 = colorsys.hls_to_rgb(comp_hue, comp_light, comp_sat)
		return "#{:02X}{:02X}{:02X}".format(int(r2 * 255), int(g2 * 255), int(b2 * 255))
	except Exception:
		return "#00C2FF"


def _faint_deep(primary_color):
	"""20% deeper than primary_color_faint: same hue, lightness 0.84, saturation 45%."""
	try:
		h = primary_color.lstrip("#")
		r, g, b = int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255
		hue, _, sat = colorsys.rgb_to_hls(r, g, b)
		r2, g2, b2 = colorsys.hls_to_rgb(hue, 0.84, min(sat * 0.45, 1.0))
		return "#{:02X}{:02X}{:02X}".format(int(r2 * 255), int(g2 * 255), int(b2 * 255))
	except Exception:
		return "#E8E8E8"


def get_context(context):
	settings = frappe.get_cached_doc("Webshop Settings", "Webshop Settings")
	for field, default in COLOR_DEFAULTS.items():
		context[field] = settings.get(field) or default
	primary = settings.get("primary_color") or COLOR_DEFAULTS["primary_color"]
	context["primary_color_faint_deep"] = _faint_deep(primary)
	context["btn_anim_color"] = _anim_color(
		settings.get("btn_bg_color") or COLOR_DEFAULTS["btn_bg_color"]
	)
