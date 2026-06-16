# Microsoft 365 Sign-In Setup

This is a **one-time, 5-minute setup** done once by you (the developer).
Your PM colleagues never need to touch this — they just click **M365 Sign In**
and a Microsoft login page opens in their browser, exactly like Gmail.

> **No Azure subscription required.**
> App Registration is a free identity feature included with every Microsoft account.

---

## Step 1 — Go to the Azure Portal (free)

Open https://portal.azure.com and sign in with **any** Microsoft account
(personal @outlook.com / @hotmail.com, or a work/school account).

---

## Step 2 — Register the app (2 minutes)

1. Search for **"App registrations"** in the top search bar → click it
2. Click **+ New registration**
3. Fill in:
   - **Name:** `PM Toolkit` (anything you like)
   - **Supported account types:** select **"Accounts in any organizational directory
     and personal Microsoft accounts"**
   - **Redirect URI:** choose **"Mobile and desktop applications"** → enter `http://localhost`
4. Click **Register**

---

## Step 3 — Copy the Client ID

On the app's Overview page you will see:

```
Application (client) ID:  xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

Copy that UUID.

---

## Step 4 — Create ms_credentials.json

In the `tools/survey/` folder, copy `ms_credentials.example.json` to
`ms_credentials.json` and paste your Client ID:

```json
{
  "client_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
}
```

Commit `ms_credentials.json` the same way you committed `credentials.json`
for Gmail — or share it with colleagues directly.

---

## Step 5 — First sign-in

Run the app, click **M365 Sign In**. A real Microsoft login page opens in
the browser. Sign in with your work or personal Microsoft account.

A `ms_token_cache.json` file is created in `tools/survey/`.
Every future sign-in is silent — the browser never opens again.

---

## That's it

Each PM colleague repeats Steps 4–5 on their own machine using the same
`ms_credentials.json` file you created. No Azure subscription, no billing,
no admin privileges required.
