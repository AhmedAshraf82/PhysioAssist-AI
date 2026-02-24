# Add a New WhatsApp Phone Number

## 🧠 The Architecture (Never Forget This)

In Meta WhatsApp Cloud API:

- App → owns webhook
- WABA (WhatsApp Business Account) → owns phone numbers
- System User → owns permissions
- Token → temporary key derived from System User

**WABA must subscribe to App** ← critical step you missed

When adding a new phone number, 99% of failures happen at step 5.

---

## ✅ FULL PROCESS — ADDING A NEW PHONE NUMBER

### 🔹 STEP 1 — Add the Phone Number to the Correct WABA

In Business Manager:

Accounts → WhatsApp Accounts → Select WABA → Add Phone Number

Verify the number via SMS or call.

After verification, copy:

- Phone Number ID (important)
- WABA ID (important)

### 🔹 STEP 2 — Confirm Token Can See the Phone

Test immediately:

```http
GET https://graph.facebook.com/v19.0/PHONE_NUMBER_ID
Authorization: Bearer YOUR_SYSTEM_USER_TOKEN
```

Expected:

```json
{
  "id": "...",
  "display_phone_number": "...",
  "verified_name": "..."
}
```

If this fails → permission issue.

Do NOT continue until this works.

### 🔹 STEP 3 — Subscribe the WABA to Your App (CRITICAL)

This is the step people forget.

```http
POST https://graph.facebook.com/v19.0/WABA_ID/subscribed_apps
Authorization: Bearer YOUR_SYSTEM_USER_TOKEN
```

Expected:

```json
{
  "success": true
}
```

This tells Meta:

“Forward inbound messages from this WABA to my app.”

### 🔹 STEP 4 — Verify Subscription

```http
GET https://graph.facebook.com/v19.0/WABA_ID/subscribed_apps
Authorization: Bearer YOUR_SYSTEM_USER_TOKEN
```

You should see your app listed:

```json
{
  "data": [
    {
      "whatsapp_business_api_data": {
        "id": "YOUR_APP_ID"
      }
    }
  ]
}
```

If you don’t see it → inbound messages will never hit your webhook.

### 🔹 STEP 5 — Confirm Webhook Is Configured

Go to:

https://developers.facebook.com/apps/YOUR_APP_ID/webhooks/

Under:

WhatsApp Business Account

Make sure these are subscribed:

- ✅ messages
- ✅ message_status
- ✅ message_template_status_update

### 🔹 STEP 6 — Test Outbound Send

```http
POST https://graph.facebook.com/v19.0/PHONE_NUMBER_ID/messages
Authorization: Bearer YOUR_SYSTEM_USER_TOKEN
Content-Type: application/json
```

Body:

```json
{
  "messaging_product": "whatsapp",
  "to": "201XXXXXXXXX",
  "type": "text",
  "text": {
    "body": "test"
  }
}
```

If this works → sending is confirmed.

### 🔹 STEP 7 — Test Inbound

From your personal WhatsApp:

Send “hi” to the business number.

Then check your server logs.

You should receive:

```json
{
  "object": "whatsapp_business_account"
}
```

If not → 99% of the time you forgot Step 3.

---

## 🚨 MOST COMMON MISTAKES

- Multiple WABAs under same Business
- Subscribing wrong WABA
- Token from wrong app
- System user not assigned to WABA
- Forgetting to re-generate token after permission changes

---

## 🧩 Quick Debug Commands Cheat Sheet

- Check Phone Access  
  `GET /PHONE_NUMBER_ID`
- Check WABA Access  
  `GET /WABA_ID`
- Subscribe WABA  
  `POST /WABA_ID/subscribed_apps`
- Verify Subscription  
  `GET /WABA_ID/subscribed_apps`

---

## 🏆 The Golden Rule

Whenever inbound messages don’t arrive:

First thing you check is:

`GET /WABA_ID/subscribed_apps`

If your app isn’t there → that’s the problem.

You’ve now gone from “debugging chaos” to actually understanding the system architecture.

If you want, I can also give you a production-safe checklist for scaling to multiple numbers cleanly without permission nightmares.
