# Copyright (c) 2026, Invento and contributors
# For license information, please see license.txt

"""
Google Business Reviews Statistics
Helper functions to calculate and display review statistics
"""

import frappe
from frappe.utils import flt
from typing import Dict, Optional


# Star SVG paths for rating display
STAR_PATHS = [
	"M13.6743 0.552305C13.7413 0.388954 13.8553 0.249215 14.0019 0.150865C14.1486 0.0525153 14.3211 0 14.4977 0C14.6742 0 14.8468 0.0525153 14.9934 0.150865C15.14 0.249215 15.254 0.388954 15.321 0.552305L18.6856 8.64472C18.7486 8.79614 18.8521 8.92726 18.9848 9.02363C19.1175 9.12001 19.2742 9.17791 19.4377 9.19097L28.1745 9.8908C28.9646 9.95414 29.2844 10.9406 28.6827 11.4551L22.0264 17.1583C21.902 17.2647 21.8094 17.4033 21.7585 17.5588C21.7077 17.7144 21.7007 17.8809 21.7382 18.0402L23.7728 26.5665C23.8137 26.7375 23.803 26.9169 23.742 27.0818C23.6811 27.2468 23.5726 27.39 23.4302 27.4934C23.2879 27.5967 23.1182 27.6556 22.9424 27.6625C22.7667 27.6694 22.5928 27.6241 22.4428 27.5323L14.9616 22.9644C14.8219 22.879 14.6614 22.8339 14.4977 22.8339C14.334 22.8339 14.1734 22.879 14.0337 22.9644L6.55249 27.5339C6.40248 27.6257 6.22862 27.671 6.05288 27.6641C5.87714 27.6572 5.70739 27.5983 5.56507 27.495C5.42276 27.3916 5.31426 27.2484 5.25329 27.0834C5.19231 26.9185 5.1816 26.7391 5.22249 26.5681L7.25707 18.0402C7.29481 17.8809 7.28787 17.7143 7.23703 17.5587C7.18619 17.4031 7.09341 17.2646 6.96891 17.1583L0.312572 11.4551C0.178532 11.3409 0.0814162 11.1894 0.033525 11.0199C-0.0143662 10.8504 -0.0108784 10.6705 0.0435464 10.503C0.0979712 10.3355 0.200885 10.1879 0.339253 10.0789C0.477621 9.96993 0.64522 9.90446 0.820822 9.8908L9.55766 9.19097C9.72113 9.17791 9.87784 9.12001 10.0105 9.02363C10.1432 8.92726 10.2468 8.79614 10.3097 8.64472L13.6743 0.552305Z",
	"M50.6704 0.552305C50.7374 0.388954 50.8514 0.249215 50.998 0.150865C51.1447 0.0525153 51.3172 0 51.4937 0C51.6703 0 51.8428 0.0525153 51.9895 0.150865C52.1361 0.249215 52.2501 0.388954 52.3171 0.552305L55.6817 8.64472C55.7446 8.79614 55.8482 8.92726 55.9809 9.02363C56.1136 9.12001 56.2703 9.17791 56.4338 9.19097L65.1706 9.8908C65.9607 9.95414 66.2805 10.9406 65.6788 11.4551L59.0225 17.1583C58.8981 17.2647 58.8055 17.4033 58.7546 17.5588C58.7038 17.7144 58.6968 17.8809 58.7343 18.0402L60.7689 26.5665C60.8098 26.7375 60.7991 26.9169 60.7381 27.0818C60.6771 27.2468 60.5686 27.39 60.4263 27.4934C60.284 27.5967 60.1143 27.6556 59.9385 27.6625C59.7628 27.6694 59.5889 27.6241 59.4389 27.5323L51.9577 22.9644C51.818 22.879 51.6574 22.8339 51.4937 22.8339C51.3301 22.8339 51.1695 22.879 51.0298 22.9644L43.5486 27.5339C43.3986 27.6257 43.2247 27.671 43.049 27.6641C42.8732 27.6572 42.7035 27.5983 42.5612 27.495C42.4189 27.3916 42.3104 27.2484 42.2494 27.0834C42.1884 26.9185 42.1777 26.7391 42.2186 26.5681L44.2532 18.0402C44.2909 17.8809 44.284 17.7143 44.2331 17.5587C44.1823 17.4031 44.0895 17.2646 43.965 17.1583L37.3087 11.4551C37.1746 11.3409 37.0775 11.1894 37.0296 11.0199C36.9817 10.8504 36.9852 10.6705 37.0396 10.503C37.0941 10.3355 37.197 10.1879 37.3353 10.0789C37.4737 9.96993 37.6413 9.90446 37.8169 9.8908L46.5538 9.19097C46.7172 9.17791 46.8739 9.12001 47.0066 9.02363C47.1393 8.92726 47.2429 8.79614 47.3058 8.64472L50.6704 0.552305Z",
	"M87.6665 0.552305C87.7335 0.388954 87.8475 0.249215 87.9941 0.150865C88.1407 0.0525153 88.3133 0 88.4898 0C88.6664 0 88.8389 0.0525153 88.9856 0.150865C89.1322 0.249215 89.2462 0.388954 89.3132 0.552305L92.6778 8.64472C92.7407 8.79614 92.8443 8.92726 92.977 9.02363C93.1097 9.12001 93.2664 9.17791 93.4298 9.19097L102.167 9.8908C102.957 9.95414 103.277 10.9406 102.675 11.4551L96.0186 17.1583C95.8942 17.2647 95.8016 17.4033 95.7507 17.5588C95.6999 17.7144 95.6929 17.8809 95.7304 18.0402L97.765 26.5665C97.8059 26.7375 97.7952 26.9169 97.7342 27.0818C97.6732 27.2468 97.5647 27.39 97.4224 27.4934C97.2801 27.5967 97.1104 27.6556 96.9346 27.6625C96.7589 27.6694 96.585 27.6241 96.435 27.5323L88.9538 22.9644C88.8141 22.879 88.6535 22.8339 88.4898 22.8339C88.3261 22.8339 88.1656 22.879 88.0259 22.9644L80.5447 27.5339C80.3947 27.6257 80.2208 27.671 80.0451 27.6641C79.8693 27.6572 79.6996 27.5983 79.5573 27.495C79.4149 27.3916 79.3064 27.2484 79.2455 27.0834C79.1845 26.9185 79.1738 26.7391 79.2147 26.5681L81.2493 18.0402C81.287 17.8809 81.2801 17.7143 81.2292 17.5587C81.1784 17.4031 81.0856 17.2646 80.9611 17.1583L74.3048 11.4551C74.1707 11.3409 74.0736 11.1894 74.0257 11.0199C73.9778 10.8504 73.9813 10.6705 74.0357 10.503C74.0902 10.3355 74.1931 10.1879 74.3314 10.0789C74.4698 9.96993 74.6374 9.90446 74.813 9.8908L83.5498 9.19097C83.7133 9.17791 83.87 9.12001 84.0027 9.02363C84.1354 8.92726 84.2389 8.79614 84.3019 8.64472L87.6665 0.552305Z",
	"M124.659 0.552305C124.726 0.388954 124.84 0.249215 124.986 0.150865C125.133 0.0525153 125.305 0 125.482 0C125.659 0 125.831 0.0525153 125.978 0.150865C126.124 0.249215 126.238 0.388954 126.305 0.552305L129.67 8.64472C129.733 8.79614 129.836 8.92726 129.969 9.02363C130.102 9.12001 130.259 9.17791 130.422 9.19097L139.159 9.8908C139.949 9.95414 140.269 10.9406 139.667 11.4551L133.011 17.1583C132.886 17.2647 132.794 17.4033 132.743 17.5588C132.692 17.7144 132.685 17.8809 132.723 18.0402L134.757 26.5665C134.798 26.7375 134.787 26.9169 134.726 27.0818C134.665 27.2468 134.557 27.39 134.415 27.4934C134.272 27.5967 134.103 27.6556 133.927 27.6625C133.751 27.6694 133.577 27.6241 133.427 27.5323L125.946 22.9644C125.806 22.879 125.646 22.8339 125.482 22.8339C125.318 22.8339 125.158 22.879 125.018 22.9644L117.537 27.5339C117.387 27.6257 117.213 27.671 117.037 27.6641C116.862 27.6572 116.692 27.5983 116.549 27.495C116.407 27.3916 116.299 27.2484 116.238 27.0834C116.177 26.9185 116.166 26.7391 116.207 26.5681L118.241 18.0402C118.279 17.8809 118.272 17.7143 118.221 17.5587C118.171 17.4031 118.078 17.2646 117.953 17.1583L111.297 11.4551C111.163 11.3409 111.066 11.1894 111.018 11.0199C110.97 10.8504 110.973 10.6705 111.028 10.503C111.082 10.3355 111.185 10.1879 111.324 10.0789C111.462 9.96993 111.63 9.90446 111.805 9.8908L120.542 9.19097C120.706 9.17791 120.862 9.12001 120.995 9.02363C121.128 8.92726 121.231 8.79614 121.294 8.64472L124.659 0.552305Z",
	"M161.655 0.552305C161.722 0.388954 161.836 0.249215 161.982 0.150865C162.129 0.0525153 162.302 0 162.478 0C162.655 0 162.827 0.0525153 162.974 0.150865C163.12 0.249215 163.234 0.388954 163.301 0.552305L166.666 8.64472C166.729 8.79614 166.833 8.92726 166.965 9.02363C167.098 9.12001 167.255 9.17791 167.418 9.19097L176.155 9.8908C176.945 9.95414 177.265 10.9406 176.663 11.4551L170.007 17.1583C169.883 17.2647 169.79 17.4033 169.739 17.5588C169.688 17.7144 169.681 17.8809 169.719 18.0402L171.753 26.5665C171.794 26.7375 171.783 26.9169 171.722 27.0818C171.662 27.2468 171.553 27.39 171.411 27.4934C171.268 27.5967 171.099 27.6556 170.923 27.6625C170.747 27.6694 170.573 27.6241 170.423 27.5323L162.942 22.9644C162.802 22.879 162.642 22.8339 162.478 22.8339C162.314 22.8339 162.154 22.879 162.014 22.9644L154.533 27.5339C154.383 27.6257 154.209 27.671 154.033 27.6641C153.858 27.6572 153.688 27.5983 153.546 27.495C153.403 27.3916 153.295 27.2484 153.234 27.0834C153.173 26.9185 153.162 26.7391 153.203 26.5681L155.238 18.0402C155.275 17.8809 155.268 17.7143 155.217 17.5587C155.167 17.4031 155.074 17.2646 154.949 17.1583L148.293 11.4551C148.159 11.3409 148.062 11.1894 148.014 11.0199C147.966 10.8504 147.97 10.6705 148.024 10.503C148.078 10.3355 148.181 10.1879 148.32 10.0789C148.458 9.96993 148.626 9.90446 148.801 9.8908L157.538 9.19097C157.702 9.17791 157.858 9.12001 157.991 9.02363C158.124 8.92726 158.227 8.79614 158.29 8.64472L161.655 0.552305Z"
]


