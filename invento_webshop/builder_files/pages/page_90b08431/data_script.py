user = frappe.session.user
item_groups = frappe.call('invento_webshop.api.item_group.get_item_groups_data')
weight_counts = frappe.call('invento_webshop.api.item.get_item_weight_counts')

form = frappe.form_dict
price_start = frappe.form_dict.get("price_start", 0)
price_end = frappe.form_dict.get("price_end", 0)
category_name = frappe.form_dict.get("category_name")
page_length = frappe.form_dict.get("page_length", 20)
stock = frappe.request.args.getlist("stock[]")
weight = frappe.request.args.getlist("weight[]")

filters = {
    "price_start": price_start,
    "price_end": price_end,
    "category_name": category_name,
  	"page_length": page_length,
    "stock": stock,
    "weight": weight
}

items = frappe.call('invento_webshop.webshop_functions.items.get_filtered_items', filters=filters)

data.user = user
data.weight_counts = weight_counts
data.items = items.get('items')
data.total_items = items.get('items_count')
data.showing_line = f"Showing 1-{page_length} of {items.get('items_count')} results"
data.item_groups = item_groups
data.metatags = {
    "og:type": "website"
}