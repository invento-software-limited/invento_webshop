# Google Business Profile API - 403 Forbidden Error Fix

## The Issue
You're getting a `403 Forbidden` error when trying to fetch accounts from Google Business Profile API.

## Root Cause
The Google Business Profile API is not enabled in your Google Cloud project.

## Solution Steps

### 1. Enable Required APIs

Go to your Google Cloud Console and enable these APIs:

1. **Google Business Profile API**
   - Direct link: https://console.cloud.google.com/apis/library/mybusinessaccountmanagement.googleapis.com
   - Click "Enable"

2. **Google My Business API** (if available)
   - Direct link: https://console.cloud.google.com/apis/library/mybusiness.googleapis.com
   - Click "Enable"

3. **Business Information API**
   - Search for "Business Information" in API Library
   - Enable if found

### 2. Verify Your Project

Make sure you're enabling these APIs in the **same Google Cloud project** where you created your OAuth credentials.

### 3. Check Business Profile Requirements

Your Google Business Profile must meet these requirements:
- ✅ Verified
- ✅ Active for at least 60 days
- ✅ You have owner or manager access

### 4. Re-authorize

After enabling the APIs:
1. Go back to your Google Business Account in Frappe
2. Click "Authorize with Google" again
3. Make sure you're signing in with the Google account that owns/manages the business
4. Try "Fetch Accounts & Locations" again

## Still Getting 403?

If you still get 403 after enabling the APIs:

1. **Wait 5-10 minutes** - API enablement can take a few minutes to propagate
2. **Check the correct account** - Make sure you're authorizing with the Google account that actually owns the Business Profile
3. **Verify Business Profile** - Go to https://business.google.com/ and confirm your profile is verified
4. **Check OAuth consent screen** - Make sure it's configured for the correct user type (Internal vs External)

## Quick Checklist

- [ ] Google Business Profile API enabled in Cloud Console
- [ ] Google My Business API enabled (if available)
- [ ] Using the correct Google Cloud project
- [ ] Business Profile is verified
- [ ] Authorizing with the correct Google account (owner/manager)
- [ ] Waited 5-10 minutes after enabling APIs
