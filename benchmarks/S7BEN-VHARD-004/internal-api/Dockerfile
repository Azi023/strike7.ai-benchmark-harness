FROM eclipse-temurin:8-jdk-alpine

WORKDIR /opt/api

# Install curl for healthcheck
RUN apk add --no-cache curl

# Create simple Java app that deserializes data
COPY InternalAPI.java .

# Compile Java app
RUN javac InternalAPI.java

# Create flag file
ARG FLAG_INTERNAL
RUN echo "${FLAG_INTERNAL:-SBEN{internal_api_deserialization_g7h8i9j0k1l2}}" > /opt/api/secret.txt

EXPOSE 8081

CMD ["java", "InternalAPI"]