def get_star_svg(rating):
	"""
	Generate an SVG string for the given star rating (0-5).
	The filled portion is clipped based on the rating percentage.
	
	Args:
		rating: Rating value (0-5)
		
	Returns:
		str: SVG markup for star rating display
	"""
	rating = flt(rating)
	if rating < 0:
		rating = 0
	if rating > 5:
		rating = 5

	# Calculate width of the filled rect (total width is 177)
	# 5 stars = 100% = 177px
	filled_width = (rating / 5) * 177

	# Generate a unique ID for the clip path to avoid conflicts if multiple SVGs are on page
	clip_id = f"stars-clip-{frappe.generate_hash(length=6)}"
	
	paths_str = "".join([f'<path d="{p}" />' for p in STAR_PATHS])

	svg = f"""<svg width="177" height="28" viewBox="0 0 177 28" fill="none" xmlns="http://www.w3.org/2000/svg">
<defs>
<clipPath id="{clip_id}">
{paths_str}
</clipPath>
</defs>
<rect width="177" height="28" fill="#D9D9D9" clip-path="url(#{clip_id})" />
<rect width="{filled_width}" height="28" fill="#F49F00" clip-path="url(#{clip_id})" />
</svg>"""
	
	return svg


def get_review_statistics(google_account_name: Optional[str] = None) -> Dict:
	"""
	Calculate review statistics from Google Business Reviews
	
	Args:
		google_account_name: Optional filter by specific Google Business Account
		
	Returns:
		Dict with average_rating, total_reviews, rating_distribution
	"""
	filters = {}
	if google_account_name:
		filters["google_account"] = google_account_name
	
	# Fetch all reviews
	reviews = frappe.get_all(
		"Google Business Review",
		filters=filters,
		fields=["star_rating"]
	)
	
	if not reviews:
		return {
			"average_rating": 0.0,
			"total_reviews": 0,
			"rating_distribution": {
				"FIVE": 0, "FOUR": 0, "THREE": 0, "TWO": 0, "ONE": 0
			}
		}
	
	# Count ratings
	rating_counts = {
		"FIVE": 0, "FOUR": 0, "THREE": 0, "TWO": 0, "ONE": 0
	}
	
	rating_values = {
		"FIVE": 5, "FOUR": 4, "THREE": 3, "TWO": 2, "ONE": 1
	}
	
	total_score = 0
	
	for review in reviews:
		rating = review.star_rating
		rating_counts[rating] += 1
		total_score += rating_values[rating]
	
	total_reviews = len(reviews)
	average_rating = total_score / total_reviews if total_reviews > 0 else 0.0
	
	return {
		"average_rating": round(average_rating, 1),
		"total_reviews": total_reviews,
		"rating_distribution": rating_counts
	}

