# Copyright (c) 2026, Invento Software Limited and contributors
# Writes built-in Webshop Theme SVG assets to site/public/files/ and
# sets the image fields on every default theme record.

import os
import frappe

FONT = "system-ui,-apple-system,'Segoe UI',sans-serif"

THEMES = [
	dict(slug="black",   name="Midnight Black",  p="#111827", d="#030712", l="#374151", f="#F9FAFB"),
	dict(slug="slate",   name="Charcoal Slate",  p="#334155", d="#1E293B", l="#475569", f="#F8FAFC"),
	dict(slug="blue",    name="Royal Blue",       p="#2563EB", d="#1D4ED8", l="#3B82F6", f="#EFF6FF"),
	dict(slug="sky",     name="Sky Blue",         p="#0284C7", d="#0369A1", l="#0EA5E9", f="#F0F9FF"),
	dict(slug="teal",    name="Ocean Teal",       p="#0D9488", d="#0F766E", l="#14B8A6", f="#F0FDFA"),
	dict(slug="emerald", name="Emerald",          p="#059669", d="#047857", l="#10B981", f="#ECFDF5"),
	dict(slug="green",   name="Forest Green",     p="#15803D", d="#166534", l="#16A34A", f="#F0FDF4"),
	dict(slug="red",     name="Crimson Red",      p="#DC2626", d="#B91C1C", l="#EF4444", f="#FEF2F2"),
	dict(slug="orange",  name="Sunset Orange",    p="#EA580C", d="#C2410C", l="#F97316", f="#FFF7ED"),
	dict(slug="amber",   name="Amber Honey",      p="#D97706", d="#B45309", l="#F59E0B", f="#FFFBEB"),
	dict(slug="pink",    name="Fuchsia Pink",     p="#DB2777", d="#BE185D", l="#EC4899", f="#FDF2F8"),
	dict(slug="violet",  name="Deep Violet",      p="#7C3AED", d="#6D28D9", l="#8B5CF6", f="#F5F3FF"),
]

# ── Logo SVGs (unique icon per theme) ─────────────────────────────────────────

def _logo_black(p, d):
	return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 64">
  <defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="{p}"/><stop offset="100%" stop-color="{d}"/></linearGradient></defs>
  <polygon points="23,8 40,31 23,54 6,31" fill="url(#g)"/>
  <polygon points="23,18 34,31 23,44 12,31" fill="rgba(255,255,255,0.18)"/>
  <text x="48" y="38" font-family="{FONT}" font-size="21" font-weight="800" fill="#111827" letter-spacing="0.5">INVENTO</text>
  <text x="49" y="53" font-family="{FONT}" font-size="9" font-weight="600" fill="#6B7280" letter-spacing="4">WEBSHOP</text>
</svg>"""

def _logo_slate(p, d):
	return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 64">
  <defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="{p}"/><stop offset="100%" stop-color="{d}"/></linearGradient></defs>
  <polygon points="23,9 38,18 38,45 23,54 8,45 8,18" fill="url(#g)"/>
  <polygon points="23,17 32,22 32,42 23,47 14,42 14,22" fill="rgba(255,255,255,0.15)"/>
  <text x="48" y="38" font-family="{FONT}" font-size="21" font-weight="800" fill="#1E293B" letter-spacing="0.5">INVENTO</text>
  <text x="49" y="53" font-family="{FONT}" font-size="9" font-weight="600" fill="#64748B" letter-spacing="4">WEBSHOP</text>
</svg>"""

def _logo_blue(p, d):
	return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 64">
  <defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="{p}"/><stop offset="100%" stop-color="{d}"/></linearGradient></defs>
  <path d="M23 8 L39 14 L39 30 Q39 46 23 56 Q7 46 7 30 L7 14 Z" fill="url(#g)"/>
  <path d="M23 18 L32 22 L32 32 Q32 40 23 46 Q14 40 14 32 L14 22 Z" fill="rgba(255,255,255,0.16)"/>
  <text x="48" y="38" font-family="{FONT}" font-size="21" font-weight="800" fill="#1E3A5F" letter-spacing="0.5">INVENTO</text>
  <text x="49" y="53" font-family="{FONT}" font-size="9" font-weight="600" fill="#3B82F6" letter-spacing="4">WEBSHOP</text>
