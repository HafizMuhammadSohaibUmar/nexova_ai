# VPS Test Deployment Checklist

This checklist installs ERPNext v15 with the `nexova_ai` custom Frappe app using official `frappe_docker` on Ubuntu 22.04 or 24.04.

This is for a VPS test or staging deployment. Review and replace every `CHANGE_ME_*`, domain, email, and password before use.

## 0. Deployment Variables

Use these values consistently through the checklist.

```bash
export SITE_NAME="erp.example.com"
export LETSENCRYPT_EMAIL="admin@example.com"
export DB_ROOT_PASSWORD="CHANGE_ME_DB_ROOT_PASSWORD"
export ADMIN_PASSWORD="CHANGE_ME_ADMIN_PASSWORD"
export CUSTOM_IMAGE="nexova-erpnext"
export CUSTOM_TAG="v15-test"
export FRAPPE_BRANCH="version-15"
export ERPNEXT_BRANCH="version-15"
export NEXOVA_AI_BRANCH="main"
```

## 1. VPS Preparation

1. Log in as a sudo-capable user.

```bash
ssh root@YOUR_VPS_IP
```

2. Update the system.

```bash
apt update
apt upgrade -y
```

3. Install base utilities.

```bash
apt install -y ca-certificates curl gnupg git ufw nano htop
```

4. Set timezone.

```bash
timedatectl set-timezone Asia/Karachi
```

5. Configure firewall for SSH, HTTP, and HTTPS.

```bash
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
ufw status verbose
```

6. Confirm DNS points to the VPS before HTTPS startup.

```bash
dig +short erp.example.com
curl -4 ifconfig.me
```

## 2. Docker Installation

1. Add Docker's official apt repository.

```bash
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" > /etc/apt/sources.list.d/docker.list
apt update
```

2. Install Docker Engine and Compose plugin.

```bash
apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

3. Enable Docker.

```bash
systemctl enable docker
systemctl start docker
```

4. Verify Docker versions.

```bash
docker --version
docker compose version
docker buildx version
```

5. Optional: allow a non-root deploy user to use Docker.

```bash
adduser deploy
usermod -aG sudo deploy
usermod -aG docker deploy
```

Log out and back in before using Docker as the `deploy` user.

## 3. frappe_docker Setup

1. Create a deployment directory.

```bash
mkdir -p /opt/frappe
cd /opt/frappe
```

2. Clone official `frappe_docker`.

```bash
git clone https://github.com/frappe/frappe_docker.git
cd frappe_docker
```

3. Check the repository.

```bash
git status
git branch --show-current
```

4. Optional: pin to a known `frappe_docker` release tag after testing.

```bash
git tag --list
```

## 4. apps.json Creation

Create `apps.json` in the `frappe_docker` root.

```bash
nano apps.json
```

Use this content:

```json
[
  {
    "url": "https://github.com/frappe/erpnext",
    "branch": "version-15"
  },
  {
    "url": "https://github.com/HafizMuhammadSohaibUmar/nexova_ai",
    "branch": "main"
  }
]
```

Validate the file.

```bash
python3 -m json.tool apps.json
```

Safety note: for private repositories, use Docker BuildKit secrets or deploy keys. Do not hardcode GitHub tokens in `apps.json`.

## 5. Custom Image Build

Build a custom ERPNext v15 image containing ERPNext and `nexova_ai`.

```bash
docker build \
  --no-cache \
  --build-arg=FRAPPE_PATH=https://github.com/frappe/frappe \
  --build-arg=FRAPPE_BRANCH=version-15 \
  --secret=id=apps_json,src=apps.json \
  --tag=nexova-erpnext:v15-test \
  --file=images/layered/Containerfile .
```

Verify the image exists.

```bash
docker image ls nexova-erpnext
```

Inspect included image metadata.

```bash
docker image inspect nexova-erpnext:v15-test
```

## 6. .env Configuration

1. Create a test environment file.

```bash
cp example.env custom.env
nano custom.env
```

2. Use this minimal test configuration.

```dotenv
ERPNEXT_VERSION=v15
CUSTOM_IMAGE=nexova-erpnext
CUSTOM_TAG=v15-test
PULL_POLICY=missing
RESTART_POLICY=unless-stopped

DB_PASSWORD=CHANGE_ME_DB_ROOT_PASSWORD
GUNICORN_THREADS=4
GUNICORN_WORKERS=2
GUNICORN_TIMEOUT=120

FRAPPE_SITE_NAME_HEADER=erp.example.com
SITES_RULE=Host(`erp.example.com`)
LETSENCRYPT_EMAIL=admin@example.com

