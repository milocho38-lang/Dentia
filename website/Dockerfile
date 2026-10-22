FROM node:22.23.4-alpine@sha256:fe4f6d74e20370acb04ad889077d14d0f64a9c8ea6a42bc60cddf1e844699914 AS dependencies
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

FROM node:22.23.4-alpine@sha256:fe4f6d74e20370acb04ad889077d14d0f64a9c8ea6a42bc60cddf1e844699914 AS builder
WORKDIR /app
ARG NEXT_PUBLIC_SITE_URL=http://localhost:3010
ARG NEXT_PUBLIC_APP_URL=https://app.dentiapro.com
ARG NEXT_PUBLIC_SITE_INDEXABLE=false
ARG API_PROXY_TARGET=http://dentia-backend:8000
ENV NEXT_TELEMETRY_DISABLED=1
ENV NEXT_PUBLIC_SITE_URL=$NEXT_PUBLIC_SITE_URL
ENV NEXT_PUBLIC_APP_URL=$NEXT_PUBLIC_APP_URL
ENV NEXT_PUBLIC_SITE_INDEXABLE=$NEXT_PUBLIC_SITE_INDEXABLE
ENV API_PROXY_TARGET=$API_PROXY_TARGET
COPY --from=dependencies /app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM node:22.23.4-alpine@sha256:fe4f6d74e20370acb04ad889077d14d0f64a9c8ea6a42bc60cddf1e844699914 AS runner
WORKDIR /app
ARG DENTIA_VCS_REF=unknown
LABEL org.opencontainers.image.revision=$DENTIA_VCS_REF
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=3010
ENV HOSTNAME=0.0.0.0
ENV API_PROXY_TARGET=http://dentia-backend:8000
RUN addgroup --system --gid 1001 nodejs && adduser --system --uid 1001 nextjs
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
USER nextjs
EXPOSE 3010
CMD ["node", "server.js"]
