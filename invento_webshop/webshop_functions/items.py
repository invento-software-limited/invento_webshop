import frappe
from frappe.utils import flt, cint
from erpnext.utilities.product import get_price
from erpnext.stock.utils import get_stock_balance
from invento_webshop.webshop_functions.cart import get_party


def _can_see_price():
	"""Return True if the current user is allowed to see prices."""
	if frappe.session.user != "Guest":
		return True
	cached = frappe.cache.get_value("ws-price-settings")
	if cached is not None:
		return cached
	result = bool(cint(frappe.db.get_single_value("Webshop Settings", "show_price_for_guest")))
	frappe.cache.set_value("ws-price-settings", result, expires_in_sec=300)
	return result

@frappe.whitelist(allow_guest=True)
def get_filtered_items(filters=None):
	"""
	API endpoint for fetching filtered items.
	Args:
		filters (str or dict): JSON string or dict of filters.
	"""
	if isinstance(filters, str):
		filters = frappe.parse_json(filters)
	
	if not filters:
		filters = {}

	start = filters.get("start", 0)
	search_term = filters.get("search_term")
	item_group = filters.get("category_name")

	pq = ProductQuery()
	return pq.query(
		filters=filters, 
		search_term=search_term, 
		start=start, 
		item_group=item_group
	)

