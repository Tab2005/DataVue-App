# 正式環境前端映像：建置 Vite SPA，交給 Caddy 提供靜態檔並反向代理 backend
# （見 deploy/Caddyfile、deploy/docker-compose.prod.yml）
# 建置 context 為 frontend/；刻意不放在 frontend/Dockerfile，避免 Zeabur 自動偵測改用它建置
#   docker build -f deploy/frontend.Dockerfile frontend
FROM node:20-alpine AS build
WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
ARG VITE_API_URL=https://datavue-bk.sitetegy.com
ENV VITE_API_URL=$VITE_API_URL
RUN npm run build

FROM caddy:2.10-alpine
COPY --from=build /app/dist /srv
