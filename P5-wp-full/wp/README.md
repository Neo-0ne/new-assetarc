
# WordPress Frontend (Theme + SSO + Booking Gate)

## Install
1. Copy `wp/theme/assetarc` to `wp-content/themes/assetarc` and activate.
2. Copy plugin folders to `wp-content/plugins/` and activate both:
   - AssetArc SSO (Email OTP)
   - AssetArc Booking Gate
3. Edit plugin constants if needed:
   - `ASSETARC_AUTH_BASE` in `assetarc-sso.php`
   - `ASSETARC_GATEWAY_BASE` and `ASSETARC_CALENDLY_URL` in `assetarc-booking-gate.php`

## Usage
- Place `[assetarc_login]` and/or `[assetarc_booking_gate]` on a page.
- The booking gate calls the **Gateway** → **Payments** to create a NOWPayments invoice, then reveals Calendly after success.