HTTP_PUBLISH_PORT=80
HTTPS_PUBLISH_PORT=443
CLIENT_MAX_BODY_SIZE=50m
PROXY_READ_TIMEOUT=120
```

3. Lock down the file.

```bash
chmod 600 custom.env
```

4. Confirm important values.

```bash
grep -E "^(CUSTOM_IMAGE|CUSTOM_TAG|PULL_POLICY|FRAPPE_SITE_NAME_HEADER|SITES_RULE|LETSENCRYPT_EMAIL)=" custom.env
```

## 7. Docker Compose Startup

### Option A: Test Without HTTPS

Use this only if testing by IP or temporary HTTP access.

```bash
docker compose --env-file custom.env \
  -f compose.yaml \
  -f overrides/compose.mariadb.yaml \
  -f overrides/compose.redis.yaml \
  -f overrides/compose.noproxy.yaml \
  config > compose.custom.yaml
```

```bash
docker compose -p frappe -f compose.custom.yaml up -d
```

### Option B: Test With HTTPS

Use this when DNS already points to the VPS and ports 80/443 are open.

```bash
docker compose --env-file custom.env \
  -f compose.yaml \
  -f overrides/compose.mariadb.yaml \
  -f overrides/compose.redis.yaml \
  -f overrides/compose.https.yaml \
  config > compose.custom.yaml
```

```bash
docker compose -p frappe -f compose.custom.yaml up -d
```

### Startup Checks

```bash
docker compose -p frappe -f compose.custom.yaml ps
docker compose -p frappe -f compose.custom.yaml logs configurator
docker compose -p frappe -f compose.custom.yaml logs --tail=100 backend
```

Wait until `configurator` has completed successfully before creating the site.

## 8. Site Creation

Create the Frappe site.

```bash
docker compose -p frappe -f compose.custom.yaml exec backend \
  bench new-site erp.example.com \
  --mariadb-user-host-login-scope='172.%.%.%' \
  --db-root-password CHANGE_ME_DB_ROOT_PASSWORD \
  --admin-password CHANGE_ME_ADMIN_PASSWORD
```

Confirm the site exists.

```bash
docker compose -p frappe -f compose.custom.yaml exec backend \
  bench --site erp.example.com list-apps
```

## 9. ERPNext Install

Install ERPNext on the site.

```bash
docker compose -p frappe -f compose.custom.yaml exec backend \
  bench --site erp.example.com install-app erpnext
```

Run migration.

```bash
docker compose -p frappe -f compose.custom.yaml exec backend \
  bench --site erp.example.com migrate
```

Clear cache.

```bash
docker compose -p frappe -f compose.custom.yaml exec backend \
  bench --site erp.example.com clear-cache
```

## 10. nexova_ai Install

Install the custom app.

```bash
docker compose -p frappe -f compose.custom.yaml exec backend \
  bench --site erp.example.com install-app nexova_ai
```

Run migration again.

```bash
docker compose -p frappe -f compose.custom.yaml exec backend \
  bench --site erp.example.com migrate
```

Clear cache and restart containers.

```bash
docker compose -p frappe -f compose.custom.yaml exec backend \
  bench --site erp.example.com clear-cache
docker compose -p frappe -f compose.custom.yaml restart backend frontend websocket queue-short queue-long scheduler
```

## 11. Verification Commands

### Container Health

```bash
docker compose -p frappe -f compose.custom.yaml ps
docker compose -p frappe -f compose.custom.yaml logs --tail=100 backend
docker compose -p frappe -f compose.custom.yaml logs --tail=100 frontend
docker compose -p frappe -f compose.custom.yaml logs --tail=100 scheduler
```

### Site and Apps

```bash
docker compose -p frappe -f compose.custom.yaml exec backend \
  bench --site erp.example.com list-apps
```

Expected apps include:

```text
frappe
erpnext
nexova_ai
```

### Frappe Site Status

```bash
docker compose -p frappe -f compose.custom.yaml exec backend \
  bench --site erp.example.com doctor
```

### Scheduler

```bash
docker compose -p frappe -f compose.custom.yaml exec backend \
  bench --site erp.example.com scheduler status
```

Enable scheduler if required.

```bash
docker compose -p frappe -f compose.custom.yaml exec backend \
  bench --site erp.example.com enable-scheduler
```

### HTTP/HTTPS Access

For HTTPS:

```bash
curl -I https://erp.example.com
```

For no-proxy HTTP testing:

```bash
curl -I http://YOUR_VPS_IP:8080
```

### Desk Login

Open:

```text
https://erp.example.com
```

Login:

```text
Username: Administrator
Password: CHANGE_ME_ADMIN_PASSWORD
```

### Invoxia AI Page

Open Desk and search for:

```text
Nexova AI
```

Or open:

```text
https://erp.example.com/app/nexova-ai
```

### Backend Method Smoke Test

Run from the backend container:

```bash
docker compose -p frappe -f compose.custom.yaml exec backend \
  bench --site erp.example.com execute nexova_ai.api.ask_ai --kwargs "{'question':'today sales'}"
