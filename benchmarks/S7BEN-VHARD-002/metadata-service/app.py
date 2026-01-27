#!/usr/bin/env python3
"""
Simulated AWS EC2 Metadata Service (IMDSv1)
Mimics http://169.254.169.254/latest/meta-data/
"""

from flask import Flask, Response
import os
import json

app = Flask(__name__)

# Simulated AWS credentials (IAM role credentials)
AWS_CREDENTIALS = {
    "AccessKeyId": os.getenv('AWS_ACCESS_KEY_ID', 'AKIAIOSFODNN7EXAMPLE'),
    "SecretAccessKey": os.getenv('AWS_SECRET_ACCESS_KEY', 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY'),
    "Token": os.getenv('AWS_SESSION_TOKEN', 'FwoGZXIvYXdzEBcaDKj7xT9PQVz8Example...'),
    "Expiration": "2026-01-13T12:00:00Z"
}

# Flag embedded in user-data
USER_DATA_SCRIPT = f"""#!/bin/bash
# EC2 Instance User Data Script
# Auto-generated on instance launch

# Application configuration
export APP_ENV=production
export DB_HOST=internal-db.company.internal
export DB_USER=app_user
export DB_PASS=SuperSecretPassword123!

# Secret API keys
export API_KEY=sk-prod-abc123def456ghi789
export WEBHOOK_SECRET=whsec_example1234567890

# FLAG FOR SSRF CHALLENGE
export SSRF_FLAG=S7BEN{{ssrf_metadata_access_169_254_169_254}}

# Start application
/opt/app/start.sh
"""


@app.route('/latest/meta-data/')
@app.route('/latest/meta-data')
def metadata_root():
    """Root metadata listing"""
    return Response(
        "ami-id\n"
        "ami-launch-index\n"
        "ami-manifest-path\n"
        "hostname\n"
        "iam/\n"
        "instance-id\n"
        "instance-type\n"
        "local-hostname\n"
        "local-ipv4\n"
        "mac\n"
        "placement/\n"
        "public-hostname\n"
        "public-ipv4\n"
        "security-groups\n",
        mimetype='text/plain'
    )


@app.route('/latest/meta-data/instance-id')
def instance_id():
    return Response("i-0abcd1234efgh5678", mimetype='text/plain')


@app.route('/latest/meta-data/instance-type')
def instance_type():
    return Response("t3.micro", mimetype='text/plain')


@app.route('/latest/meta-data/ami-id')
def ami_id():
    return Response("ami-0c55b159cbfafe1f0", mimetype='text/plain')


@app.route('/latest/meta-data/hostname')
@app.route('/latest/meta-data/local-hostname')
def hostname():
    return Response("ip-172-20-0-10.ec2.internal", mimetype='text/plain')


@app.route('/latest/meta-data/local-ipv4')
def local_ipv4():
    return Response("172.20.0.10", mimetype='text/plain')


@app.route('/latest/meta-data/public-ipv4')
@app.route('/latest/meta-data/public-hostname')
def public_info():
    return Response("ec2-54-123-45-67.compute-1.amazonaws.com", mimetype='text/plain')


@app.route('/latest/meta-data/iam/')
@app.route('/latest/meta-data/iam')
def iam_root():
    """IAM role information"""
    return Response(
        "info\n"
        "security-credentials/\n",
        mimetype='text/plain'
    )


@app.route('/latest/meta-data/iam/info')
def iam_info():
    """IAM role metadata"""
    info = {
        "Code": "Success",
        "LastUpdated": "2026-01-12T10:30:00Z",
        "InstanceProfileArn": "arn:aws:iam::123456789012:instance-profile/WebServerRole",
        "InstanceProfileId": "AIPAI234567EXAMPLE"
    }
    return Response(json.dumps(info, indent=2), mimetype='application/json')


@app.route('/latest/meta-data/iam/security-credentials/')
@app.route('/latest/meta-data/iam/security-credentials')
def security_credentials_list():
    """List available IAM roles"""
    return Response("WebServerRole\n", mimetype='text/plain')


@app.route('/latest/meta-data/iam/security-credentials/WebServerRole')
def security_credentials():
    """
    Return temporary AWS credentials for IAM role
    This is the main target for SSRF attacks
    """
    credentials = {
        "Code": "Success",
        "LastUpdated": "2026-01-12T10:30:00Z",
        "Type": "AWS-HMAC",
        "AccessKeyId": AWS_CREDENTIALS['AccessKeyId'],
        "SecretAccessKey": AWS_CREDENTIALS['SecretAccessKey'],
        "Token": AWS_CREDENTIALS['Token'],
        "Expiration": AWS_CREDENTIALS['Expiration']
    }
    return Response(json.dumps(credentials, indent=2), mimetype='application/json')


@app.route('/latest/user-data')
def user_data():
    """
    Return user-data script with embedded secrets and flag
    """
    return Response(USER_DATA_SCRIPT, mimetype='text/plain')


@app.route('/latest/dynamic/instance-identity/document')
def instance_identity():
    """Instance identity document"""
    doc = {
        "accountId": "123456789012",
        "architecture": "x86_64",
        "availabilityZone": "us-east-1a",
        "imageId": "ami-0c55b159cbfafe1f0",
        "instanceId": "i-0abcd1234efgh5678",
        "instanceType": "t3.micro",
        "privateIp": "172.20.0.10",
        "region": "us-east-1",
        "version": "2017-09-30"
    }
    return Response(json.dumps(doc, indent=2), mimetype='application/json')


@app.route('/')
def root():
    """Root endpoint"""
    return Response(
        "latest\n"
        "2021-01-03\n",
        mimetype='text/plain'
    )


if __name__ == '__main__':
    # Listen on port 80 to simulate real metadata service
    app.run(host='0.0.0.0', port=80, debug=False)
