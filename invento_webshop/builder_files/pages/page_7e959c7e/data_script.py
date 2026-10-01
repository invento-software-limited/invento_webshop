data.page_data = {
  'csrf_token': frappe.session.csrf_token
}
data.user = frappe.session.user
data.metatags = {
    "og:type": "website"
}