</svg>"""

def _logo_sky(p, d):
	return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 64">
  <defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="{p}"/><stop offset="100%" stop-color="{d}"/></linearGradient></defs>
  <path d="M8 10 L40 31 L8 52 L14 33 L8 31 L14 29 Z" fill="url(#g)"/>
  <path d="M14 29 L14 33 L22 31 Z" fill="rgba(255,255,255,0.25)"/>
  <text x="48" y="38" font-family="{FONT}" font-size="21" font-weight="800" fill="#0C1A33" letter-spacing="0.5">INVENTO</text>
  <text x="49" y="53" font-family="{FONT}" font-size="9" font-weight="600" fill="#0284C7" letter-spacing="4">WEBSHOP</text>
</svg>"""

def _logo_teal(p, d):
	return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 64">
  <defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="{p}"/><stop offset="100%" stop-color="{d}"/></linearGradient></defs>
  <path d="M23 8 Q36 22 36 34 A13 13 0 0 1 10 34 Q10 22 23 8 Z" fill="url(#g)"/>
  <ellipse cx="19" cy="32" rx="4" ry="6" fill="rgba(255,255,255,0.22)" transform="rotate(-20,19,32)"/>
  <text x="48" y="38" font-family="{FONT}" font-size="21" font-weight="800" fill="#0D2825" letter-spacing="0.5">INVENTO</text>
  <text x="49" y="53" font-family="{FONT}" font-size="9" font-weight="600" fill="#0D9488" letter-spacing="4">WEBSHOP</text>
</svg>"""

def _logo_emerald(p, d):
	return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 64">
  <defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="{p}"/><stop offset="100%" stop-color="{d}"/></linearGradient></defs>
  <path d="M23 52 Q6 38 8 14 Q30 8 40 26 Q36 52 23 52 Z" fill="url(#g)"/>
  <path d="M23 52 L17 26" stroke="rgba(255,255,255,0.4)" stroke-width="1.8" fill="none" stroke-linecap="round"/>
  <path d="M17 26 L26 20" stroke="rgba(255,255,255,0.25)" stroke-width="1.2" fill="none" stroke-linecap="round"/>
  <path d="M17 26 L10 30" stroke="rgba(255,255,255,0.25)" stroke-width="1.2" fill="none" stroke-linecap="round"/>
  <text x="48" y="38" font-family="{FONT}" font-size="21" font-weight="800" fill="#064E3B" letter-spacing="0.5">INVENTO</text>
  <text x="49" y="53" font-family="{FONT}" font-size="9" font-weight="600" fill="#059669" letter-spacing="4">WEBSHOP</text>
</svg>"""

def _logo_green(p, d):
	return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 64">
  <defs><linearGradient id="g" x1="0" y1="1" x2="0" y2="0"><stop offset="0%" stop-color="{d}"/><stop offset="100%" stop-color="{p}"/></linearGradient></defs>
  <polygon points="23,8 38,34 8,34" fill="url(#g)"/>
  <polygon points="23,18 35,38 11,38" fill="{p}" opacity="0.85"/>
  <rect x="19" y="38" width="8" height="14" rx="2" fill="{d}"/>
  <text x="48" y="38" font-family="{FONT}" font-size="21" font-weight="800" fill="#052E16" letter-spacing="0.5">INVENTO</text>
  <text x="49" y="53" font-family="{FONT}" font-size="9" font-weight="600" fill="#15803D" letter-spacing="4">WEBSHOP</text>
