# SSL Certificates Directory

This directory holds the SSL/TLS certificate and private key mounted into the Nginx container at `/etc/nginx/certs/`.

Files expected by Nginx:
- `cert.pem` - Certificate (Cloudflare Origin CA Certificate or Let's Encrypt `fullchain.pem`)
- `key.pem` - Private Key (Cloudflare Origin Private Key or Let's Encrypt `privkey.pem`)

> A default self-signed placeholder certificate has been generated so Nginx can start immediately without errors.
> 
> **For Cloudflare Full (Strict) Production:**
> 1. Go to **Cloudflare Dashboard** -> **SSL/TLS** -> **Origin Server** -> **Create Certificate**.
> 2. Copy the **Origin Certificate** contents into `cert.pem`.
> 3. Copy the **Private Key** contents into `key.pem`.
> 4. Reload Nginx: `docker compose exec nginx nginx -s reload`.

