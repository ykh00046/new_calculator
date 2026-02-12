# Deployment & Security Notes

This document outlines recommended settings when deploying the Production Analysis Dashboard.

## Streamlit Server Options

- Port: `--server.port 8504` (customize as needed)
- Headless: `--server.headless true` (recommended for servers)
- Base URL path (behind reverse proxy): `--server.baseUrlPath /dashboard`

## .streamlit/config.toml

Example (already included):

```
[theme]
base = "dark"
primaryColor = "#4A9EFF"
backgroundColor = "#0E1117"
secondaryBackgroundColor = "#1E2530"
textColor = "#FAFAFA"
font = "sans serif"

[server]
headless = true
enableCORS = false        # keep off behind trusted reverse proxy
enableXsrfProtection = false  # consider enabling for external exposure
```

For external/public exposure, prefer enabling `enableCORS` and `enableXsrfProtection`, or place Streamlit behind a reverse proxy (Nginx) with proper access control.

## Reverse Proxy (Nginx) Example

```
server {
    listen 80;
    server_name example.com;

    location /dashboard/ {
        proxy_pass http://127.0.0.1:8504/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Database Path

- The app reads the DB path from `config/db_path.conf` (user-managed), or you can upload the DB file through the UI.
- Ensure proper file permissions for the app process.

## Environment

- Python: 3.10+
- Packages pinned in `requirements.txt` to reduce drift.

