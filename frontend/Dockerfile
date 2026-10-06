FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci

FROM node:22-alpine AS builder
WORKDIR /app
ARG API_PROXY_TARGET=http://dentia-backend:8000
ENV API_PROXY_TARGET=${API_PROXY_TARGET}
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM node:22-alpine AS runner
WORKDIR /app
ARG DENTIA_VCS_REF=unknown
LABEL org.opencontainers.image.revision=$DENTIA_VCS_REF
ENV NODE_ENV=production
ENV API_PROXY_TARGET=http://dentia-backend:8000
RUN addgroup -S dentia && adduser -S dentia -G dentia
COPY --chown=dentia:dentia --from=builder /app ./
USER dentia
EXPOSE 3000
CMD ["npm", "run", "start"]