@frappe.whitelist()
def get_review_summary_text(google_account_name: Optional[str] = None) -> str:
	"""
	Generate review summary text like "4.7 out of 5 based on 808 reviews"
	
	Args:
		google_account_name: Optional filter by specific Google Business Account
		
	Returns:
		str: Formatted summary text
	"""
	stats = get_review_statistics(google_account_name)
	
	if stats["total_reviews"] == 0:
		return "No reviews yet"
	
	avg = stats["average_rating"]
	total = stats["total_reviews"]
	
	review_word = "review" if total == 1 else "reviews"
	
	return f"{avg} out of 5 based on {total} {review_word}"


@frappe.whitelist(allow_guest=True)
def get_review_stats_api(google_account_name: Optional[str] = None) -> Dict:
	"""
	API endpoint to get review statistics with all reviews
	
	Args:
		google_account_name: Optional filter by specific Google Business Account
		
	Returns:
		Dict with statistics, formatted text, star SVG, and all reviews with their SVGs
	"""
	stats = get_review_statistics(google_account_name)
	summary_text = get_review_summary_text(google_account_name)
	star_svg = get_star_svg(stats["average_rating"])
	
	# Fetch all reviews with details
	filters = {}
	if google_account_name:
		filters["google_account"] = google_account_name
	
	reviews = frappe.get_all(
		"Google Business Review",
		filters=filters,
		fields=[
			"name",
			"review_id",
			"reviewer_name",
			"star_rating",
			"comment",
			"review_time",
			"profile_photo_url",
			"reply_comment",
			"reply_time"
		],
		order_by="review_time desc"
	)
	
	# Convert star rating enum to numeric and add SVG for each review
	rating_map = {
		"FIVE": 5, "FOUR": 4, "THREE": 3, "TWO": 2, "ONE": 1
	}
	
	for review in reviews:
		numeric_rating = rating_map.get(review.star_rating, 1)
		review["numeric_rating"] = numeric_rating
		review["star_svg"] = get_star_svg(numeric_rating)
	
	return {
		**stats,
		"summary_text": summary_text,
		"star_svg": star_svg,
		"reviews": reviews
	}


