FROM maven:3.8-eclipse-temurin-11-alpine AS build

WORKDIR /build

# Copy pom.xml and download dependencies
COPY pom.xml .
RUN mvn dependency:go-offline

# Copy source code
COPY src/ src/

# Build application
RUN mvn clean package -DskipTests

# Runtime stage
FROM eclipse-temurin:11-jre-alpine

WORKDIR /app

# Install curl for health checks
RUN apk add --no-cache curl

# Copy jar from build stage
COPY --from=build /build/target/xxe-webapp-1.0.0.jar /app/app.jar

# Create directories
RUN mkdir -p /app/data

# Copy entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose port
EXPOSE 8080

# Use entrypoint for dynamic flag generation
ENTRYPOINT ["/entrypoint.sh"]
CMD ["java", "-jar", "/app/app.jar"]
