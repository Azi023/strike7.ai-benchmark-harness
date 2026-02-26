FROM eclipse-temurin:8-jdk-alpine

WORKDIR /opt/api

# Install curl for healthcheck
RUN apk add --no-cache curl

# Create simple Java app that deserializes data
COPY InternalAPI.java .

# Compile Java app
RUN javac InternalAPI.java

# Copy and set entrypoint
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8081

ENTRYPOINT ["/entrypoint.sh"]
