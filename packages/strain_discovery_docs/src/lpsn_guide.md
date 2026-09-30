# LPSN API Registration Guide

This guide explains how to register for an LPSN API account.

## Registration

To use the LPSN API, you must register for an account.

### Step 1: Navigate to the LPSN API Login Page

Visit: [https://api.lpsn.dsmz.de/login](https://api.lpsn.dsmz.de/login)

You will be redirected to the Keycloak authentication service at DSMZ.

### Step 2: Click Register

On the Keycloak login page, click **Register**. This will take you to the Keycloak registration page where you can create your account.

### Step 3: Fill in Registration Details

On the Keycloak registration page, provide:

- **First name**
- **Last name**
- **Institution**
- **Country** (dropdown selection)
- **Email**
- **Password**

### Step 4: Complete Registration

Click **Register** to finalize your account creation. Once registered, you can log in with your credentials.

## API Access

After registration, your credentials can be used with the LPSN API endpoints:

- `https://api.lpsn.dsmz.de/fetch/{lpsn_id}`
- `https://api.lpsn.dsmz.de/advanced_search`
- `https://api.lpsn.dsmz.de/flexible_search`

Authentication is handled via HTTP Basic Authentication using your username and password.

## Notes

- Registration is free
- Your account grants access to all LPSN API endpoints
