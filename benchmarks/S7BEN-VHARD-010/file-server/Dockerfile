FROM nginx:alpine

WORKDIR /usr/share/nginx/html

# Copy files
COPY index.html confidential.txt credentials.txt internal_flag.txt ./

# Copy entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose port
EXPOSE 80

# Use entrypoint for dynamic flag generation
ENTRYPOINT ["/entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]
