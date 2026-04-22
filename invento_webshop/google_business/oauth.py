# Copyright (c) 2026, Invento and contributors
# For license information, please see license.txt

"""
Google OAuth Flow Handler
Handles OAuth authorization and token exchange
"""

import requests
import frappe
from frappe import _
from frappe.utils import get_url
import urllib.parse


@frappe.whitelist()
def get_authorization_url(account_name):
	"""
	Generate OAuth authorization URL for a Google Business Account
	
	Args:
		account_name: Name of the Google Business Account document
		
	Returns:
		str: OAuth authorization URL
	"""
	account = frappe.get_doc("Google Business Account", account_name)
	return account.get_authorization_url()


@frappe.whitelist(allow_guest=True)
def callback():
	"""
	OAuth callback endpoint
	Exchanges authorization code for refresh token
	"""
	# Get parameters from callback
	code = frappe.form_dict.get("code")
	state = frappe.form_dict.get("state")  # This is the account name
	error = frappe.form_dict.get("error")
	
	if error:
		frappe.respond_as_web_page(
			_("Authorization Failed"),
			_("Google authorization was denied or failed: {0}").format(error),
			indicator_color="red"
		)
		return
	
	if not code or not state:
		frappe.respond_as_web_page(
			_("Authorization Failed"),
			_("Missing authorization code or state parameter"),
			indicator_color="red"
		)
		return
	
	try:
		# Get the account document
		account_name = state
		account = frappe.get_doc("Google Business Account", account_name)
		
		# Exchange code for tokens
		redirect_uri = get_url("/api/method/invento_webshop.google_business.oauth.callback")
		
		token_data = {
			"code": code,
			"client_id": account.client_id,
			"client_secret": account.get_password("client_secret"),
			"redirect_uri": redirect_uri,
			"grant_type": "authorization_code"
		}
		
		response = requests.post(
			"https://oauth2.googleapis.com/token",
			data=token_data,
			timeout=30
		)
		response.raise_for_status()
		
		tokens = response.json()
		refresh_token = tokens.get("refresh_token")
		
		if not refresh_token:
			frappe.respond_as_web_page(
				_("Authorization Failed"),
				_("No refresh token received. Please ensure you selected 'offline access' and gave consent."),
				indicator_color="red"
			)
			return
		
		# Update account with refresh token
		account.refresh_token = refresh_token
		account.authorization_status = "Authorized"
		
		# Automatically fetch and set the first account ID
		try:
			access_token = tokens.get("access_token")
			if access_token:
				headers = {
					"Authorization": f"Bearer {access_token}",
					"Content-Type": "application/json"
				}
				
				# Fetch accounts
				accounts_response = requests.get(
					"https://mybusinessaccountmanagement.googleapis.com/v1/accounts",
					headers=headers,
					timeout=30
				)
				
				if accounts_response.status_code == 200:
					accounts_data = accounts_response.json()
					accounts_list = accounts_data.get("accounts", [])
					
					if accounts_list:
						# Set the first account ID automatically
						first_account = accounts_list[0]
						account_id = first_account.get("name", "").split("/")[-1]
						account.account_id = account_id
		except Exception as e:
			# Log error but don't fail authorization
			frappe.log_error(
				message=f"Failed to auto-fetch account ID: {str(e)}",
				title="Google OAuth Account Fetch Warning"
			)
		
		account.save(ignore_permissions=True)
		frappe.db.commit()
		
		# Success page
		frappe.respond_as_web_page(
			_("Authorization Successful"),
			_("Your Google Business Account has been authorized successfully. You can now close this window and sync reviews."),
			indicator_color="green"
		)
		
	except Exception as e:
		frappe.log_error(
			message=f"OAuth callback error: {str(e)}",
			title="Google OAuth Error"
		)
		frappe.respond_as_web_page(
			_("Authorization Failed"),
			_("An error occurred during authorization: {0}").format(str(e)),
			indicator_color="red"
		)


