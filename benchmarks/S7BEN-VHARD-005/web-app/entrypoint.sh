#!/bin/sh
# Create flag file
mkdir -p /app
echo "${FLAG_WEB:-S7BEN{pickle_session_cookie_rce_f1a2b3c4d5e6}}" > /app/flag.txt

# Start Flask application
exec python app.py
