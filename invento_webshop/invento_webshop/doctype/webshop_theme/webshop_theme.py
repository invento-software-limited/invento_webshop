# Copyright (c) 2026, Invento Software Limited and contributors
# For license information, please see license.txt

import colorsys
import math
import os
import re
import shutil

import frappe
from frappe.model.document import Document

THEME_FIELDS = [
	"logo", "footer_logo", "why_us_bg",
	"theme_primary", "theme_text", "theme_bg",
	"btn_color", "btn_bg_color", "btn_hover_color", "btn_hover_bg_color",
	"primary_color", "primary_color_hover", "primary_color_light", "primary_color_faint",
	"primary_text_color", "primary_text_hover",
	"light_bg_color", "warm_bg_color", "secondary_bg_color",
	"carousel_image_1", "carousel_image_2", "carousel_image_3",
]

# Stable SVG filenames written to builder_assets on every apply
STABLE = {
	"logo":         "ws_logo.svg",
	"footer_logo":  "ws_footer_logo.svg",
	"why_us_bg":    "ws_section_bg.svg",
	"carousel_1":   "ws_carousel_1.svg",
	"carousel_2":   "ws_carousel_2.svg",
	"carousel_3":   "ws_carousel_3.svg",
	"footer_bg":    "ws_footer_bg.svg",       # referenced in footer.json
	"svg_icon":     "ws_diff_icon.svg",       # What Makes Us Different inline icon
}

FONT = "system-ui,-apple-system,'Segoe UI',sans-serif"


class WebshopTheme(Document):
	def validate(self):
		self._derive_theme_colors()

	def _derive_theme_colors(self):
		primary = self.get("theme_primary")
		text    = self.get("theme_text")
		bg      = self.get("theme_bg")
		if not (primary or text or bg):
			return
		if primary:
			h, l, s = _hls(primary)
			self.primary_color       = primary
			self.primary_color_hover = _hex(h, l - 0.10, s)
			self.primary_color_light = _hex(h, l + 0.15, s)
			self.primary_color_faint = _hex(h, 0.92,     s * 0.25)
		if text:
			h, l, s = _hls(text)
			self.primary_text_color  = _hex(h, max(0.08, l - 0.15), s)
			self.primary_text_hover  = text
		if bg:
			h, l, s = _hls(bg)
			self.light_bg_color      = _hex(h, min(0.97, l + 0.05), s)
			self.warm_bg_color       = bg
			self.secondary_bg_color  = _hex(h, l, s * 0.15)


@frappe.whitelist()
def apply_theme(name):
	theme = frappe.get_doc("Webshop Theme", name)

	for n in frappe.get_all("Webshop Theme", filters={"status": "Applied"}, pluck="name"):
		if n != name:
			frappe.db.set_value("Webshop Theme", n, "status", "Not Applied")

	settings = frappe.get_doc("Webshop Settings", "Webshop Settings")
	for field in THEME_FIELDS:
		settings.set(field, theme.get(field))

	settings.custom_images = []
	for row in theme.get("custom_images") or []:
		settings.append("custom_images", {
			"image": row.get("image"), "image_key": row.get("image_key"),
			"description": row.get("description"),
		})
	settings.save(ignore_permissions=True)

	# Write all SVG stable files to builder_assets
	_write_all_svgs(theme)

	frappe.db.set_value("Webshop Theme", name, "status", "Applied")
	frappe.clear_cache()
	from frappe.website.utils import clear_cache as _wc
	_wc()
	return {"message": "Theme applied successfully"}


# ── SVG generation orchestrator ───────────────────────────────────────────────

