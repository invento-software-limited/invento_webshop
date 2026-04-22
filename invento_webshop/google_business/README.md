# Google Business Reviews Integration - Usage Guide

## Overview
This integration allows you to automatically fetch and store Google Business Profile reviews in your Frappe site with **automatic OAuth authorization** - no manual token generation needed!

## Setup Instructions

### 1. Get OAuth Credentials from Google

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. **IMPORTANT: Enable the following APIs:**
   - [Google Business Profile API](https://console.cloud.google.com/apis/library/mybusinessaccountmanagement.googleapis.com)
   - [Google My Business API](https://console.cloud.google.com/apis/library/mybusiness.googleapis.com) (if available)
   - Search for "Business Profile" in the API Library and enable all related APIs
4. Go to **Credentials** → **Create Credentials** → **OAuth 2.0 Client ID**
5. Configure the OAuth consent screen
6. Add authorized redirect URI: `https://your-site.com/api/method/invento_webshop.google_business.oauth.callback`
   - Replace `your-site.com` with your actual Frappe site URL
7. Create credentials and note down:
   - **Client ID**
   - **Client Secret**

**Prerequisites:**
- Your Google Business Profile must be verified
- Profile should be active for at least 60 days
- You must be the owner or manager of the business profile

### 2. Create Google Business Account in Frappe

1. Navigate to **Google Business Account** DocType
2. Click **New**
3. Fill in the details:
   - **Account Name**: A friendly name (e.g., "My Restaurant - Main Location")
   - **Client ID**: Your OAuth Client ID from step 1
   - **Client Secret**: Your OAuth Client Secret from step 1
4. Save the document

### 3. Authorize with Google (Automatic)

1. Click the **"Authorize with Google"** button
2. A popup window will open with Google's OAuth consent screen
3. Sign in with the Google account that manages your business
4. Grant the requested permissions
5. The popup will show a success message
6. Close the popup and refresh the Frappe page
7. The **Authorization Status** will now show "Authorized"

### 4. Enter Location ID

After authorization, the Account ID will be automatically populated. You need to manually enter the Location ID:

1. Go to [Google Business Profile](https://business.google.com/)
2. Select your business location
3. The Location ID can be found in the URL or you can use the API to list locations
4. Enter the Location ID in the **Location ID** field
5. Save the document

### 5. Start Syncing Reviews

1. Check the **Enabled** checkbox
2. Click the **"Sync Reviews"** button
3. Reviews will be fetched and saved
4. View reviews in **Google Business Review** DocType

## Usage

### Manual Sync

1. Open a **Google Business Account** document
2. Click the **Sync Reviews** button
3. Wait for the sync to complete
4. Check **Google Business Review** DocType to see fetched reviews

### Automatic Sync

Reviews are automatically synced **daily** for all enabled accounts via a scheduled job.

### View Reviews

1. Navigate to **Google Business Review** DocType
2. Filter by **Google Account** to see reviews for a specific location
3. Reviews include:
   - Reviewer name and photo
   - Star rating (1-5)
   - Review comment
   - Review timestamp
   - Business reply (if any)

## API Endpoints

### Sync Reviews Programmatically

```python
import frappe

# Sync reviews for a specific account
frappe.call(
    method='invento_webshop.google_business.google_reviews.sync_reviews',
    args={'google_account_name': 'My Restaurant - Main Location'}
)
```

### Background Job

```python
from invento_webshop.google_business.google_reviews import save_reviews_to_frappe

# Queue sync job
frappe.enqueue(
    save_reviews_to_frappe,
    queue='long',
    timeout=600,
    google_account_name='My Restaurant - Main Location'
)
```

## Features

✅ **Automatic OAuth Flow**: No manual token generation - authorize with one click!  
✅ **Auto Account Discovery**: Automatically fetches and lists all your accounts and locations  
✅ **Smart Button Workflow**: Shows only relevant buttons based on authorization state  
✅ **OAuth Token Auto-Refresh**: Automatically refreshes access tokens using refresh token  
✅ **Pagination Support**: Fetches all reviews with automatic pagination  
✅ **Duplicate Handling**: Updates existing reviews instead of creating duplicates  
✅ **Error Handling**: Comprehensive error logging and user-friendly messages  
✅ **Background Jobs**: Sync runs in background to avoid blocking  
✅ **Scheduled Sync**: Daily automatic sync for all enabled accounts  
✅ **Real-time Progress**: Shows progress during sync  

## Troubleshooting

### "403 Forbidden" when fetching accounts
This is the most common error. It means:
1. **Google Business Profile API is not enabled** in your Google Cloud project
   - Go to [API Library](https://console.cloud.google.com/apis/library)
   - Search for "Google Business Profile API" and enable it
   - Also enable "Google My Business API" if available
2. **Wrong Google Account**: You're authorizing with a Google account that doesn't own/manage any Business Profiles
   - Make sure to authorize with the correct Google account
3. **Business Profile not verified**: Your profile must be verified and active for 60+ days
4. **Missing permissions**: The authenticated user needs owner or manager access to the Business Profile

### "Failed to refresh OAuth token"
- Verify your Client ID, Client Secret, and Refresh Token are correct
- Ensure the refresh token hasn't expired (they can expire if not used for 6 months)
- Check that the Google Business Profile API is enabled in your Google Cloud project

### "Failed to fetch reviews"
- Verify your Account ID and Location ID are correct
- Ensure your OAuth credentials have the correct scope
- Check the Error Log for detailed error messages

### No reviews appearing
- Ensure the location actually has reviews on Google
- Check that the account is enabled
- Verify the sync completed without errors

## Notes

- Reviews are identified by their unique `review_id` to prevent duplicates
- The `last_sync` field shows when reviews were last fetched
- Only System Managers can trigger manual syncs
- Star ratings are stored as enums: ONE, TWO, THREE, FOUR, FIVE
