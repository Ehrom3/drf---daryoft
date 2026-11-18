#!/usr/bin/env bash
set -euo pipefail
cd /opt/daryoft
ip=${1:-}
if ! python3 -c 'import ipaddress,sys; ipaddress.IPv4Address(sys.argv[1])' "$ip"; then
    echo "Укажи публичный IPv4 сервера."
    exit 1
fi
apt-get update
apt-get install -y nginx python3-venv openssl
id daryoft >/dev/null 2>&1 || useradd --system --home-dir /var/lib/daryoft --shell /usr/sbin/nologin daryoft
install -d -o daryoft -g www-data -m 0750 /var/lib/daryoft /var/lib/daryoft/media
if test -d media; then cp -rn media/. /var/lib/daryoft/media/; fi
chown -R daryoft:www-data /var/lib/daryoft/media
if ! test -f /etc/daryoft.env; then
    install -m 0600 /dev/null /etc/daryoft.env
    cat >/etc/daryoft.env <<EOF
DJANGO_SECRET_KEY=$(openssl rand -hex 48)
DJANGO_ALLOWED_HOSTS=$ip,localhost,127.0.0.1
DJANGO_DB=/var/lib/daryoft/db.sqlite3
DJANGO_MEDIA=/var/lib/daryoft/media
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
EOF
fi
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
set -a
source /etc/daryoft.env
set +a
runuser -u daryoft --preserve-environment -- .venv/bin/python manage.py migrate --noinput
.venv/bin/python manage.py collectstatic --noinput
install -d -m 0700 /etc/daryoft-tls
if ! test -f /etc/daryoft-tls/server.crt; then
    openssl req -x509 -newkey rsa:2048 -nodes -days 365 -subj "/CN=$ip" -addext "subjectAltName=IP:$ip" -keyout /etc/daryoft-tls/server.key -out /etc/daryoft-tls/server.crt
fi
install -m 0644 deploy/daryoft.service /etc/systemd/system/daryoft.service
sed "s/DROPLET_IP/$ip/g" deploy/nginx.conf >/etc/nginx/sites-available/daryoft
ln -sfn /etc/nginx/sites-available/daryoft /etc/nginx/sites-enabled/daryoft
nginx -t
systemctl daemon-reload
systemctl enable --now daryoft nginx
systemctl restart daryoft
systemctl reload nginx
curl --retry 5 --retry-connrefused --cacert /etc/daryoft-tls/server.crt --resolve "$ip:443:127.0.0.1" -fsS "https://$ip/api/items/"
