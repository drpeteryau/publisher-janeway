# Deploying Janeway on Coolify behind a Cloudflare Tunnel

`compose.yaml` (repo root) builds `dockerfiles/Dockerfile.coolify` and runs
Janeway under gunicorn on port 8000 with a Postgres 15 sidecar. The entrypoint
runs migrations, first-boot install, `collectstatic`, then starts gunicorn.
Static and media files are served by WhiteNoise, so no nginx is required.

## Coolify setup
1. New Resource -> Docker Compose -> this repo, compose file `/compose.yaml`.
2. Paste the variables from `etc/coolify.env.example` into Environment Variables.
   `JANEWAY_SECRET_KEY` and `DB_PASSWORD` are required.
3. Deploy.

## Cloudflare Tunnel
Point the tunnel's Public Hostname (e.g. `journals.example.org`) at the container:

- **cloudflared as a Coolify resource on the same network**: service URL
  `http://janeway:8000` (use the compose service name; if Coolify suffixes names,
  use the container name shown in the resource).
- **Via the Coolify proxy**: assign the domain to the `janeway` service in Coolify
  (`https://journals.example.org:8000` sets the container port) and point the
  tunnel at `http://<server-ip>:80`, with "HTTP Host Header" set to the hostname.

## Variables that make the tunnel work
| Variable | Why |
|---|---|
| `JANEWAY_ALLOWED_HOSTS` | Public hostname(s); Django rejects other Host headers. |
| `JANEWAY_CSRF_TRUSTED_ORIGINS` | `https://` origins; needed for login/forms over HTTPS. Defaults to the allowed hosts. |
| `JANEWAY_PRESS_DOMAIN` / `JANEWAY_JOURNAL_DOMAIN` | Janeway selects the site by Host header; must match the public hostname (or use path mode with the press domain). |
| `JANEWAY_SECURE_COOKIES` | Keep `true`; TLS ends at Cloudflare. The app trusts `X-Forwarded-Proto/Host`. |

If the press domain was set wrongly on first boot, fix it in Django admin
(Press / Journal domain) or run `python manage.py alter_domains`.

## Notes
- Volumes: `janeway-db`, `janeway-media`, `janeway-files`, `janeway-logs`.
- Set `JANEWAY_AUTO_INSTALL=false` to skip first-boot install on an existing DB.
- Set `JANEWAY_DEBUG=true` temporarily to diagnose 400/500 errors.
