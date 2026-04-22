# Copyright (c) 2026, Invento Software Limited and contributors
# For license information, please see license.txt

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
	def on_update(self):
		self._sync_stable_assets()

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
