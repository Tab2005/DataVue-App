#!/usr/bin/env bash
# deploy/backup.sh — DataVue 備份到 Cloudflare R2（bucket: sitetegy-backups）
#
#   backup.sh db      每日：pg_dump → 本機保留 7 天，R2 datavue/db/ 保留 30 天
#   backup.sh files   每週：素材 volume 增量上傳到 R2 datavue/storage/（只新增不刪除）
#
# 主機位置：/opt/datavue/backup.sh（由 GitHub Actions 部署時複製）
# R2 憑證：/opt/backup/r2.env（R2_ACCOUNT_ID / R2_ACCESS_KEY_ID / R2_SECRET_ACCESS_KEY，sitetegy-01 各專案共用）
# 排程：/etc/cron.d/datavue-backup；紀錄：/opt/datavue/backup/backup.log
# 失敗通知：/opt/backup/healthchecks.env（HC_DATAVUE_DB / HC_DATAVUE_FILES，Healthchecks.io ping 網址，選用）
# 還原步驟見 deploy/RESTORE.md
set -euo pipefail

MODE="${1:?用法：backup.sh db|files}"
APP_DIR=/opt/datavue
LOCAL_DIR="$APP_DIR/backup/daily"
BUCKET=sitetegy-backups
RCLONE_IMAGE=rclone/rclone:1.68.2

set -a
# shellcheck disable=SC1091
. /opt/backup/r2.env
# shellcheck disable=SC1091
[ -f /opt/backup/healthchecks.env ] && . /opt/backup/healthchecks.env
set +a

case "$MODE" in
  db) HC_URL="${HC_DATAVUE_DB:-}" ;;
  files) HC_URL="${HC_DATAVUE_FILES:-}" ;;
esac
hc_ping() { [ -n "${HC_URL:-}" ] && curl -fsS -m 10 --retry 3 -o /dev/null "$HC_URL$1" || true; }
hc_ping /start
trap 'hc_ping /fail' ERR

rclone() {
  docker run --rm \
    -e RCLONE_CONFIG_R2_TYPE=s3 \
    -e RCLONE_CONFIG_R2_PROVIDER=Cloudflare \
    -e RCLONE_CONFIG_R2_ACCESS_KEY_ID="$R2_ACCESS_KEY_ID" \
    -e RCLONE_CONFIG_R2_SECRET_ACCESS_KEY="$R2_SECRET_ACCESS_KEY" \
    -e RCLONE_CONFIG_R2_ENDPOINT="https://$R2_ACCOUNT_ID.r2.cloudflarestorage.com" \
    -e RCLONE_CONFIG_R2_NO_CHECK_BUCKET=true \
    -e RCLONE_CONFIG=/dev/null \
    "${RCLONE_MOUNTS[@]}" \
    "$RCLONE_IMAGE" "$@"
}

log() { echo "$(date '+%F %T') [$MODE] $*"; }

case "$MODE" in
  db)
    mkdir -p "$LOCAL_DIR"
    file="datavue-$(date +%Y%m%d-%H%M).dump"
    docker compose -f "$APP_DIR/docker-compose.prod.yml" exec -T postgres \
      pg_dump -U datavue -d datavue -Fc --no-owner --no-acl > "$LOCAL_DIR/$file.tmp"
    mv "$LOCAL_DIR/$file.tmp" "$LOCAL_DIR/$file"
    log "dump $file $(du -h "$LOCAL_DIR/$file" | cut -f1)"

    RCLONE_MOUNTS=(-v "$LOCAL_DIR:/data:ro")
    rclone copyto "/data/$file" "r2:$BUCKET/datavue/db/$file"
    rclone delete --min-age 30d "r2:$BUCKET/datavue/db/"
    find "$LOCAL_DIR" -name 'datavue-*.dump' -mtime +7 -delete
    log "uploaded r2:$BUCKET/datavue/db/$file"
    ;;
  files)
    # copy 不刪除 R2 上已有檔案：本機誤刪也不會把備份一起刪掉
    RCLONE_MOUNTS=(-v datavue_storage:/data:ro)
    rclone copy /data "r2:$BUCKET/datavue/storage/" --transfers 8 --stats-one-line --stats 0
    log "storage synced to r2:$BUCKET/datavue/storage/"
    ;;
  *)
    echo "未知模式：$MODE" >&2
    exit 2
    ;;
esac

hc_ping ""
