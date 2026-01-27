FROM nginx:alpine

WORKDIR /usr/share/nginx/html

# Copy files
COPY index.html confidential.txt credentials.txt internal_flag.txt ./

# Expose port
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
