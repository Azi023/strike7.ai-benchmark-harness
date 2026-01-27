#!/bin/bash
set -e

echo "[*] Setting up OpenLDAP for CORP.LOCAL domain..."

# Set domain variables
DOMAIN=${DOMAIN:-CORP.LOCAL}
BASE_DN="dc=corp,dc=local"
ADMIN_PASSWORD=${ADMIN_PASSWORD:-P@ssw0rd123!}

# Configure slapd
echo "[*] Configuring slapd..."
debconf-set-selections <<EOF
slapd slapd/internal/generated_adminpw password ${ADMIN_PASSWORD}
slapd slapd/internal/adminpw password ${ADMIN_PASSWORD}
slapd slapd/password2 password ${ADMIN_PASSWORD}
slapd slapd/password1 password ${ADMIN_PASSWORD}
slapd slapd/dump_database_destdir string /var/backups/slapd-VERSION
slapd slapd/domain string corp.local
slapd shared/organization string CORP
slapd slapd/backend string MDB
slapd slapd/purge_database boolean true
slapd slapd/move_old_database boolean true
slapd slapd/allow_ldap_v2 boolean false
slapd slapd/no_configuration boolean false
EOF

# Reconfigure slapd with new settings
dpkg-reconfigure -f noninteractive slapd

# Configure slapd to listen on TCP
echo "[*] Configuring slapd to listen on all interfaces..."
sed -i "s|^SLAPD_SERVICES=.*|SLAPD_SERVICES=\"ldap://0.0.0.0:389/ ldapi:///\"|" /etc/default/slapd

# Start slapd
echo "[*] Starting slapd service..."
service slapd start

# Wait for LDAP to be ready
sleep 3

# Import organizational structure and users
echo "[*] Importing users and organizational structure..."
ldapadd -x -D "cn=admin,${BASE_DN}" -w "${ADMIN_PASSWORD}" -f /opt/dc/create-users.ldif || true

# Enable anonymous bind for enumeration (intentional vulnerability)
echo "[*] Configuring anonymous bind access (VULNERABLE)..."
cat > /tmp/allow-anon.ldif <<EOF
dn: olcDatabase={1}mdb,cn=config
changetype: modify
replace: olcAccess
olcAccess: {0}to attrs=userPassword by self write by anonymous auth by * none
olcAccess: {1}to * by * read
EOF

ldapmodify -Y EXTERNAL -H ldapi:/// -f /tmp/allow-anon.ldif || true

echo "[+] LDAP setup complete!"
echo "[+] Base DN: ${BASE_DN}"
echo "[+] Anonymous bind: ENABLED (vulnerable)"
echo "[+] Users created: Administrator, alice, bob, svc_web, svc_sql"
