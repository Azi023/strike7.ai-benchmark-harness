FROM strike7/base-web-app:latest

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies including DOMPurify
RUN npm install

# Copy application source
COPY *.js ./
COPY views ./views
COPY public ./public

# Create session directory
RUN mkdir -p /tmp/sessions && chmod 777 /tmp/sessions

EXPOSE 3000

HEALTHCHECK --interval=10s --timeout=5s --retries=3 --start-period=20s \
    CMD curl -f http://localhost:3000/health || exit 1

CMD ["node", "server.js"]
