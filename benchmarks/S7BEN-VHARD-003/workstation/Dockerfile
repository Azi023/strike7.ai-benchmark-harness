FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Install tools for penetration testing and Kerberos
RUN apt-get update && \
    apt-get install -y \
    python3 \
    python3-pip \
    krb5-user \
    ldap-utils \
    curl \
    vim \
    git \
    net-tools \
    dnsutils \
    && rm -rf /var/lib/apt/lists/*

# Install impacket for Kerberos attacks
RUN pip3 install flask impacket ldap3

# Create directories
RUN mkdir -p /opt/workstation /opt/tools

# Copy Kerberos config
COPY krb5.conf /etc/krb5.conf

# Copy application files
COPY app.py /opt/workstation/
COPY entrypoint.sh /opt/workstation/

# Make scripts executable
RUN chmod +x /opt/workstation/*.sh

EXPOSE 5000

WORKDIR /opt/workstation

ENTRYPOINT ["/opt/workstation/entrypoint.sh"]
