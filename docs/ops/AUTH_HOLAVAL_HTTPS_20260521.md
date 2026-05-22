# AUTH_HOLAVAL_HTTPS_20260521

Status:
HTTPS enabled for auth.holaval.com.

Domain:
auth.holaval.com

DNS:
auth.holaval.com A record points to Val0 public IP:
167.172.239.59

Reverse proxy:
Nginx installed and running.

Public endpoints:
- https://auth.holaval.com/health
- https://auth.holaval.com/oauth2callback

Backend sidecar:
- val0-gcal-oauth.service
- binds local-only on 127.0.0.1:8080
- Nginx proxies public HTTPS traffic to the local sidecar

Certificate:
Issued by Let's Encrypt using Snap Certbot.

Certificate paths:
- /etc/letsencrypt/live/auth.holaval.com/fullchain.pem
- /etc/letsencrypt/live/auth.holaval.com/privkey.pem

Expiry:
2026-08-20

Verification:
- Snap Certbot 5.6.0 succeeded
- HTTPS /health returned OK val0-gcal-oauth preview-only
- HTTPS /oauth2callback rejected malformed state safely
- SECRET_ECHO_FAIL=NO
- NGINX_SECRET_LOG_LEAK=NO
- SIDECAR_SECRET_LOG_LEAK=NO
- port 443 is listening through Nginx
- sidecar remains local-only on 127.0.0.1:8080

Important:
APT Certbot is broken due to Python/OpenSSL package conflict.
Use /snap/bin/certbot for cert operations.

Next required action:
Update Val0 Google OAuth redirect URI from old omfgeeks HTTP callback to:

https://auth.holaval.com/oauth2callback

Then update Google Cloud OAuth authorized redirect URI to match exactly before live token exchange.
