FROM node:20-alpine

WORKDIR /app

# Install curl for healthcheck
RUN apk add --no-cache curl

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install --production

# Copy application files
COPY index.js ./
COPY schema.graphql ./

# Copy and set entrypoint for dynamic flag generation
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose GraphQL port
EXPOSE 4000

# Run application via entrypoint
ENTRYPOINT ["/entrypoint.sh"]
