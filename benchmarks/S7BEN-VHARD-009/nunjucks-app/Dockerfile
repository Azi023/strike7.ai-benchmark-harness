FROM node:20-alpine

WORKDIR /app

# Install wget for health checks
RUN apk add --no-cache wget

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install --production

# Copy application
COPY index.js .

# Expose port
EXPOSE 3000

# Start application
CMD ["npm", "start"]
