FROM node:18-alpine

WORKDIR /app

# Install curl for health checks
RUN apk add --no-cache curl

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy application code
COPY . .

# Create directory for keys
RUN mkdir -p /app/keys

EXPOSE 3000

CMD ["node", "index.js"]