def _write_all_svgs(theme):
	p  = theme.primary_color       or "#111827"
	d  = theme.primary_color_hover  or "#030712"
	l  = theme.primary_color_light  or "#374151"
	f  = theme.primary_color_faint  or "#F9FAFB"
	tc = theme.primary_text_color   or "#0F172A"

	ba = os.path.join(frappe.get_app_path("invento_webshop"), "public", "builder_assets")
	os.makedirs(ba, exist_ok=True)

	site_public = os.path.join(frappe.get_site_path(), "public")

	def _write(filename, content):
		with open(os.path.join(ba, filename), "w", encoding="utf-8") as fh:
			fh.write(content)

	# 1. Navbar / mobile logo — copy directly from theme's own SVG file
	#    so the design is exactly ws_theme_*_logo.svg, just with theme colors.
	logo_url = theme.get("logo")
	logo_copied = False
	if logo_url and logo_url.startswith("/files/"):
		src = os.path.join(site_public, "files", logo_url[len("/files/"):])
		if os.path.exists(src):
			shutil.copy2(src, os.path.join(ba, STABLE["logo"]))
			logo_copied = True
	if not logo_copied:
		_write(STABLE["logo"], _svg_logo(p, d, tc))

	# 2. Footer logo — copy theme's logo file then rewrite text to white for dark bg
	footer_logo_url = theme.get("footer_logo") or logo_url
	footer_copied = False
	if footer_logo_url and footer_logo_url.startswith("/files/"):
		src = os.path.join(site_public, "files", footer_logo_url[len("/files/"):])
		if os.path.exists(src):
			shutil.copy2(src, os.path.join(ba, STABLE["footer_logo"]))
			footer_copied = True
	if not footer_copied:
		_write(STABLE["footer_logo"], _svg_footer_logo(p, d))

	# 3. "Why Us" section background — light geometric SVG
	_write(STABLE["why_us_bg"], _svg_section_bg(p, l, f))

	# 4. Carousels — copy from /files/ if available, else use generated SVG
	for i, key in enumerate(["carousel_1", "carousel_2", "carousel_3"], 1):
		field = f"carousel_image_{i}"
		src_url = theme.get(field)
		copied = False
		if src_url and src_url.startswith("/files/"):
			src = os.path.join(site_public, "files", src_url[len("/files/"):])
			if os.path.exists(src):
				shutil.copy2(src, os.path.join(ba, STABLE[key]))
				copied = True
		if not copied:
			fns = [_svg_carousel_1, _svg_carousel_2, _svg_carousel_3]
			_write(STABLE[key], fns[i - 1](p, d, l, f))

	# 5. Footer background — dark SVG that contrasts with white footer text
	_write(STABLE["footer_bg"], _svg_footer_bg(p, d, l))

	# 6. "What Makes Us Different" inline SVG icon color
	_patch_svg_icon(p)

	# 7. Point navbar/mobile-nav directly to this theme's own logo file
	#    (different URL per theme → browser never serves a stale cached version)
	_update_navbar_logo(theme.get("logo") or f"/assets/invento_webshop/builder_assets/{STABLE['logo']}")


# ── SVG builders ──────────────────────────────────────────────────────────────

def _svg_logo(p, d, tc):
	"""Navbar logo: water-drop icon + INVENTO / WEBSHOP, theme text colors."""
	return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 64">
  <defs>
    <linearGradient id="g" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="{p}"/>
      <stop offset="100%" stop-color="{d}"/>
    </linearGradient>
  </defs>
  <path d="M23 8 Q36 22 36 34 A13 13 0 0 1 10 34 Q10 22 23 8 Z" fill="url(#g)"/>
  <ellipse cx="19" cy="32" rx="4" ry="6" fill="rgba(255,255,255,0.22)" transform="rotate(-20,19,32)"/>
  <text x="48" y="38" font-family="{FONT}" font-size="21" font-weight="800" fill="{tc}" letter-spacing="0.5">INVENTO</text>
  <text x="49" y="53" font-family="{FONT}" font-size="9" font-weight="600" fill="{p}" letter-spacing="4">WEBSHOP</text>
</svg>"""


def _svg_footer_logo(p, d):
	"""Footer logo: text-only (no icon), white INVENTO + primary WEBSHOP, tight margins."""
	return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 126 56">
  <text x="4" y="34" font-family="{FONT}" font-size="26" font-weight="800" fill="#FFFFFF" letter-spacing="0.5">INVENTO</text>
  <text x="5" y="50" font-family="{FONT}" font-size="9"  font-weight="600" fill="{p}"       letter-spacing="4">WEBSHOP</text>
  <rect x="5" y="53" width="116" height="2" fill="{p}" opacity="0.7"/>
</svg>"""


