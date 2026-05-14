// Copyright (c) 2026, Invento Software Limited and contributors
// For license information, please see license.txt

frappe.ui.form.on("Webshop Settings", {
	refresh(frm) {
		// ── Reset to Applied Theme ─────────────────────────────────────────
		frm.add_custom_button(__("Reset to Applied Theme"), function () {
			frappe.confirm(
				__("This will restore all settings, images and builder assets from the currently applied theme. Any manual changes will be overwritten. Continue?"),
				function () {
					frappe.call({
						method: "invento_webshop.api.webshop_settings.reset_to_applied_theme",
						freeze: true,
						freeze_message: __("Restoring theme settings and rebuilding assets…"),
						callback: function (r) {
							if (!r.exc) {
								frm.reload_doc();
								frappe.show_alert({
									message: __("Theme settings restored successfully"),
									indicator: "green",
								});
							}
						},
					});
				}
			);
		}, __("Theme"));

		// ── Reset Colors to Default ────────────────────────────────────────
		frm.add_custom_button(__("Reset Colors to Default"), function () {
			frappe.confirm(
				__("Reset all brand colors to their default values?"),
				function () {
					frappe.call({
						method: "invento_webshop.api.webshop_settings.reset_colors",
						freeze: true,
						freeze_message: __("Resetting colors…"),
						callback: function () {
							frm.reload_doc();
							frappe.show_alert({ message: __("Colors reset to defaults"), indicator: "green" });
						},
					});
				}
			);
		}, __("Theme"));

		// ── Clear Cache ────────────────────────────────────────────────────
		frm.add_custom_button(__("Clear Cache"), function () {
			frappe.call({
				method: "invento_webshop.api.webshop_settings.clear_all_cache",
				freeze: true,
				freeze_message: __("Clearing cache…"),
				callback: function () {
					frappe.show_alert({ message: __("Cache cleared"), indicator: "green" });
				},
			});
		});
	},
});
