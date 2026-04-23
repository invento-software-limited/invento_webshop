import os
import shutil

import builder.utils as builder_utils
from builder.builder.doctype.builder_page.builder_page import BuilderPage


def _safe_copy_file_to_assets(source_path, file_url, assets_path, target_app="builder"):
	"""Same as builder's copy_file_to_assets but skips when source == dest."""
	filename = os.path.basename(file_url)
	dest_path = os.path.join(assets_path, filename)
	if os.path.abspath(source_path) != os.path.abspath(dest_path):
		shutil.copy2(source_path, dest_path)
	return f"/assets/{target_app}/builder_assets/{filename}"


class CustomBuilderPage(BuilderPage):
	def on_update(self):
		original = builder_utils.copy_file_to_assets
		builder_utils.copy_file_to_assets = _safe_copy_file_to_assets
		try:
			super().on_update()
		finally:
			builder_utils.copy_file_to_assets = original

	def get_context(self, context):
		super().get_context(context)
		context.setdefault("styles", []).append("/ws-colors.css")