def _svg_footer_bg(p, d, l):
	"""Dark footer background SVG — deep gradient, accent line, large INVENTO watermark."""
	dark1 = _darken_hex(d, 0.55)
	dark2 = _darken_hex(p, 0.40)
	return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1920 979" preserveAspectRatio="xMidYMid slice">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{dark1}"/>
      <stop offset="100%" stop-color="{dark2}"/>
    </linearGradient>
  </defs>
  <rect width="1920" height="979" fill="url(#bg)"/>
  <!-- Accent line top -->
  <rect x="0" y="0" width="1920" height="4" fill="{p}"/>
  <!-- Decorative circles -->
  <circle cx="200"  cy="979" r="600" fill="{p}" opacity="0.06"/>
  <circle cx="1920" cy="0"   r="500" fill="{p}" opacity="0.06"/>
  <circle cx="960"  cy="490" r="800" fill="{l}" opacity="0.04"/>
  <!-- Small accent dots -->
  <circle cx="400"  cy="100" r="30" fill="{l}" opacity="0.12"/>
  <circle cx="800"  cy="200" r="18" fill="{l}" opacity="0.10"/>
  <circle cx="1200" cy="80"  r="24" fill="{l}" opacity="0.10"/>
  <circle cx="1600" cy="160" r="20" fill="{l}" opacity="0.10"/>
  <circle cx="1800" cy="300" r="14" fill="{l}" opacity="0.10"/>
  <!-- Large INVENTO watermark text (replaces old Buzz branding) -->
  <text x="960" y="620"
        font-family="{FONT}"
        font-size="240"
        font-weight="900"
        fill="rgba(255,255,255,0.04)"
        text-anchor="middle"
        letter-spacing="-4">INVENTO</text>
</svg>"""


def _svg_section_bg(p, l, f):
	"""Light geometric background for the 'What Makes Us Different' section."""
	return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1800 896" preserveAspectRatio="xMidYMid slice">
  <rect width="1800" height="896" fill="{f}"/>
  <!-- Corner accents -->
  <circle cx="-80"  cy="-80"  r="340" fill="{l}" opacity="0.25"/>
  <circle cx="1880" cy="976"  r="340" fill="{l}" opacity="0.25"/>
  <circle cx="1880" cy="-80"  r="240" fill="{p}" opacity="0.08"/>
  <circle cx="-80"  cy="976"  r="240" fill="{p}" opacity="0.08"/>
  <!-- Centre subtle radial -->
  <circle cx="900" cy="448" r="500"  fill="{p}" opacity="0.04"/>
  <!-- Top accent line -->
  <rect x="0" y="0" width="1800" height="3" fill="{p}" opacity="0.25"/>
</svg>"""


def _svg_carousel_1(p, d, l, f):
	return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 810 656" font-family="{FONT}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{f}"/>
      <stop offset="100%" stop-color="#FFFFFF"/>
    </linearGradient>
  </defs>
  <rect width="810" height="656" fill="url(#bg)"/>
  <polygon points="490,0 810,0 810,656 380,656" fill="{p}"/>
  <circle cx="680" cy="180" r="180" fill="{d}" opacity="0.25"/>
  <circle cx="560" cy="520" r="130" fill="{l}" opacity="0.22"/>
  <circle cx="680" cy="310" r="140" fill="rgba(255,255,255,0.10)"/>
  <circle cx="680" cy="310" r="96"  fill="rgba(255,255,255,0.07)"/>
  <rect x="60" y="140" width="8" height="360" fill="{p}" opacity="0.28"/>
  <rect x="0" y="650" width="470" height="6" fill="{p}"/>
  <text x="60" y="220" font-size="11" font-weight="700" fill="#475569" letter-spacing="5">WELCOME TO OUR STORE</text>
  <text x="60" y="316" font-size="58" font-weight="900" fill="#0F172A" letter-spacing="-1">Shop the</text>
  <text x="60" y="384" font-size="58" font-weight="900" fill="{p}">Latest.</text>
  <text x="60" y="430" font-size="16" fill="#475569" opacity="0.9">Handpicked products crafted for you.</text>
  <rect  x="60" y="460" width="172" height="48" rx="24" fill="{p}"/>
  <text x="146" y="490" font-size="14" font-weight="700" fill="#FFFFFF" text-anchor="middle">Shop Now &#x2192;</text>
