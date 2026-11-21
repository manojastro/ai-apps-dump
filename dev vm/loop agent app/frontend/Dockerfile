FROM node:20-alpine AS deps
WORKDIR /app
COPY frontend/package.json ./
RUN npm install

FROM node:20-alpine AS build
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY frontend .
ENV BACKEND_URL=http://backend:8000
RUN npm run build

FROM node:20-alpine
WORKDIR /app
ENV NODE_ENV=production
ENV BACKEND_URL=http://backend:8000
COPY --from=build /app ./
EXPOSE 3000
CMD ["npm", "run", "start"]