@frappe.whitelist()
def fetch_accounts_and_locations(account_name):
	"""
	Fetch available Google Business accounts and locations
	
	Args:
		account_name: Name of the Google Business Account document
		
	Returns:
		dict: Available accounts and locations
	"""
	from invento_webshop.google_business.google_reviews import get_access_token
	
	account = frappe.get_doc("Google Business Account", account_name)
	
	if not account.refresh_token:
		frappe.throw(_("Please authorize with Google first"))
	
	try:
		access_token = get_access_token(account)
		headers = {
			"Authorization": f"Bearer {access_token}",
			"Content-Type": "application/json"
		}
		
		# Fetch accounts
		accounts_response = requests.get(
			"https://mybusinessaccountmanagement.googleapis.com/v1/accounts",
			headers=headers,
			timeout=30
		)
		accounts_response.raise_for_status()
		accounts_data = accounts_response.json()
		
		accounts_list = []
		for acc in accounts_data.get("accounts", []):
			account_id = acc.get("name", "").split("/")[-1]
			account_name_display = acc.get("accountName", account_id)
			
			# Fetch locations for this account
			locations_response = requests.get(
				f"https://mybusinessbusinessinformation.googleapis.com/v1/{acc.get('name')}/locations",
				headers=headers,
				timeout=30
			)
			
			locations = []
			if locations_response.status_code == 200:
				locations_data = locations_response.json()
				for loc in locations_data.get("locations", []):
					location_id = loc.get("name", "").split("/")[-1]
					location_name = loc.get("title", location_id)
					locations.append({
						"id": location_id,
						"name": location_name
					})
			
			accounts_list.append({
				"id": account_id,
				"name": account_name_display,
				"locations": locations
			})
		
		return accounts_list
		
	except requests.exceptions.HTTPError as e:
		error_msg = str(e)
		
		# Provide specific guidance for 403 errors
		if "403" in error_msg or "Forbidden" in error_msg:
			frappe.log_error(
				message=f"Failed to fetch accounts/locations (403 Forbidden): {error_msg}",
				title="Google Business API 403 Error"
			)
			frappe.throw(_("""
				<b>403 Forbidden Error - API Access Issue</b><br><br>
				This error usually means:<br>
				1. <b>Google Business Profile API is not enabled</b> in your Google Cloud project<br>
				2. The authenticated account doesn't have access to any Google Business Profiles<br>
				3. Your Business Profile needs to be verified and active for at least 60 days<br><br>
				<b>To fix this:</b><br>
				• Go to <a href="https://console.cloud.google.com/apis/library/mybusinessaccountmanagement.googleapis.com" target="_blank">Google Cloud Console</a><br>
				• Enable "Google Business Profile API"<br>
				• Also enable "Google My Business API" if available<br>
				• Ensure your Google Business Profile is verified<br>
				• Make sure you're authorizing with the Google account that owns/manages the business
			"""))
		
		frappe.log_error(
			message=f"Failed to fetch accounts/locations: {error_msg}",
			title="Google Business API Error"
		)
		frappe.throw(_(f"Failed to fetch accounts and locations from Google: {error_msg}"))
	except Exception as e:
		frappe.log_error(
			message=f"Failed to fetch accounts/locations: {str(e)}",
			title="Google Business API Error"
		)
		frappe.throw(_("Failed to fetch accounts and locations from Google"))


@frappe.whitelist()
def get_google_business_locations(account_name):
	"""
	Fetch locations for a specific Google Business Account
	
	Args:
		account_name: Name of the Google Business Account document
		
	Returns:
		list: List of location objects
	"""
	from invento_webshop.google_business.google_reviews import get_access_token
	
	account = frappe.get_doc("Google Business Account", account_name)
	
	if not account.refresh_token:
		frappe.throw(_("Please authorize with Google first"))
	
	try:
		access_token = get_access_token(account)
		headers = {
			"Authorization": f"Bearer {access_token}",
			"Content-Type": "application/json"
		}
		
		account_id = account.account_id
		
		# If account_id is missing, try to fetch it first
		if not account_id:
			accounts_response = requests.get(
				"https://mybusinessaccountmanagement.googleapis.com/v1/accounts",
				headers=headers,
				timeout=30
			)
			accounts_response.raise_for_status()
			accounts_data = accounts_response.json()
			accounts_list = accounts_data.get("accounts", [])
			
			if not accounts_list:
				frappe.throw(_("No Google Business Accounts found for this authorization"))
			
			# Use the first account
			first_account = accounts_list[0]
			account_id = first_account.get("name", "").split("/")[-1]
		
		# Fetch locations using the more standard businessinformation endpoint
		# Endpoint: https://mybusinessbusinessinformation.googleapis.com/v1/accounts/{accountId}/locations
		url = f"https://mybusinessbusinessinformation.googleapis.com/v1/accounts/{account_id}/locations"
		
		response = requests.get(url, headers=headers, timeout=30)
		response.raise_for_status()
		locations_data = response.json()
		
		return locations_data.get("locations", [])
		
	except requests.exceptions.HTTPError as e:
		error_msg = str(e)
		
		# Provide specific guidance for 403 errors (Account Management vs Business Information)
		if "403" in error_msg or "Forbidden" in error_msg:
			frappe.log_error(
				message=f"Failed to fetch locations (403 Forbidden): {error_msg}",
				title="Google Business API 403 Error"
			)
			frappe.throw(_("""
				<b>403 Forbidden Error - API Access Issue</b><br><br>
				This error usually means:<br>
				1. <b>Google Business Profile API</b> or <b>My Business Business Information API</b> is not enabled in your Google Cloud project<br>
				2. The authenticated account doesn't have access to locations in this Google Business Account<br>
				3. Your Business Profile needs to be verified<br><br>
				<b>To fix this:</b><br>
				• Go to <a href="https://console.cloud.google.com/apis/library/mybusinessbusinessinformation.googleapis.com" target="_blank">Google Cloud Console</a><br>
				• Enable <b>"My Business Business Information API"</b><br>
				• Also enable <b>"Google Business Profile API"</b><br>
				• Ensure your Google Business Profile is verified<br>
				• Make sure you're authorizing with the correct Google account
			"""))
		
		frappe.throw(_(f"Failed to fetch locations from Google: {error_msg}"))
	except Exception as e:
		frappe.log_error(
			message=f"Failed to fetch Google locations: {str(e)}",
			title="Google Business API Error"
		)
		frappe.throw(_("Failed to fetch locations from Google Business API. Please check your API configuration or verify your business profile."))
