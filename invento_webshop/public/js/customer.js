frappe.ui.form.on('Customer', {
    refresh: function (frm) {
        if (!frm.doc.custom_is_approved && !frm.is_new()) {
            frm.add_custom_button(__('Approve'), function () {
                if(!frm.doc.tax_category && frm.is_dirty){
                    frappe.throw("Error: Value missing for Customer: Tax Category")
                }
                frappe.call({
                    method: 'invento_webshop.api.customer.approve_customer',
                    freeze: true,
                    freeze_message: __('Approving Customer...'),
                    args: {
                        customer: frm.doc.name
                    },
                    callback: function (r) {
                        if (!r.exc) {
                            frappe.msgprint(__('Customer Approved and User created.'));
                            frm.reload_doc();
                        }
                    }
                });
            }).addClass('btn-primary');
        }
    },
    validate: function(frm){
        if(!frm.doc.tax_category){
            frappe.throw("Error: Value missing for Customer: Tax Category")
        }
    }
});
