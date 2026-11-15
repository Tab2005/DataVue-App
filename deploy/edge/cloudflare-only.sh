#!/usr/bin/env bash
# deploy/edge/cloudflare-only.sh — sitetegy-01 的 80/443 只接受 Cloudflare 來源
#
#   cloudflare-only.sh on    建立／更新 Cloudflare IP 清單（ipset cf4）並套用規則
#   cloudflare-only.sh off   移除規則（緊急時直接連主機 IP 測試用）
#
# Docker 對外的埠走 FORWARD，不經過 INPUT／ufw，所以規則放在 DOCKER-USER chain。
# SSH（22）走 INPUT，不受影響。主機目前只有 IPv4，因此只處理 iptables。
# 主機位置：/opt/edge/cloudflare-only.sh；開機與每週更新由
# cloudflare-only.service / cloudflare-only.timer 執行。
set -euo pipefail

EXT_IF=eth0
SET=cf4
TAG="cloudflare-only"

# 抓不到官方清單時的後備（https://www.cloudflare.com/ips-v4/，與 deploy/edge/Caddyfile 一致）
FALLBACK="173.245.48.0/20 103.21.244.0/22 103.22.200.0/22 103.31.4.0/22 141.101.64.0/18
108.162.192.0/18 190.93.240.0/20 188.114.96.0/20 197.234.240.0/22 198.41.128.0/17
162.158.0.0/15 104.16.0.0/13 104.24.0.0/14 172.64.0.0/13 131.0.72.0/22"

remove_rules() {
  while iptables -S DOCKER-USER | grep -q "$TAG"; do
    rule=$(iptables -S DOCKER-USER | grep "$TAG" | head -1 | sed 's/^-A /-D /')
    eval "iptables $rule"
  done
}

case "${1:-on}" in
  on)
    ranges=$(curl -fsS -m 10 https://www.cloudflare.com/ips-v4/ || true)
    if ! grep -qE '^[0-9.]+/[0-9]+$' <<<"$ranges"; then
      echo "無法取得 Cloudflare IP 清單，改用內建清單" >&2
      ranges=$FALLBACK
    fi

    # 先建好新清單再整份替換，套用期間不會出現空清單
    ipset create "$SET" hash:net -exist
    ipset create "$SET-new" hash:net -exist
    ipset flush "$SET-new"
    for r in $ranges; do ipset add "$SET-new" "$r" -exist; done
    ipset swap "$SET-new" "$SET"
    ipset destroy "$SET-new"

    remove_rules
    for port in 80 443; do
      iptables -I DOCKER-USER -i "$EXT_IF" -p tcp \
        -m conntrack --ctorigdstport "$port" --ctdir ORIGINAL \
        -m set ! --match-set "$SET" src \
        -m comment --comment "$TAG" -j DROP
    done
    echo "已套用：$EXT_IF 的 80/443 只接受 Cloudflare（$(ipset list "$SET" | grep -cE '^[0-9]') 個網段）"
    ;;
  off)
    remove_rules
    echo "已移除 Cloudflare-only 規則，80/443 對所有來源開放"
    ;;
  *)
    echo "用法：cloudflare-only.sh on|off" >&2
    exit 2
    ;;
esac
