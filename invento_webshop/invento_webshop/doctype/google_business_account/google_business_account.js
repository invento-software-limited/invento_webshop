frappe.ui.form.on('Google Business Account', {
    refresh: function (frm) {
        // Add Authorize with Google button if not authorized
        if (!frm.is_new() && (!frm.doc.refresh_token || frm.doc.authorization_status !== 'Authorized')) {
            frm.add_custom_button(__('Authorize with Google'), function () {
                frappe.call({
                    method: 'invento_webshop.google_business.oauth.get_authorization_url',
                    args: {
                        account_name: frm.doc.name
                    },
                    callback: function (r) {
                        if (r.message) {
                            // Open OAuth URL in new window
                            window.open(r.message, '_blank', 'width=600,height=700');

                            frappe.msgprint({
                                title: __('Authorization Required'),
                                message: __('Please complete the authorization in the popup window. After authorization, refresh this page and enter your Location ID.'),
                                indicator: 'blue'
                            });
                        }
                    }
                });
            }).addClass('btn-primary');
        }

        // Add Sync Reviews button only if authorized and location set
        if (!frm.is_new() && frm.doc.enabled && frm.doc.refresh_token &&
            frm.doc.authorization_status === 'Authorized' && frm.doc.location_id) {
            frm.add_custom_button(__('Sync Reviews'), function () {
                frappe.call({
                    method: 'invento_webshop.google_business.google_reviews.sync_reviews',
                    args: {
                        google_account_name: frm.doc.name
                    },
                    freeze: true,
                    freeze_message: __('Fetching reviews from Google...'),
                    callback: function (r) {
                        if (r.message) {
                            frm.reload_doc();
                        }
                    }
                });
            }).addClass('btn-primary');
        }
        // Add Fetch Locations button only if authorized
        if (frm.doc.refresh_token && frm.doc.authorization_status === 'Authorized') {
            frm.add_custom_button(__('Fetch Locations'), function () {
                frappe.call({
                    method: 'invento_webshop.google_business.oauth.get_google_business_locations',
                    args: {
                        account_name: frm.doc.name
                    },
                    freeze: true,
                    freeze_message: __('Fetching locations from Google...'),
                    callback: function (r) {
                        if (r.message && r.message.length > 0) {
                            let locations = r.message;
                            let html = `
                                <div class="table-responsive">
                                    <table class="table table-bordered table-hover" style="margin-bottom: 0;">
                                        <thead>
                                            <tr>
                                                <th>${__('Location Name')}</th>
                                                <th>${__('Location ID')}</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            ${locations.map(loc => {
                                let loc_id = loc.name.split('/').pop();
                                return `
                                                    <tr>
                                                       <td>${loc.title}</td>
                                                       <td><code>${loc_id}</code></td>
                                                    </tr>
                                                `;
                            }).join('')}
                                        </tbody>
                                    </table>
                                </div>
                            `;

                            let d = new frappe.ui.Dialog({
                                title: __('Available Locations'),
                                fields: [
                                    {
                                        fieldtype: 'HTML',
                                        fieldname: 'loc_list',
                                        options: html
                                    }
                                ],
                                primary_action_label: __('Close'),
                                primary_action() {
                                    d.hide();
                                }
                            });
                            d.show();
                        } else {
                            frappe.msgprint(__('No locations found for this account.'));
                        }
                    }
                });
            });
        }
    }
});
