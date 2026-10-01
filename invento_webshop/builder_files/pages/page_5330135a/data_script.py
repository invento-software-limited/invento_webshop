items = frappe.call('invento_webshop.api.item.get_on_sale_items')
faqs = frappe.get_all(
    "FAQ",
    fields=["topic", "question", "answer"],
    limit_page_length=5
)

# blogs = frappe.get_all(
#   "Blog Post",
#   fields=["name", "title", "blog_category","blogger", "route", "published_on", "blog_intro", "meta_image"]
# )

# for blog in blogs:
#     blog.image = f"url('{blog.meta_image}')"
    
#     if blog.published_on:
#         blog.published_on_formatted = frappe.utils.formatdate(
#             blog.published_on,
#             "MMMM d, yyyy"
#         )

review_stats = frappe.call('invento_webshop.google_business.review_stats.get_review_stats_api')

data.reviews = review_stats.get('reviews')
data.review_text = review_stats.get('summary_text')
data.review_svg = review_stats.get('star_svg')
# data.blogs = blogs
data.blogs = []
data.faqs = faqs
data.user = frappe.session.user
data.items = items.get('items')
data.total_items = 0 if frappe.session.user == "Guest" else items.get("items_count")
data.include_item_section = data.total_items > 0
data.include_reviews_section = len(data.reviews) > 0
data.include_blogs_section = 0
# data.include_blogs_section = len(blogs) > 0
data.metatags = {
    "og:type": "website"
}