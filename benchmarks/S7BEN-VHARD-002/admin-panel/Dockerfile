FROM node:18-alpine

WORKDIR /app

RUN apk add --no-cache curl

COPY package*.json ./
RUN npm ci --only=production

COPY . .

EXPOSE 4000

CMD ["node", "index.js"]
