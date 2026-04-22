frappe.listview_settings['Item'] = {
  onload: function(listview) {
    listview.page.add_menu_item('Update Route', () => {
      frappe.call({
        method: 'invento_webshop.hook_functions.item.enqueue_update_products_route',
        callback: function(r) {
          if (r.message) {
            frappe.msgprint(r.message);
            listview.refresh();
          } else {
            frappe.msgprint(__('Failed to queue route update.'));
          }
        }
      });
    });
  }
}
