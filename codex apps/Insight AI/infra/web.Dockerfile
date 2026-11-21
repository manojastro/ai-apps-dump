FROM node:22.17.1-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY app ./app
COPY lib ./lib
COPY tsconfig.json next-env.d.ts next.config.ts postcss.config.mjs ./
ENV API_INTERNAL_URL=http://api:8000
RUN npm run build
FROM node:22.17.1-alpine
WORKDIR /app
ENV NODE_ENV=production API_INTERNAL_URL=http://api:8000
COPY --from=build --chown=node:node /app /app
USER node
EXPOSE 3000
CMD ["npm", "start", "--", "--hostname", "0.0.0.0"]
