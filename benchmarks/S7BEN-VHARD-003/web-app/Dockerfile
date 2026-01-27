FROM node:18-alpine

# Install LDAP client tools
RUN apk add --no-cache openldap-clients curl

# Create app directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy application files
COPY . .

EXPOSE 3000

CMD ["node", "index.js"]