</svg>"""


def _svg_carousel_2(p, d, l, f):
	return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 810 656" font-family="{FONT}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%"   stop-color="{f}"/>
      <stop offset="55%"  stop-color="#FFFFFF"/>
      <stop offset="100%" stop-color="{f}"/>
    </linearGradient>
    <radialGradient id="rg" cx="68%" cy="50%" r="48%">
      <stop offset="0%"   stop-color="{l}"/>
      <stop offset="100%" stop-color="{d}"/>
    </radialGradient>
  </defs>
  <rect width="810" height="656" fill="url(#bg)"/>
  <circle cx="570" cy="328" r="230" fill="url(#rg)" opacity="0.90"/>
  <circle cx="570" cy="328" r="182" fill="rgba(255,255,255,0.09)"/>
  <circle cx="370" cy="80"  r="68"  fill="{p}" opacity="0.12"/>
  <circle cx="730" cy="60"  r="50"  fill="{l}" opacity="0.22"/>
  <circle cx="760" cy="560" r="80"  fill="{d}" opacity="0.13"/>
  <rect x="60" y="148" width="104" height="32" rx="16" fill="{p}"/>
  <text x="112" y="170" font-size="11" font-weight="800" fill="#FFFFFF" text-anchor="middle" letter-spacing="3">NEW</text>
  <text x="60"  y="280" font-size="62" font-weight="900" fill="#0F172A" letter-spacing="-1">Fresh</text>
  <text x="60"  y="352" font-size="62" font-weight="900" fill="{p}"     letter-spacing="-1">Arrivals</text>
  <text x="60"  y="396" font-size="16" fill="#475569" opacity="0.88">The season&apos;s best, just landed.</text>
  <rect  x="60" y="424" width="208" height="48" rx="24" fill="{p}"/>
  <text x="164" y="454" font-size="14" font-weight="700" fill="#FFFFFF" text-anchor="middle">Explore &#x2192;</text>
</svg>"""


def _svg_carousel_3(p, d, f):
	return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 810 656" font-family="{FONT}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%"   stop-color="{d}"/>
      <stop offset="100%" stop-color="{p}"/>
    </linearGradient>
    <linearGradient id="badge" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%"   stop-color="#FFFFFF" stop-opacity="0.98"/>
      <stop offset="100%" stop-color="{f}"/>
    </linearGradient>
  </defs>
  <rect width="810" height="656" fill="url(#bg)"/>
  <ellipse cx="100" cy="656" rx="400" ry="200" fill="rgba(255,255,255,0.05)"/>
  <ellipse cx="750" cy="0"   rx="340" ry="180" fill="rgba(255,255,255,0.05)"/>
  <circle cx="610" cy="310" r="200" fill="url(#badge)" opacity="0.97"/>
  <circle cx="610" cy="310" r="162" fill="{f}" opacity="0.30"/>
  <circle cx="610" cy="310" r="72"  fill="{p}"/>
  <text x="610" y="270" font-size="22" font-weight="800" fill="{d}" text-anchor="middle" letter-spacing="1">UP TO</text>
  <text x="610" y="340" font-size="72" font-weight="900" fill="{p}" text-anchor="middle" letter-spacing="-2">50%</text>
  <text x="610" y="372" font-size="22" font-weight="800" fill="{d}" text-anchor="middle" letter-spacing="2">OFF</text>
  <text x="60" y="200" font-size="11" font-weight="700" fill="rgba(255,255,255,0.70)" letter-spacing="5">LIMITED TIME OFFER</text>
  <text x="60" y="290" font-size="58" font-weight="900" fill="#FFFFFF" letter-spacing="-1">Exclusive</text>
  <text x="60" y="358" font-size="58" font-weight="900" fill="#FFFFFF" letter-spacing="-1">Deals.</text>
  <text x="60" y="400" font-size="15" fill="rgba(255,255,255,0.82)">Unbeatable prices on premium products.</text>
  <rect  x="60" y="426" width="196" height="48" rx="24" fill="#FFFFFF"/>
  <text x="158" y="456" font-size="14" font-weight="700" fill="{p}" text-anchor="middle">Grab Deal &#x2192;</text>
