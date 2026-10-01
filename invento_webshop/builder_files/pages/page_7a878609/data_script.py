downloads = frappe.get_all(
    "Website Download",
    fields=["title", "description", "category", "file", "file_type", "file_size"],
    filters={'is_published': 1}
)
data.downloads = downloads
data.catalogue_brochures = [
    d for d in downloads if d.category == "Catalogues"
]

data.safety_data_sheets = [
    d for d in downloads if d.category == "Safety Data Sheets"
]

data.manuals_product_data = [
    d for d in downloads if d.category == "Technical Data Sheets"
]
data.user = frappe.session.user
data.metatags = {
    "og:type": "website"
}