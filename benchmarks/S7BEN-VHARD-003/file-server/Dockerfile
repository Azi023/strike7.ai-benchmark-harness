FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies
RUN apt-get update && \
    apt-get install -y \
    python3 \
    python3-pip \
    krb5-user \
    curl \
    vim \
    net-tools \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
RUN pip3 install flask

# Create directories
RUN mkdir -p /opt/fileserver /opt/fileserver/shares

# Copy Kerberos config
COPY krb5.conf /etc/krb5.conf

# Copy application files
COPY app.py /opt/fileserver/
COPY entrypoint.sh /opt/fileserver/

# Create shared files with sensitive data
RUN echo "Database Connection String: Server=dbserver.corp.local;Database=CorpDB;User=sa;Password=DBP@ssw0rd!" > /opt/fileserver/shares/db_config.txt
RUN echo "Admin credentials for emergency access:" > /opt/fileserver/shares/admin_notes.txt
RUN echo "Username: Administrator" >> /opt/fileserver/shares/admin_notes.txt
RUN echo "Password: P@ssw0rd123!" >> /opt/fileserver/shares/admin_notes.txt
RUN echo "" >> /opt/fileserver/shares/admin_notes.txt
RUN echo "NTLM Hash: aad3b435b51404eeaad3b435b51404ee:8846f7eaee8fb117ad06bdd830b7586c" >> /opt/fileserver/shares/admin_notes.txt

# Make scripts executable
RUN chmod +x /opt/fileserver/*.sh

EXPOSE 8080

WORKDIR /opt/fileserver

ENTRYPOINT ["/opt/fileserver/entrypoint.sh"]
