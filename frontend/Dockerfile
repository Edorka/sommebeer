# Frontend static deliverable — nginx serving the built bundle.
# Build context must be frontend/:
#   docker build -f frontend/Dockerfile -t sommebeer-web frontend/
FROM nginxinc/nginx-unprivileged:alpine

# unprivileged image listens on 8080 and drops regular nginx config users
COPY nginx-default.conf /etc/nginx/conf.d/default.conf
COPY dist/ /usr/share/nginx/html/

EXPOSE 8080
HEALTHCHECK --interval=10s --timeout=3s --retries=3 \
    CMD wget -q --spider http://127.0.0.1:8080/ || exit 1
