FROM node:22-alpine AS deps
WORKDIR /web
COPY package.json package-lock.json* ./
RUN npm install

FROM node:22-alpine AS builder
WORKDIR /web
COPY --from=deps /web/node_modules ./node_modules
COPY . .
ARG BACKEND_URL=http://api:8000
ENV BACKEND_URL=$BACKEND_URL
RUN npm run build

FROM node:22-alpine AS runner
WORKDIR /web
ENV NODE_ENV=production
COPY --from=builder /web/.next/standalone ./
COPY --from=builder /web/.next/static ./.next/static
COPY --from=builder /web/public ./public
EXPOSE 3000
CMD ["node", "server.js"]