</svg>"""

def _logo_red(p, d):
	return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 64">
  <defs><linearGradient id="g" x1="0" y1="1" x2="0" y2="0"><stop offset="0%" stop-color="{d}"/><stop offset="100%" stop-color="#FCA5A5"/></linearGradient></defs>
  <path d="M23 56 Q9 46 9 32 Q9 20 17 14 Q15 22 19 24 Q18 16 23 8 Q29 16 27 24 Q31 20 29 12 Q37 20 37 32 Q37 46 23 56 Z" fill="url(#g)"/>
  <path d="M23 50 Q16 42 16 34 Q18 26 23 24 Q28 26 28 34 Q28 42 23 50 Z" fill="rgba(255,255,255,0.18)"/>
  <text x="48" y="38" font-family="{FONT}" font-size="21" font-weight="800" fill="#450A0A" letter-spacing="0.5">INVENTO</text>
  <text x="49" y="53" font-family="{FONT}" font-size="9" font-weight="600" fill="#DC2626" letter-spacing="4">WEBSHOP</text>
</svg>"""

def _logo_orange(p, d):
	return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 64">
  <defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="{p}"/><stop offset="100%" stop-color="{d}"/></linearGradient></defs>
  <g transform="translate(23,31)">
    <line x1="0" y1="-21" x2="0" y2="-14" stroke="{p}" stroke-width="3" stroke-linecap="round"/>
    <line x1="0" y1="14" x2="0" y2="21" stroke="{p}" stroke-width="3" stroke-linecap="round"/>
    <line x1="-21" y1="0" x2="-14" y2="0" stroke="{p}" stroke-width="3" stroke-linecap="round"/>
    <line x1="14" y1="0" x2="21" y2="0" stroke="{p}" stroke-width="3" stroke-linecap="round"/>
    <line x1="-15" y1="-15" x2="-10" y2="-10" stroke="{p}" stroke-width="3" stroke-linecap="round"/>
    <line x1="10" y1="-10" x2="15" y2="-15" stroke="{p}" stroke-width="3" stroke-linecap="round"/>
    <line x1="-10" y1="10" x2="-15" y2="15" stroke="{p}" stroke-width="3" stroke-linecap="round"/>
    <line x1="10" y1="10" x2="15" y2="15" stroke="{p}" stroke-width="3" stroke-linecap="round"/>
    <circle r="11" fill="url(#g)"/>
  </g>
  <text x="48" y="38" font-family="{FONT}" font-size="21" font-weight="800" fill="#431407" letter-spacing="0.5">INVENTO</text>
  <text x="49" y="53" font-family="{FONT}" font-size="9" font-weight="600" fill="#EA580C" letter-spacing="4">WEBSHOP</text>
</svg>"""

def _logo_amber(p, d):
	return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 64">
  <defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="{p}"/><stop offset="100%" stop-color="{d}"/></linearGradient></defs>
  <polygon points="23,9 38,18 38,45 23,54 8,45 8,18" fill="url(#g)"/>
  <circle cx="23" cy="31" r="8" fill="rgba(255,255,255,0.22)"/>
  <circle cx="23" cy="31" r="3.5" fill="{d}"/>
  <text x="48" y="38" font-family="{FONT}" font-size="21" font-weight="800" fill="#451A03" letter-spacing="0.5">INVENTO</text>
  <text x="49" y="53" font-family="{FONT}" font-size="9" font-weight="600" fill="#D97706" letter-spacing="4">WEBSHOP</text>
</svg>"""

def _logo_pink(p, d):
	return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 64">
  <defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="{p}"/><stop offset="100%" stop-color="{d}"/></linearGradient></defs>
  <path d="M23 50 Q7 38 7 24 Q7 12 16 12 Q20 12 23 17 Q26 12 30 12 Q39 12 39 24 Q39 38 23 50 Z" fill="url(#g)"/>
  <path d="M23 44 Q13 34 13 26 Q13 20 18 20 Q21 20 23 24 Q25 20 28 20 Q33 20 33 26 Q33 34 23 44 Z" fill="rgba(255,255,255,0.16)"/>
  <text x="48" y="38" font-family="{FONT}" font-size="21" font-weight="800" fill="#500724" letter-spacing="0.5">INVENTO</text>
  <text x="49" y="53" font-family="{FONT}" font-size="9" font-weight="600" fill="#DB2777" letter-spacing="4">WEBSHOP</text>
