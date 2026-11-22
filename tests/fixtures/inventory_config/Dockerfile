# syntax=docker/dockerfile:1
FROM node:24 AS installer
WORKDIR /app
COPY . .
RUN npm ci \
    --omit=dev
USER 0

FROM --platform=linux/amd64 gcr.io/distroless/nodejs24-debian13
WORKDIR /app
COPY --from=installer /app /app
EXPOSE 3000
EXPOSE 8080/tcp
USER 65532
CMD ["build/server.js"]
