#!/bin/bash
# Generic healthcheck for Java applications
# Checks if port is provided as argument, otherwise checks common ports

PORT=${1:-8080}

if nc -z localhost $PORT 2>/dev/null; then
    exit 0
else
    exit 1
fi