```

Expected result: a structured response with a `message` and `data`.

### Static Assets

```bash
docker compose -p frappe -f compose.custom.yaml exec backend \
  ls -la /home/frappe/frappe-bench/apps/nexova_ai
docker compose -p frappe -f compose.custom.yaml exec backend \
  ls -la /home/frappe/frappe-bench/sites/assets/nexova_ai
```

If assets are missing, rebuild assets and restart.

```bash
docker compose -p frappe -f compose.custom.yaml exec backend bench build
docker compose -p frappe -f compose.custom.yaml restart frontend backend
```

## 12. Rollback Steps

### Roll Back Only nexova_ai

Use this when ERPNext is healthy and only the custom app is failing.

```bash
docker compose -p frappe -f compose.custom.yaml exec backend \
  bench --site erp.example.com uninstall-app nexova_ai --yes
docker compose -p frappe -f compose.custom.yaml exec backend \
  bench --site erp.example.com migrate
docker compose -p frappe -f compose.custom.yaml restart backend frontend websocket queue-short queue-long scheduler
```

### Disable Access Temporarily

Stop public web access while keeping data volumes intact.

```bash
docker compose -p frappe -f compose.custom.yaml stop frontend
```

Restart access.

```bash
docker compose -p frappe -f compose.custom.yaml start frontend
```

### Roll Back to Previous Image Tag

1. Edit `custom.env`.

```bash
nano custom.env
```

2. Change image values.

```dotenv
CUSTOM_IMAGE=nexova-erpnext
CUSTOM_TAG=PREVIOUS_KNOWN_GOOD_TAG
PULL_POLICY=missing
```

3. Recreate Compose config.

```bash
docker compose --env-file custom.env \
  -f compose.yaml \
  -f overrides/compose.mariadb.yaml \
  -f overrides/compose.redis.yaml \
  -f overrides/compose.https.yaml \
  config > compose.custom.yaml
```

4. Restart stack with the previous image.

```bash
docker compose -p frappe -f compose.custom.yaml up -d
```

5. Run migration only if the rollback image and database schema are compatible.

```bash
docker compose -p frappe -f compose.custom.yaml exec backend \
  bench --site erp.example.com migrate
```

### Full Site Restore

Use only when you have a valid pre-change backup.

1. List backups.

```bash
docker compose -p frappe -f compose.custom.yaml exec backend \
  bench --site erp.example.com backup --with-files
```

2. Copy backup files off the server before destructive restore work.

```bash
docker compose -p frappe -f compose.custom.yaml exec backend \
  ls -lah /home/frappe/frappe-bench/sites/erp.example.com/private/backups
```

3. Restore using the exact backup paths.

```bash
docker compose -p frappe -f compose.custom.yaml exec backend \
  bench --site erp.example.com restore /path/to/database.sql.gz \
  --with-public-files /path/to/public-files.tar \
  --with-private-files /path/to/private-files.tar \
  --db-root-password CHANGE_ME_DB_ROOT_PASSWORD
```

4. Migrate and restart.

```bash
docker compose -p frappe -f compose.custom.yaml exec backend \
  bench --site erp.example.com migrate
docker compose -p frappe -f compose.custom.yaml restart backend frontend websocket queue-short queue-long scheduler
```

### Stop and Remove Test Stack

This removes containers but keeps named volumes unless `-v` is added.

```bash
docker compose -p frappe -f compose.custom.yaml down
```

Only for disposable test environments, remove volumes too.

```bash
docker compose -p frappe -f compose.custom.yaml down -v
```

## 13. Safety Warnings

- Do not run this directly on a production VPS without first testing on staging.
- Do not use `pwd.yml` for this custom app deployment; it is a disposable demo setup and not suitable for custom app installation.
- Do not store real passwords, API keys, or GitHub tokens in committed files.
- Do not use `--build-arg` for private `apps.json` credentials; use BuildKit secrets.
- Do not use weak `DB_PASSWORD` or `Administrator` passwords.
- Do not expose MariaDB, Redis, or internal container ports publicly.
- Do not use one Frappe site for multiple clients.
- Do not install `nexova_ai` by manually copying files into a running container.
- Do not delete Docker volumes during rollback unless the environment is disposable and backups are verified.
- Do not enable AI provider keys or client data integrations until HTTPS, backups, and tenant isolation are verified.
- Do not suspend a client by deleting the site or database; use a reversible subscription state in the app when implemented.
- Always take a database and files backup before app upgrade, image change, migration, or rollback.
