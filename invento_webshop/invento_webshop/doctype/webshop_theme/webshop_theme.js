// Copyright (c) 2026, Invento Software Limited and contributors
// For license information, please see license.txt

frappe.ui.form.on("Webshop Theme", {
	refresh(frm) {
		const is_applied = frm.doc.status === "Applied";

		if (!frm.is_new()) {
			if (is_applied) {
				frm.set_intro(__("This theme is currently applied to the webshop."), "green");
			}

			frm.add_custom_button(
				is_applied ? __("Applied ✓") : __("Apply Theme"),
				function () {
					if (is_applied) return;
					frappe.confirm(
						__("Apply <b>{0}</b> to the webshop? This will overwrite Webshop Settings and clear all caches.", [frm.doc.theme_name]),
						function () {
							frappe.call({
								method: "invento_webshop.invento_webshop.doctype.webshop_theme.webshop_theme.apply_theme",
								args: { name: frm.doc.name },
								freeze: true,
								freeze_message: __("Applying theme and clearing cache…"),
								callback: function (r) {
									if (!r.exc) {
										frappe.show_alert({ message: __("Theme applied successfully"), indicator: "green" });
										frm.reload_doc();
									}
								},
							});
						}
					);
				},
				is_applied ? "success" : "primary"
			);
		}
	},
});
