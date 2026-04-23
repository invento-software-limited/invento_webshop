// Copyright (c) 2026, Invento Software Limited and contributors
// For license information, please see license.txt

frappe.ui.form.on("Webshop Settings", {
	refresh(frm) {
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
		});

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