</svg>"""

def _logo_violet(p, d):
	import math
	pts = []
	for i in range(10):
		r = 23 if i % 2 == 0 else 10
		a = math.radians(i * 36 - 90)
		pts.append(f"{23 + r*math.cos(a):.1f},{31 + r*math.sin(a):.1f}")
	star = " ".join(pts)
	return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 64">
  <defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="{p}"/><stop offset="100%" stop-color="{d}"/></linearGradient></defs>
  <polygon points="{star}" fill="url(#g)"/>
  <text x="48" y="38" font-family="{FONT}" font-size="21" font-weight="800" fill="#2E1065" letter-spacing="0.5">INVENTO</text>
  <text x="49" y="53" font-family="{FONT}" font-size="9" font-weight="600" fill="#7C3AED" letter-spacing="4">WEBSHOP</text>
</svg>"""

LOGO_FN = {
	"black": _logo_black, "slate": _logo_slate, "blue": _logo_blue,
	"sky": _logo_sky, "teal": _logo_teal, "emerald": _logo_emerald,
	"green": _logo_green, "red": _logo_red, "orange": _logo_orange,
	"amber": _logo_amber, "pink": _logo_pink, "violet": _logo_violet,
}

# ── Carousel SVGs ─────────────────────────────────────────────────────────────

def _c1(t):
	p, d, l, f = t["p"], t["d"], t["l"], t["f"]
	tc, ts = "#0F172A", "#475569"
	return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1440 520" font-family="{FONT}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="{f}"/><stop offset="100%" stop-color="#FFFFFF"/></linearGradient>
  </defs>
  <rect width="1440" height="520" fill="url(#bg)"/>
  <polygon points="810,0 1440,0 1440,520 670,520" fill="{p}"/>
  <circle cx="1230" cy="160" r="240" fill="{d}" opacity="0.25"/>
  <circle cx="970" cy="430" r="175" fill="{l}" opacity="0.20"/>
  <circle cx="1400" cy="460" r="115" fill="{d}" opacity="0.16"/>
  <circle cx="1165" cy="260" r="158" fill="rgba(255,255,255,0.09)"/>
  <circle cx="1165" cy="260" r="108" fill="rgba(255,255,255,0.06)"/>
  <text x="100" y="162" font-size="12" font-weight="700" fill="{ts}" letter-spacing="5">WELCOME TO OUR STORE</text>
  <text x="100" y="252" font-size="70" font-weight="900" fill="{tc}" letter-spacing="-1">Shop the</text>
  <text x="100" y="334" font-size="70" font-weight="900" fill="{p}">Latest.</text>
  <text x="100" y="382" font-size="19" fill="{ts}" opacity="0.9">Discover handpicked products crafted for you.</text>
  <rect x="100" y="412" width="196" height="54" rx="27" fill="{p}"/>
  <text x="198" y="445" font-size="16" font-weight="700" fill="#FFFFFF" text-anchor="middle">Shop Now &#x2192;</text>
</svg>"""

def _c2(t):
	p, d, l, f = t["p"], t["d"], t["l"], t["f"]
	tc, ts = "#0F172A", "#475569"
	return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1440 520" font-family="{FONT}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="{f}"/><stop offset="55%" stop-color="#FFFFFF"/><stop offset="100%" stop-color="{f}"/>
    </linearGradient>
    <radialGradient id="rg" cx="68%" cy="50%" r="48%">
      <stop offset="0%" stop-color="{l}"/><stop offset="100%" stop-color="{d}"/>
    </radialGradient>
  </defs>
  <rect width="1440" height="520" fill="url(#bg)"/>
  <circle cx="1055" cy="260" r="248" fill="url(#rg)" opacity="0.90"/>
  <circle cx="1055" cy="260" r="198" fill="rgba(255,255,255,0.08)"/>
  <circle cx="820" cy="90" r="74" fill="{p}" opacity="0.12"/>
  <circle cx="1288" cy="68" r="54" fill="{l}" opacity="0.22"/>
  <circle cx="1322" cy="434" r="86" fill="{d}" opacity="0.12"/>
  <rect x="100" y="145" width="110" height="34" rx="17" fill="{p}"/>
  <text x="155" y="168" font-size="12" font-weight="800" fill="#FFFFFF" text-anchor="middle" letter-spacing="3">NEW</text>
  <text x="100" y="272" font-size="74" font-weight="900" fill="{tc}" letter-spacing="-1">Fresh</text>
  <text x="100" y="356" font-size="74" font-weight="900" fill="{p}" letter-spacing="-1">Arrivals</text>
  <text x="100" y="400" font-size="19" fill="{ts}" opacity="0.88">The season&apos;s best, just landed.</text>
  <rect x="100" y="426" width="228" height="54" rx="27" fill="{p}"/>
  <text x="214" y="459" font-size="16" font-weight="700" fill="#FFFFFF" text-anchor="middle">Explore Collection &#x2192;</text>
</svg>"""

