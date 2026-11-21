FROM node:24-slim
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build
ENV EVE_HOST=0.0.0.0
EXPOSE 3101 3102 3103 3104 3105
CMD ["npm", "start"]