class ProductQuery:
	"""Query items directly from the Item DocType for the webshop."""

	def __init__(self):
		self.settings = self._get_settings()
		self.page_length = 20
		self.fields = [
			"item_code",
			"item_name",
			"description",
			"custom_route",
			"item_group",
			"sales_uom",
			"image",
			"stock_uom",
			"weight_per_unit",
			"brand",
			"has_variants",
			"custom_on_sale"
		]

	def _get_settings(self):
		"""
		Get default settings for the query.
		Since we cannot use Webshop Settings, we derive defaults.
		"""
		price_list = frappe.db.get_single_value("Selling Settings", "selling_price_list")
		customer_group = frappe.db.get_single_value("Selling Settings", "customer_group")

		party = None
		if frappe.session.user != "Guest":
			party_doc = get_party()
			if party_doc and party_doc.doctype == "Customer":
				party = party_doc
				customer_group = party_doc.customer_group
		
		return frappe._dict({
			"company": frappe.defaults.get_user_default("Company") or frappe.db.get_single_value("Global Defaults", "default_company"),
			"price_list": price_list or "Standard Selling",
			"default_customer_group": customer_group or "All Customer Groups",
			"party": party
		})

	def query(self, filters=None, search_term=None, start=0, item_group=None):
		"""
		Main query method to fetch items.
		args:
			filters (dict): Dictionary of filters (price, stock, attributes)
			search_term (str): Search keyword
			start (int): Pagination start
			item_group (str): Item Group filter
		"""
		start = cint(start)
		if not filters: filters = {}

		start = cint(start)
		if not filters: filters = {}

		db_filters = self._build_filters(filters, item_group)
		or_filters = self._build_or_filters(search_term)


		
		post_filter_needed = (
			filters.get("price_start") or 
			filters.get("price_end") or 
			filters.get("stock")
		)

		limit = cint(filters.get("limit") or filters.get("page_length") or self.page_length)

		items = frappe.get_all(
			"Item",
			fields=self.fields,
			filters=db_filters,
			or_filters=or_filters,
			start=start if not post_filter_needed else 0, # Cannot use DB skip if we filter after
			page_length=1000 if post_filter_needed else limit,
			order_by="creation desc",
			ignore_permissions=True
		)
		
		
		processed_items = []
		for item in items:
			detailed_item = self.get_item_details(item)
			
			if not self.check_filters(detailed_item, filters):
				continue
				
			processed_items.append(detailed_item)
			
			if not post_filter_needed and len(processed_items) >= limit:
				break

		if post_filter_needed:
			total_count = len(processed_items)
			paged_items = processed_items[start : start + limit]
		else:
			# If no post-filtering, we can get the total count from DB
			total_count = len(frappe.get_all("Item", filters=db_filters, or_filters=or_filters, pluck="name", ignore_permissions=True))
			paged_items = processed_items

		return {
			"items": paged_items,
			"items_count": total_count
		}

	def check_filters(self, item, filters):
		"""
		Apply in-memory filters for Price, Stock, etc.
		Returns True if item should be kept.
		"""
		# Price Filter
		price_start = flt(filters.get("price_start"))
		price_end = flt(filters.get("price_end"))
		
		if price_end > 0:
			rate = item.get("price_list_rate") or 0
			if not (price_start <= rate <= price_end):
				return False

		# Stock Filter
		stock_filters = filters.get("stock")
		if stock_filters:
			match = False
			is_in_stock = item.get("in_stock")
			
			if "in_stock" in stock_filters and is_in_stock:
				match = True
			
			if "on_backorder" in stock_filters:
				if not is_in_stock:
					match = True
					
			if "on_sale" in stock_filters:
				if item.get("custom_on_sale") or flt(item.get("discount_percent")) > 0:
					match = True
					
			if not match:
				return False

		return True

	def _build_filters(self, filters_dict, item_group):
		filters = [
			["custom_publish_on_website", "=", 1],
			["disabled", "=", 0],
			["is_sales_item", "=", 1]
		]

		if item_group:
			child_groups = frappe.get_all("Item Group", filters={"lft": [">=", frappe.db.get_value("Item Group", item_group, "lft")], "rgt": ["<=", frappe.db.get_value("Item Group", item_group, "rgt")]}, pluck="name", ignore_permissions=True)
			if child_groups:
				filters.append(["item_group", "in", child_groups])
			else:
				filters.append(["item_group", "=", item_group])

		if filters_dict and filters_dict.get("weight"):
			weights = filters_dict.get("weight")
			if weights:
				conditions = []
				for w in weights:
					parts = w.split(' ')
					if len(parts) >= 2:
						val = flt(parts[0])
						uom = " ".join(parts[1:])
						conditions.append(f"(weight_per_unit = {val} AND weight_uom = {frappe.db.escape(uom)})")
					elif len(parts) == 1:
						val = flt(parts[0])
						conditions.append(f"(weight_per_unit = {val})")

				if conditions:
					where_clause = " OR ".join(conditions)
					matching_items = frappe.db.sql(f"SELECT name FROM `tabItem` WHERE {where_clause}", pluck=True)
					
					if matching_items:
						filters.append(["name", "in", matching_items])
					else:
						filters.append(["name", "=", "No Match"])

		if filters_dict and filters_dict.get("custom_on_sale"):
			filters.append(["custom_on_sale", "=", 1])

		stock_filters = filters_dict.get("stock") if filters_dict else None
		if stock_filters and "on_sale" in stock_filters:
			filters.append(["custom_on_sale", "=", 1])

		return filters

	def _build_group_count_filters(self, item_group):
		filters = [
		["disabled", "=", 0],
		["custom_publish_on_website", "=", 1],
		["is_sales_item", "=", 1]
	]

		if item_group:
			child_groups = frappe.get_all("Item Group", filters={"lft": [">=", frappe.db.get_value("Item Group", item_group, "lft")], "rgt": ["<=", frappe.db.get_value("Item Group", item_group, "rgt")]}, pluck="name", ignore_permissions=True)
			if child_groups:
				filters.append(["item_group", "in", child_groups])
			else:
				filters.append(["item_group", "=", item_group])

		return filters

	def _build_or_filters(self, search_term):
		or_filters = []
		if search_term:
			or_filters = [
				["item_name", "like", f"%{search_term}%"],
				["item_code", "like", f"%{search_term}%"],
				["description", "like", f"%{search_term}%"]
			]
		return or_filters

	def get_item_details(self, item):
		"""Attach price and stock info to the item."""
		item.formatted_price = 0
		item.price_list_rate = 0

		if _can_see_price():
			if item.has_variants:
				variants = frappe.db.get_all("Item", filters={"variant_of": item.item_code, "disabled": 0}, pluck="name")
				if variants:
					min_price = float('inf')
					cheapest_variant_details = None

					for variant in variants:
						price_details = get_price(
							item_code=variant,
							price_list=self.settings.price_list,
							customer_group=self.settings.default_customer_group,
							company=self.settings.company,
							party=self.settings.party,
							qty=1
						)
						if price_details:
							rate = flt(price_details.get("price_list_rate"))
							if rate < min_price:
								min_price = rate
								cheapest_variant_details = price_details

					if cheapest_variant_details:
						item.price_list_rate = min_price
						formatted = frappe.format_value(min_price, dict(fieldtype="Currency"), doc=cheapest_variant_details)
						item.formatted_price = f"Starts at {formatted} per {item.stock_uom}"
			else:
				price_details = get_price(
					item_code=item.item_code,
					price_list=self.settings.price_list,
					customer_group=self.settings.default_customer_group,
					company=self.settings.company,
					party=self.settings.party,
					qty=1
				)

				if price_details:
					item.price_list_rate = price_details.get("price_list_rate")
					item.discount_percent = price_details.get("discount_percentage", 0)

					rate = price_details.get("rate") or price_details.get("price_list_rate")
					item.formatted_price = f"{frappe.format_value(rate, dict(fieldtype='Currency'), doc=price_details)} per {item.stock_uom}"


		is_stock_item = frappe.db.get_value("Item", item.item_code, "is_stock_item")
		
		if is_stock_item:
			# Check stock in all warehouses (permission safe for Guest)
			actual_qty = frappe.db.sql("""select sum(actual_qty) from `tabBin` where item_code = %s""", item.item_code)
			actual_qty = actual_qty[0][0] if actual_qty and actual_qty[0][0] else 0
			item.in_stock = actual_qty > 0
		else:
			item.in_stock = True

		item.item_image = item.image
		item.route = item.get("custom_route") or (f"/shop/{item.item_code}" if item.get("item_code") else "#")

		return item

