FROM ubuntu:22.04

# Prevent interactive prompts during installation
ENV DEBIAN_FRONTEND=noninteractive

# Install OpenLDAP, Kerberos, and utilities
RUN apt-get update && \
    apt-get install -y \
    slapd \
    ldap-utils \
    krb5-kdc \
    krb5-admin-server \
    krb5-user \
    libsasl2-modules-gssapi-mit \
    python3 \
    python3-pip \
    curl \
    vim \
    net-tools \
    && rm -rf /var/lib/apt/lists/*


# Create directory structure
RUN mkdir -p /opt/dc /var/lib/krb5kdc /etc/ldap/slapd.d

# Copy configuration files
COPY setup-ldap.sh /opt/dc/
COPY setup-kerberos.sh /opt/dc/
COPY create-users.ldif /opt/dc/
COPY krb5.conf /etc/krb5.conf
COPY kdc.conf /etc/krb5kdc/kdc.conf
COPY entrypoint.sh /opt/dc/

# Make scripts executable
RUN chmod +x /opt/dc/*.sh

# Expose ports
# 389: LDAP
# 636: LDAPS
# 88: Kerberos
# 464: Kerberos password change
# 749: Kerberos admin
EXPOSE 389 636 88 464 749

WORKDIR /opt/dc

ENTRYPOINT ["/opt/dc/entrypoint.sh"]
