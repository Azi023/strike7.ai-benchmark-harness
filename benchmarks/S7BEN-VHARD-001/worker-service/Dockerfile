FROM golang:1.21-alpine AS builder

WORKDIR /app

# Install build dependencies
RUN apk add --no-cache git

# Copy go mod files
COPY go.mod go.sum ./
RUN go mod download

# Copy source code
COPY . .

# Build the application
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o worker-service .

# Final stage
FROM alpine:latest

# Install runtime dependencies including wget for health checks and postgresql-client
RUN apk add --no-cache ca-certificates wget postgresql-client

WORKDIR /root/

# Copy the binary from builder
COPY --from=builder /app/worker-service .

EXPOSE 8080

CMD ["./worker-service"]
