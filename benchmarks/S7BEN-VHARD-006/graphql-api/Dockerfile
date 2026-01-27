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

# Expose GraphQL port
EXPOSE 4000

# Run application
CMD ["node", "index.js"]
