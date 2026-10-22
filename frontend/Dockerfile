FROM node:22.23.4-alpine@sha256:fe4f6d74e20370acb04ad889077d14d0f64a9c8ea6a42bc60cddf1e844699914 AS deps
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci

FROM node:22.23.4-alpine@sha256:fe4f6d74e20370acb04ad889077d14d0f64a9c8ea6a42bc60cddf1e844699914 AS builder
WORKDIR /app
ARG API_PROXY_TARGET=http://dentia-backend:8000
ENV API_PROXY_TARGET=${API_PROXY_TARGET}
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM node:22.23.4-alpine@sha256:fe4f6d74e20370acb04ad889077d14d0f64a9c8ea6a42bc60cddf1e844699914 AS runner
WORKDIR /app
ARG DENTIA_VCS_REF=unknown
LABEL org.opencontainers.image.revision=$DENTIA_VCS_REF
ENV NODE_ENV=production
ENV API_PROXY_TARGET=http://dentia-backend:8000
ENV PORT=3000
ENV HOSTNAME=0.0.0.0
RUN addgroup -S dentia && adduser -S dentia -G dentia
COPY --chown=dentia:dentia --from=builder /app/.next/standalone ./
COPY --chown=dentia:dentia --from=builder /app/.next/static ./.next/static
USER dentia
EXPOSE 3000
CMD ["node", "server.js"]
