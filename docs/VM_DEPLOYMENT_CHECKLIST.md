# VM Deployment Checklist

Use this checklist for the Azure test VM. Do not hotfix files inside running containers except for emergency diagnosis.

## Source Control

1. Commit local changes.
2. Push to GitHub `main`.
3. Confirm the latest commit is visible on GitHub.

## Rebuild Image

Run from the VM:

```bash
cd ~/invoxia/frappe_docker
docker build --no-cache --secret id=apps_json,src=apps.json --build-arg=FRAPPE_PATH=https://github.com/frappe/frappe --build-arg=FRAPPE_BRANCH=version-15 --build-arg=ERPNEXT_REPO=https://github.com/frappe/erpnext --build-arg=ERPNEXT_BRANCH=version-15 --tag=invoxia-erpnext:version-15 --file=images/custom/Containerfile .
```

## Recreate Stack

```bash
docker compose -p invoxia -f compose.yaml -f overrides/compose.mariadb.yaml -f overrides/compose.redis.yaml -f overrides/compose.noproxy.yaml up -d --force-recreate
```

Verify:

```bash
docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Ports}}\t{{.Status}}"
docker exec -it invoxia-backend-1 bash -lc 'getent hosts db && getent hosts redis-cache && getent hosts redis-queue'
```

## Site Migration

```bash
docker exec -it invoxia-backend-1 bench --site invoxia.local migrate
docker exec -it invoxia-backend-1 bench --site invoxia.local clear-cache
```

If MariaDB rejects the site user, repair the site database user using the password in `sites/invoxia.local/site_config.json`, then rerun migrate.

## Verification

```bash
docker exec -it invoxia-backend-1 bench --site invoxia.local console
```

Then:

```python
frappe.db.exists("Page", "nexova-ai-assistant")
frappe.db.exists("Workspace", "Nexova AI")
```

Browser checks:

- Open `/app/nexova-ai`.
- Click `Open Nexova AI`.
- Confirm `/app/nexova-ai-assistant` renders the assistant.
- DevTools Console should not show Nexova AI JavaScript errors.

## Security

- Rotate exposed DB passwords before production or shared demos.
- Do not paste secrets into support logs.
- Do not use VM hotfixes as a deployment method.
