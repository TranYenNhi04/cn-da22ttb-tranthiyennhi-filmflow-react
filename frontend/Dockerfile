# Build stage
FROM node:18-alpine AS build
WORKDIR /app

# Nhận biến API từ docker-compose
ARG REACT_APP_API_BASE
ENV REACT_APP_API_BASE=$REACT_APP_API_BASE

COPY package.json package-lock.json ./
RUN npm install

COPY . .

# Fix lỗi OpenSSL trên Node 20
ENV NODE_OPTIONS=--openssl-legacy-provider

RUN npm run build

# Production stage
FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
