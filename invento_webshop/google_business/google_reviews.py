# Copyright (c) 2026, Invento and contributors
# For license information, please see license.txt

"""
Google Business Profile API Integration
Handles OAuth token refresh and review fetching
"""

import requests
import frappe
from frappe import _
from frappe.utils import now_datetime, get_datetime
from typing import Dict, List, Optional

TOKEN_URL = "https://oauth2.googleapis.com/token"
SCOPE = "https://www.googleapis.com/auth/business.manage"


def get_access_token(google_account) -> str:
	"""
	Refresh access token using stored refresh token
	
	Args:
		google_account: Google Business Account document
		
	Returns:
		str: Fresh access token
		
	Raises:
		Exception: If token refresh fails
	"""
	data = {
		"client_id": google_account.get_password("client_id"),
		"client_secret": google_account.get_password("client_secret"),
		"refresh_token": google_account.get_password("refresh_token"),
		"grant_type": "refresh_token"
	}
	
	try:
		response = requests.post(TOKEN_URL, data=data, timeout=30)
		response.raise_for_status()
		token_data = response.json()
		
		if "access_token" not in token_data:
			frappe.throw(_("Failed to get access token from Google"))
		
		return token_data.get("access_token")
	
	except requests.exceptions.RequestException as e:
		frappe.log_error(
			message=f"OAuth token refresh failed: {str(e)}",
			title="Google Business OAuth Error"
		)
		frappe.throw(_("Failed to refresh OAuth token. Please check credentials."))


def fetch_reviews(google_account) -> List[Dict]:
	"""
	Fetch reviews from Google Business Profile API with pagination
	
	Args:
		google_account: Google Business Account document
		
	Returns:
		List[Dict]: List of review objects
		
	Raises:
		Exception: If API call fails
	"""
	access_token = get_access_token(google_account)
	account_id = google_account.account_id
	location_id = google_account.location_id
	
	# Updated API endpoint for Google Business Profile API v1
	url = f"https://mybusinessaccountmanagement.googleapis.com/v1/accounts/{account_id}/locations/{location_id}/reviews"
	
	headers = {
		"Authorization": f"Bearer {access_token}",
		"Content-Type": "application/json"
	}
	
	reviews = []
	params = {"pageSize": 50}
	
	try:
		while True:
			response = requests.get(url, headers=headers, params=params, timeout=30)
			response.raise_for_status()
			data = response.json()
			
			# Add reviews from current page
			page_reviews = data.get("reviews", [])
			reviews.extend(page_reviews)
			
			frappe.publish_realtime(
				"google_reviews_progress",
				{"fetched": len(reviews)},
				user=frappe.session.user
			)
			
			# Check for next page
			next_token = data.get("nextPageToken")
			if not next_token:
				break
			
			params["pageToken"] = next_token
		
		return reviews
	
	except requests.exceptions.RequestException as e:
		frappe.log_error(
			message=f"Failed to fetch reviews: {str(e)}",
			title="Google Business API Error"
		)
		frappe.throw(_("Failed to fetch reviews from Google Business Profile API"))


def parse_star_rating(rating_enum: str) -> str:
	"""
	Convert Google's star rating enum to readable format
	
	Args:
		rating_enum: Star rating enum (e.g., "FIVE", "FOUR")
		
	Returns:
		str: Star rating enum value
	"""
	rating_map = {
		"STAR_RATING_UNSPECIFIED": "ONE",
		"ONE": "ONE",
		"TWO": "TWO",
		"THREE": "THREE",
		"FOUR": "FOUR",
		"FIVE": "FIVE"
	}
	return rating_map.get(rating_enum, "ONE")


def save_reviews_to_frappe(google_account_name: str) -> Dict:
	"""
	Fetch reviews and save them to Frappe DocType
	
	Args:
		google_account_name: Name of the Google Business Account document
		
	Returns:
		Dict: Summary of sync operation
	"""
	google_account = frappe.get_doc("Google Business Account", google_account_name)
	
	if not google_account.enabled:
		frappe.throw(_("Google Business Account is disabled"))
	
	if not google_account.location_id:
		frappe.throw(_("Please select a location before syncing reviews. Click 'Fetch Accounts & Locations' to choose a location."))
	
	reviews = fetch_reviews(google_account)
	
	new_count = 0
	updated_count = 0
	skipped_count = 0
	
	for review_data in reviews:
		try:
			# Extract review ID from the name field (format: accounts/{accountId}/locations/{locationId}/reviews/{reviewId})
			review_name = review_data.get("name", "")
			review_id = review_name.split("/")[-1] if review_name else None
			
			if not review_id:
				skipped_count += 1
				continue
			
			# Check if review already exists
			existing = frappe.db.exists("Google Business Review", review_id)
			
			reviewer = review_data.get("reviewer", {})
			review_reply = review_data.get("reviewReply", {})
			
			review_doc_data = {
				"doctype": "Google Business Review",
				"review_id": review_id,
				"google_account": google_account.name,
				"reviewer_name": reviewer.get("displayName", "Anonymous"),
				"profile_photo_url": reviewer.get("profilePhotoUrl", ""),
				"star_rating": parse_star_rating(review_data.get("starRating", "ONE")),
				"comment": review_data.get("comment", ""),
				"review_time": review_data.get("createTime"),
				"reply_comment": review_reply.get("comment", "") if review_reply else "",
				"reply_time": review_reply.get("updateTime", "") if review_reply else None
			}
			
			if existing:
				# Update existing review
				doc = frappe.get_doc("Google Business Review", review_id)
				doc.update(review_doc_data)
				doc.save(ignore_permissions=True)
				updated_count += 1
			else:
				# Create new review
				doc = frappe.get_doc(review_doc_data)
				doc.insert(ignore_permissions=True)
				new_count += 1
		
		except Exception as e:
			frappe.log_error(
				message=f"Failed to save review {review_id}: {str(e)}",
				title="Google Business Review Save Error"
			)
			skipped_count += 1
			continue
	
	# Update last sync time
	google_account.last_sync = now_datetime()
	google_account.save(ignore_permissions=True)
	
	frappe.db.commit()
	
	summary = {
		"total_fetched": len(reviews),
		"new": new_count,
		"updated": updated_count,
		"skipped": skipped_count
	}
	
	frappe.msgprint(
		_(f"Sync completed: {new_count} new, {updated_count} updated, {skipped_count} skipped out of {len(reviews)} total reviews"),
		title=_("Google Reviews Sync Complete"),
		indicator="green"
	)
	
	return summary


@frappe.whitelist()
def sync_reviews(google_account_name: str) -> Dict:
	"""
	API endpoint to trigger review sync
	
	Args:
		google_account_name: Name of the Google Business Account
		
	Returns:
		Dict: Sync summary
	"""
	frappe.only_for("System Manager")
	return save_reviews_to_frappe(google_account_name)


def sync_all_enabled_accounts():
	"""
	Sync reviews for all enabled Google Business Accounts
	Called by scheduled job
	"""
	accounts = frappe.get_all(
		"Google Business Account",
		filters={"enabled": 1},
		pluck="name"
	)
	
	for account_name in accounts:
		try:
			frappe.enqueue(
				save_reviews_to_frappe,
				queue="long",
				timeout=600,
				google_account_name=account_name
			)
			frappe.logger().info(f"Queued review sync for {account_name}")
		except Exception as e:
			frappe.log_error(
				message=f"Failed to queue sync for {account_name}: {str(e)}",
				title="Google Business Sync Queue Error"
			)