</svg>"""


# ── Logo cache buster ────────────────────────────────────────────────────────

def _update_navbar_logo(logo_url):
	"""Set the navbar & mobile-nav logo src to logo_url.
	Using the theme's own /files/ URL means every theme has a unique URL —
	the browser never serves a stale cached version from a previous theme."""

	# Match the full "src":"<logo-url>" pair — simpler than lookbehind
	pattern = re.compile(
		r'"src"\s*:\s*"('
		r'/assets/invento_webshop/builder_assets/ws_logo\.svg[^"]*'
		r'|/files/ws_theme_[^"]+_logo\.svg[^"]*'
		r')"'
	)
	replacement = f'"src":"{logo_url}"'

	# 1. Update JSON files on disk
	comp_dir = os.path.join(
		frappe.get_app_path("invento_webshop"),
		"builder_files", "components"
	)
	for comp_name in ("navbar", "mobile_nav"):
		json_path = os.path.join(comp_dir, comp_name, f"{comp_name}.json")
		if os.path.exists(json_path):
			content = open(json_path, encoding="utf-8").read()
			updated = pattern.sub(replacement, content)
			if updated != content:
				with open(json_path, "w", encoding="utf-8") as fh:
					fh.write(updated)

	# 2. Update DB — read in Python, sub in Python, write back with parameterized query
	rows = frappe.db.sql(
		"SELECT `name`, `block` FROM `tabBuilder Component` "
		"WHERE `component_name` IN ('Navbar', 'Mobile Nav')",
		as_dict=True,
	)
	for row in rows:
		if not row.block:
			continue
		new_block = pattern.sub(replacement, row.block)
		if new_block != row.block:
			frappe.db.sql(
				"UPDATE `tabBuilder Component` SET `block` = %s, `modified` = NOW() WHERE `name` = %s",
				(new_block, row.name),
			)
	frappe.db.commit()


# ── SVG icon color patcher ────────────────────────────────────────────────────

def _patch_svg_icon(primary_color):
	"""Replace hardcoded #484848 with theme primary color in the Why Us page."""
	OLD = "#484848"
	NEW = primary_color

	# Update JSON file on disk
	json_path = os.path.join(
		frappe.get_app_path("invento_webshop"),
		"builder_files", "pages", "page_5330135a", "page_5330135a.json"
	)
	if os.path.exists(json_path):
		content = open(json_path, encoding="utf-8").read()
		if OLD in content:
			with open(json_path, "w", encoding="utf-8") as fh:
				fh.write(content.replace(OLD, NEW))

	# Update Builder Page record in DB
	try:
		pages = frappe.get_all("Builder Page", filters={"page_name": "page_5330135a"}, pluck="name")
		if pages:
			doc = frappe.get_doc("Builder Page", pages[0])
			changed = False
			for attr in ("draft_blocks", "blocks"):
				val = getattr(doc, attr, None)
				if val and OLD in val:
					setattr(doc, attr, val.replace(OLD, NEW))
					changed = True
			if changed:
				doc.save(ignore_permissions=True)
	except Exception:
		pass


# ── Color helpers ─────────────────────────────────────────────────────────────

def _darken_hex(hex_color, amount):
	h = hex_color.lstrip("#")
	r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
	r = max(0, int(r * (1 - amount)))
	g = max(0, int(g * (1 - amount)))
	b = max(0, int(b * (1 - amount)))
	return f"#{r:02X}{g:02X}{b:02X}"


def _hls(hex_color):
	h = hex_color.lstrip("#")
	r, g, b = int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255
	return colorsys.rgb_to_hls(r, g, b)


def _hex(h, l, s):
	l = max(0.0, min(1.0, l))
	s = max(0.0, min(1.0, s))
	r, g, b = colorsys.hls_to_rgb(h, l, s)
	return "#{:02X}{:02X}{:02X}".format(int(r * 255), int(g * 255), int(b * 255))
