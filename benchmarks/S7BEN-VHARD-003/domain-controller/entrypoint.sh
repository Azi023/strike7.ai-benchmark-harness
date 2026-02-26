#!/bin/bash
set -e

# --- Dynamic flag generation ---
FLAG_GOLDEN_TICKET="S7BEN{domain_admin_golden_ticket_$(cat /dev/urandom | tr -dc 'a-f0-9' | head -c 12)}"
export FLAG_GOLDEN_TICKET
echo "$FLAG_GOLDEN_TICKET" > /tmp/flag.txt
# --- End dynamic flag generation ---

echo "[*] Starting Active Directory Domain Controller (CORP.LOCAL)..."
echo "[*] Hostname: $(hostname -f)"
echo "[*] IP Address: $(hostname -i)"

# Set environment variables with defaults
export DOMAIN=${DOMAIN:-CORP.LOCAL}
export REALM=${REALM:-CORP.LOCAL}
export ADMIN_PASSWORD=${ADMIN_PASSWORD:-P@ssw0rd123!}

echo ""
echo "========================================="
echo "Phase 1: OpenLDAP Setup"
echo "========================================="
/opt/dc/setup-ldap.sh

echo ""
echo "========================================="
echo "Phase 2: Kerberos KDC Setup"
echo "========================================="
/opt/dc/setup-kerberos.sh

echo ""
echo "========================================="
echo "Domain Controller Ready!"
echo "========================================="
echo ""
echo "Domain: ${DOMAIN}"
echo "Realm: ${REALM}"
echo ""
echo "Services Running:"
echo "  - LDAP on port 389"
echo "  - LDAPS on port 636"
echo "  - Kerberos KDC on port 88"
echo "  - Kerberos Admin on port 749"
echo ""
echo "Vulnerable Accounts:"
echo "  - bob@${REALM} (NO PREAUTH - AS-REP Roasting)"
echo "  - svc_web@${REALM} (Kerberoastable - HTTP/webapp.corp.local)"
echo "  - svc_sql@${REALM} (Kerberoastable - MSSQLSvc/dbserver.corp.local)"
echo ""
echo "Test LDAP: ldapsearch -x -H ldap://localhost -b dc=corp,dc=local"
echo "Test Kerberos: kinit alice@${REALM}"
echo ""
echo "[+] Domain Controller initialization complete!"
echo ""

# Keep container running by tailing logs
echo "[*] Tailing service logs..."
tail -f /var/log/slapd.log /var/log/krb5kdc.log /var/log/kadmin.log 2>/dev/null &

# Wait for any process to exit
wait -n

# Exit with status of process that exited first
exit $?
