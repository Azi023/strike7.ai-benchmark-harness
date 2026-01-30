#!/bin/bash
# Common Strike7 development tasks

case "$1" in
    deploy)
        echo "🚀 Deploying to VPS..."
        ssh root@139.59.80.137 "/opt/strike7-deploy.sh"
        ;;

    sync-vps)
        echo "🔄 Syncing VPS changes to local..."
        ./sync-vps-ports.sh
        ;;

    regen-json)
        echo "📝 Regenerating benchmarks.json..."
        python3 dashboard/scripts/generate_benchmarks_json.py
        ;;

    check-status)
        echo "📊 Checking VPS status..."
        ssh root@139.59.80.137 "systemctl status strike7-dashboard --no-pager"
        echo ""
        ssh root@139.59.80.137 "docker ps --format 'table {{.Names}}\t{{.Ports}}'"
        ;;

    logs)
        echo "📄 Viewing deployment logs..."
        ssh root@139.59.80.137 "tail -50 /var/log/strike7-deploy.log"
        ;;

    *)
        echo "Usage: $0 {deploy|sync-vps|regen-json|check-status|logs}"
        exit 1
        ;;
esac
