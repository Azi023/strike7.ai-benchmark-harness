#!/bin/bash
set -e

echo "[*] Setting up Kerberos KDC for CORP.LOCAL realm..."

REALM=${REALM:-CORP.LOCAL}
ADMIN_PASSWORD=${ADMIN_PASSWORD:-P@ssw0rd123!}

# Create KDC database (idempotent)
if [ ! -f /var/lib/krb5kdc/principal ]; then
  echo "[*] Creating Kerberos database..."
  kdb5_util create -s -P "${ADMIN_PASSWORD}" <<EOF
${ADMIN_PASSWORD}
${ADMIN_PASSWORD}
EOF
else
  echo "[*] Kerberos database already exists, skipping creation..."
fi

# Create admin ACL
echo "[*] Configuring admin ACL..."
cat > /etc/krb5kdc/kadm5.acl <<EOF
*/admin@${REALM} *
EOF

# Start Kerberos services
echo "[*] Starting Kerberos KDC..."
service krb5-kdc start
service krb5-admin-server start

# Wait for services to be ready
sleep 2

# Check if principals already exist
if kadmin.local -q "listprincs" | grep -q "Administrator@${REALM}"; then
  echo "[*] Principals already exist, skipping creation..."
else
  echo "[*] Creating Kerberos principals..."

  # Administrator principal
  kadmin.local -q "addprinc -pw P@ssw0rd123! Administrator@${REALM}"

  # Regular users
  kadmin.local -q "addprinc -pw Alice123! alice@${REALM}"

  # Bob - with pre-auth DISABLED (AS-REP Roasting vulnerability)
  kadmin.local -q "addprinc -pw BobPassword1 +requires_preauth bob@${REALM}"
  kadmin.local -q "modprinc -requires_preauth bob@${REALM}"

  # Service accounts (Kerberoasting targets)
  kadmin.local -q "addprinc -pw ServiceWeb123 svc_web@${REALM}"
  kadmin.local -q "addprinc -pw SQLService456 svc_sql@${REALM}"

  # Add SPNs for service accounts
  kadmin.local -q "addprinc -randkey HTTP/webapp.corp.local@${REALM}"
  kadmin.local -q "ktadd -k /opt/dc/webapp.keytab HTTP/webapp.corp.local@${REALM}"

  kadmin.local -q "addprinc -randkey MSSQLSvc/dbserver.corp.local@${REALM}"
  kadmin.local -q "ktadd -k /opt/dc/mssql.keytab MSSQLSvc/dbserver.corp.local@${REALM}"

  # Create host principals
  kadmin.local -q "addprinc -randkey host/dc.corp.local@${REALM}"
  kadmin.local -q "addprinc -randkey host/webapp.corp.local@${REALM}"
  kadmin.local -q "addprinc -randkey host/fileserver.corp.local@${REALM}"
fi

echo "[+] Kerberos KDC setup complete!"
echo "[+] Realm: ${REALM}"
echo "[+] Principals created:"
echo "    - Administrator@${REALM}"
echo "    - alice@${REALM}"
echo "    - bob@${REALM} (NO PREAUTH - vulnerable to AS-REP roasting)"
echo "    - svc_web@${REALM} (SPN: HTTP/webapp.corp.local)"
echo "    - svc_sql@${REALM} (SPN: MSSQLSvc/dbserver.corp.local)"

# List all principals
kadmin.local -q "listprincs"
