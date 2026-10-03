# Deploying Janeway on Coolify behind a Cloudflare Tunnel

`compose.yaml` (repo root) builds `dockerfiles/Dockerfile.coolify` and runs
Janeway under gunicorn on `$PORT` with a Postgres 15 sidecar. The entrypoint
runs migrations, first-boot install, `collectstatic`, then starts gunicorn.
Static and media files are served by WhiteNoise, so no nginx is required.

## Coolify setup
1. New Resource -> Docker Compose -> this repo, compose file `/compose.yaml`.
2. Paste the variables from `etc/coolify.env.example` into Environment Variables.
   `PORT`, `JANEWAY_SECRET_KEY` and `DB_PASSWORD` are required.
3. Deploy.

## Cloudflare Tunnel (PORT pattern, same as the other Coolify apps)

```
Browser -> Cloudflare -> cloudflared (on the Docker host) -> 127.0.0.1:PORT -> gunicorn in container (0.0.0.0:PORT)
```

1. Coolify -> Environment Variables: `PORT=<unique port>` (e.g. 9205; gentle-truths
   uses 9203, night-shift 9204). Compose fails the deploy if `PORT` is unset.
2. Coolify **Domains: leave empty**. A domain makes Traefik intervene and forward
   to port 80 -> 502.
3. Cloudflare Zero Trust -> Tunnels -> Public Hostname: service `HTTP`,
   `127.0.0.1:<PORT>`.
4. Verify on the host:
   `docker ps --format 'table {{.Names}}\t{{.Ports}}' | grep <PORT>` (shows `127.0.0.1:<PORT>->`)
   and `curl -I http://127.0.0.1:<PORT>`.

`compose.yaml` publishes `127.0.0.1:${PORT}:${PORT}` (loopback only, so the port
cannot bypass Cloudflare) and gunicorn binds `0.0.0.0:$PORT`.
`cloudflared` must run on the host (or host network); if it is a container, use
`host.docker.internal` or share a Docker network and target `http://janeway:<PORT>`.

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
