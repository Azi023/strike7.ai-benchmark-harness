from app import app
import json

routes = []
for rule in app.url_map.iter_rules():
    routes.append({
        "endpoint": rule.endpoint,
        "methods": list(rule.methods),
        "rule": str(rule)
    })

print(json.dumps(routes, indent=2))
