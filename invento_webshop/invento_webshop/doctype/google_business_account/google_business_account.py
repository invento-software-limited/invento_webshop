# Copyright (c) 2026, Invento and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import get_url
import urllib.parse


class GoogleBusinessAccount(Document):
	"""Google Business Account DocType for storing OAuth credentials"""
	
	def validate(self):
		"""Validate the account details"""
		if not self.client_id or not self.client_secret:
			frappe.throw("Client ID and Client Secret are required")
	
	def get_authorization_url(self):
		"""Generate OAuth authorization URL"""
		redirect_uri = get_url("/api/method/invento_webshop.google_business.oauth.callback")
		
		params = {
			"client_id": self.client_id,
			"redirect_uri": redirect_uri,
			"response_type": "code",
			"scope": "https://www.googleapis.com/auth/business.manage",
			"access_type": "offline",
			"prompt": "consent",
			"state": self.name  # Pass document name as state
		}
		
		auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(params)
		return auth_url