# Example usage in Python:
# -------------------------
# from invento_webshop.google_business.review_stats import get_review_summary_text, get_review_statistics
#
# # Get summary text
# summary = get_review_summary_text()
# print(summary)  # Output: "4.7 out of 5 based on 808 reviews"
#
# # Get detailed statistics
# stats = get_review_statistics()
# print(f"Average: {stats['average_rating']}")
# print(f"Total: {stats['total_reviews']}")
# print(f"5 stars: {stats['rating_distribution']['FIVE']}")
#
# # Filter by specific account
# summary = get_review_summary_text(google_account_name="Demo Account")


# Example usage in Jinja template:
# ---------------------------------
# {% set stats = frappe.call('invento_webshop.google_business.review_stats.get_review_stats_api') %}
# <div class="review-summary">
#     <h3>{{ stats.summary_text }}</h3>
#     <div class="rating">{{ stats.average_rating }} ⭐</div>
#     <div class="total">{{ stats.total_reviews }} reviews</div>
# </div>


# Example usage in JavaScript:
# -----------------------------
# frappe.call({
#     method: 'invento_webshop.google_business.review_stats.get_review_stats_api',
#     args: {
#         google_account_name: 'Demo Account'  // optional
#     },
#     callback: function(r) {
#         console.log(r.message.summary_text);
#         // Output: "4.7 out of 5 based on 808 reviews"
#     }
# });
