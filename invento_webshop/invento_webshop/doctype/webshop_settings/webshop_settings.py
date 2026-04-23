# Copyright (c) 2026, Invento Software Limited and contributors
# For license information, please see license.txt

import colorsys
import os
import shutil

import frappe
from frappe.model.document import Document

# Maps Webshop Settings field → stable filename in public/builder_assets/
STABLE_ASSET_MAP = {
	"carousel_image_1": "ws_carousel_1.webp",
	"carousel_image_2": "ws_carousel_2.webp",
	"carousel_image_3": "ws_carousel_3.webp",
	"logo": "ws_logo.webp",
}


class WebshopSettings(Document):
	def validate(self):
		self._derive_theme_colors()

	def on_update(self):
		self._sync_stable_assets()
		self._clear_color_cache()

	def _derive_theme_colors(self):
		primary = self.get("theme_primary")
		text = self.get("theme_text")
		bg = self.get("theme_bg")
		if not (primary or text or bg):
			return
		if primary:
			h, l, s = _hex_to_hls(primary)
			self.primary_color = primary
			self.primary_color_hover = _hls_to_hex(h, l - 0.10, s)
			self.primary_color_light = _hls_to_hex(h, l + 0.15, s)
			self.primary_color_faint = _hls_to_hex(h, 0.92, s * 0.25)
		if text:
			h, l, s = _hex_to_hls(text)
			self.primary_text_color = _hls_to_hex(h, max(0.08, l - 0.15), s)
			self.primary_text_hover = text
		if bg:
			h, l, s = _hex_to_hls(bg)
			self.light_bg_color = _hls_to_hex(h, min(0.97, l + 0.05), s)
			self.warm_bg_color = bg
			self.secondary_bg_color = _hls_to_hex(h, l, s * 0.15)

	def _clear_color_cache(self):
		frappe.cache.delete_keys("ws-colors")
		frappe.cache.delete_keys("ws-price-settings")

	def _sync_stable_assets(self):
		app_path = frappe.get_app_path("invento_webshop")
		assets_dir = os.path.join(app_path, "public", "builder_assets")
		os.makedirs(assets_dir, exist_ok=True)

		for field, stable_name in STABLE_ASSET_MAP.items():
			file_url = self.get(field)
			if not file_url:
				continue
			source_path = _resolve_file_path(file_url)
			if not source_path or not os.path.exists(source_path):
				continue
			dest_path = os.path.join(assets_dir, stable_name)
			if os.path.abspath(source_path) == os.path.abspath(dest_path):
				continue
			shutil.copy2(source_path, dest_path)


def _hex_to_hls(hex_color):
	hex_color = hex_color.lstrip("#")
	r = int(hex_color[0:2], 16) / 255
	g = int(hex_color[2:4], 16) / 255
	b = int(hex_color[4:6], 16) / 255
	return colorsys.rgb_to_hls(r, g, b)


def _hls_to_hex(h, l, s):
	l = max(0.0, min(1.0, l))
	s = max(0.0, min(1.0, s))
	r, g, b = colorsys.hls_to_rgb(h, l, s)
	return "#{:02X}{:02X}{:02X}".format(int(r * 255), int(g * 255), int(b * 255))


def _resolve_file_path(file_url):
	if file_url.startswith("/files/"):
		return os.path.join(frappe.local.site_path, "public", file_url.lstrip("/"))
	if file_url.startswith("/assets/"):
		parts = file_url.strip("/").split("/")
		# parts: ["assets", "<app>", ...]
		if len(parts) >= 3:
			app_name = parts[1]
			rel_path = "/".join(parts[2:])
			return os.path.join(frappe.get_app_path(app_name), "public", rel_path)
	return None
