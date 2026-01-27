FROM maven:3.8-openjdk-8 AS build

WORKDIR /app

# Copy pom.xml and download dependencies
COPY pom.xml .
RUN mvn dependency:go-offline

# Copy source code
COPY src ./src

# Build application
RUN mvn clean package -DskipTests

# Runtime stage
FROM eclipse-temurin:8-jre-alpine

WORKDIR /app

# Install curl for healthcheck
RUN apk add --no-cache curl

# Copy JAR from build stage
COPY --from=build /app/target/webapp-1.0.jar /app/webapp.jar

# Create flag file
ARG FLAG_WEB
RUN echo "${FLAG_WEB:-SBEN{java_deserialize_web_rce_a1b2c3d4e5f6}}" > /app/flag.txt

# Create data directory
RUN mkdir -p /app/data

EXPOSE 8080

ENTRYPOINT ["java", "-jar", "/app/webapp.jar"]
