import frappe
from invento_webshop.webshop_functions.items import ProductQuery

@frappe.whitelist(allow_guest=True)
def get_item_groups_data():
	"""
	Return all item groups (except 'All Item Groups') with item counts.
	Item count includes items in descendant groups.
	"""

	group_filters = {
		"name": ["!=", "All Item Groups"],
		"custom_publish_to_website": 1,
	}
	
	groups = frappe.get_all("Item Group", 
		filters=group_filters,
		fields=["name", "item_group_name", "image"],
		ignore_permissions=True
	)
	
	pq = ProductQuery()
	result = []
	
	for group in groups:
		filters = pq._build_group_count_filters(item_group=group.name)
		
		count = frappe.db.count("Item", filters=filters)
		
		result.append({
			"item_group_name": group.item_group_name,
			"image": group.image,
			"item_count": count
		})
		
	return result
