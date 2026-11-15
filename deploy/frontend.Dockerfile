# syntax=docker/dockerfile:1
# 正式環境前端映像：建置 Vite SPA，以 Caddy 在容器內 :80 提供靜態檔，
# 對外由 sitetegy-01 的 edge Caddy 轉入（見 deploy/edge/sites/datavue.caddy）。
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
COPY <<'EOF' /etc/caddy/Caddyfile
:80 {
	root * /srv

	@assets path /assets/*
	header @assets Cache-Control "public, max-age=31536000, immutable"
	@html not path /assets/*
	header @html Cache-Control "no-cache"

	try_files {path} /index.html
	file_server
}
EOF
