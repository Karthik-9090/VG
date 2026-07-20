FROM nginx:1.26-alpine

COPY nginx.conf /etc/nginx/nginx.conf
RUN apk add --no-cache openssl wget && \
    mkdir -p /etc/nginx/ssl && \
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/nginx/ssl/key.pem \
    -out /etc/nginx/ssl/cert.pem \
    -subj "/C=IN/ST=Delhi/L=Delhi/O=VayuGuard/CN=localhost" && \
    chown -R nginx:nginx /etc/nginx

EXPOSE 80 443

HEALTHCHECK --interval=10s --timeout=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost/health || exit 1

CMD ["nginx", "-g", "daemon off;"]
