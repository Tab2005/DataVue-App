# DataVue 備份與還原（sitetegy-01）

## 備份內容

| 內容 | 頻率 | 位置 | 保留 |
|---|---|---|---|
| 資料庫 `pg_dump -Fc` | 每日 03:00 | R2 `sitetegy-backups/datavue/db/`、主機 `/opt/datavue/backup/daily/` | R2 30 天、主機 7 天 |
| 素材 volume `datavue_storage` | 每週日 03:30（增量，只新增不刪除） | R2 `sitetegy-backups/datavue/storage/` | 永久 |

- 腳本：`deploy/backup.sh`（主機 `/opt/datavue/backup.sh`）
- 排程：`/etc/cron.d/datavue-backup`；紀錄：`/opt/datavue/backup/backup.log`
- R2 憑證：`/opt/backup/r2.env`（本機備份 `~/.ssh/r2-backup.env`）
- 不在備份內：`/opt/datavue/.env`（本機 `backend/.env.production`）、Origin 憑證（本機 `~/.ssh/cf-origin/`）

## 準備：rclone 指令

在主機上執行，之後的步驟都用 `R` 存取 R2：

```bash
set -a; . /opt/backup/r2.env; set +a
mkdir -p /tmp/restore
R() {
  docker run --rm -e RCLONE_CONFIG=/dev/null \
    -e RCLONE_CONFIG_R2_TYPE=s3 -e RCLONE_CONFIG_R2_PROVIDER=Cloudflare \
    -e RCLONE_CONFIG_R2_ACCESS_KEY_ID="$R2_ACCESS_KEY_ID" \
    -e RCLONE_CONFIG_R2_SECRET_ACCESS_KEY="$R2_SECRET_ACCESS_KEY" \
    -e RCLONE_CONFIG_R2_ENDPOINT="https://$R2_ACCOUNT_ID.r2.cloudflarestorage.com" \
    -v /tmp/restore:/restore -v datavue_storage:/storage \
    rclone/rclone:1.68.2 "$@"
}
R lsl r2:sitetegy-backups/datavue/db/   # 列出可用的資料庫備份
```

## 還原資料庫

會覆蓋現有資料庫，先停 backend / worker：

```bash
cd /opt/datavue
C="docker compose -f docker-compose.prod.yml"
F=datavue-YYYYmmdd-HHMM.dump                       # 從上面清單挑一份
R copyto r2:sitetegy-backups/datavue/db/$F /restore/$F

$C stop backend worker
$C exec -T postgres psql -U datavue -d postgres \
  -c "DROP DATABASE datavue WITH (FORCE);" -c "CREATE DATABASE datavue OWNER datavue;"
$C exec -T postgres pg_restore -U datavue -d datavue --no-owner --no-acl --exit-on-error < /tmp/restore/$F
$C up -d backend worker
```

## 還原素材檔案

```bash
R copy r2:sitetegy-backups/datavue/storage/ /storage --transfers 8
# 檔案擁有者需為 appuser（uid 995）
docker run --rm -v datavue_storage:/s alpine chown -R 995:995 /s
```

## 整台主機重建

1. 新主機依 sitetegy-01 的方式安裝 Docker，建立 `docker network create edge`
2. 放回 `/opt/edge`（`deploy/edge/` + Origin 憑證）、`/opt/datavue/.env`、`/opt/backup/r2.env`
3. `cd /opt/edge && docker compose up -d`
4. 手動觸發 GitHub Actions「Deploy (Tencent Cloud)」，或在主機 `docker compose -f docker-compose.prod.yml up -d`
5. 依上面步驟還原資料庫與素材，安裝 `/etc/cron.d/datavue-backup`
6. Cloudflare DNS 指向新 IP
