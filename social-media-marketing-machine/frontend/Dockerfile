# Multi-stage build for a production-sensible Next.js image.
FROM node:20-slim AS deps

WORKDIR /app
COPY package.json ./
RUN npm install --no-audit --no-fund

FROM node:20-slim AS builder

WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

FROM node:20-slim AS runner

WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

RUN useradd --create-home --shell /bin/bash nextjs

COPY --from=builder /app/public ./public
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json

RUN chown -R nextjs:nextjs /app
USER nextjs

EXPOSE 3000

CMD ["npm", "run", "start"]