def _c3(t):
	p, d, f = t["p"], t["d"], t["f"]
	return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1440 520" font-family="{FONT}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{d}"/><stop offset="100%" stop-color="{p}"/>
    </linearGradient>
    <linearGradient id="badge" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#FFFFFF" stop-opacity="0.98"/><stop offset="100%" stop-color="{f}"/>
    </linearGradient>
  </defs>
  <rect width="1440" height="520" fill="url(#bg)"/>
  <ellipse cx="210" cy="520" rx="430" ry="215" fill="rgba(255,255,255,0.05)"/>
  <ellipse cx="1310" cy="0" rx="370" ry="195" fill="rgba(255,255,255,0.05)"/>
  <circle cx="1108" cy="260" r="218" fill="url(#badge)" opacity="0.97"/>
  <circle cx="1108" cy="260" r="178" fill="rgba(255,255,255,0.07)"/>
  <text x="1108" y="215" font-size="26" font-weight="800" fill="{d}" text-anchor="middle" letter-spacing="1">UP TO</text>
  <text x="1108" y="306" font-size="94" font-weight="900" fill="{p}" text-anchor="middle" letter-spacing="-2">50%</text>
  <text x="1108" y="346" font-size="26" font-weight="800" fill="{d}" text-anchor="middle" letter-spacing="2">OFF</text>
  <text x="100" y="175" font-size="12" font-weight="700" fill="rgba(255,255,255,0.70)" letter-spacing="5">LIMITED TIME OFFER</text>
  <text x="100" y="268" font-size="72" font-weight="900" fill="#FFFFFF" letter-spacing="-1">Exclusive</text>
  <text x="100" y="350" font-size="72" font-weight="900" fill="#FFFFFF" letter-spacing="-1">Deals.</text>
  <text x="100" y="394" font-size="18" fill="rgba(255,255,255,0.82)">Shop premium products at unbeatable prices.</text>
  <rect x="100" y="420" width="210" height="54" rx="27" fill="#FFFFFF"/>
  <text x="205" y="453" font-size="16" font-weight="700" fill="{p}" text-anchor="middle">Grab the Deal &#x2192;</text>
</svg>"""

# ── Helpers ───────────────────────────────────────────────────────────────────

def _write(files_dir, filename, content):
	path = os.path.join(files_dir, filename)
	with open(path, "w", encoding="utf-8") as fh:
		fh.write(content)
	return f"/files/{filename}"

# ── Patch entry point ─────────────────────────────────────────────────────────

def execute():
	if not frappe.db.table_exists("tabWebshop Theme"):
		return

	files_dir = os.path.join(frappe.get_site_path(), "public", "files")
	os.makedirs(files_dir, exist_ok=True)

	for t in THEMES:
		slug = t["slug"]
		theme_name = t["name"]

		logo_url = _write(files_dir, f"ws_theme_{slug}_logo.svg",
		                  LOGO_FN[slug](t["p"], t["d"]))
		c1_url   = _write(files_dir, f"ws_theme_{slug}_c1.svg", _c1(t))
		c2_url   = _write(files_dir, f"ws_theme_{slug}_c2.svg", _c2(t))
		c3_url   = _write(files_dir, f"ws_theme_{slug}_c3.svg", _c3(t))

		if frappe.db.exists("Webshop Theme", theme_name):
			frappe.db.set_value("Webshop Theme", theme_name, {
				"logo":            logo_url,
				"carousel_image_1": c1_url,
				"carousel_image_2": c2_url,
				"carousel_image_3": c3_url,
			})

	frappe.db.commit()
