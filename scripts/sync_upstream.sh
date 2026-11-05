#!/usr/bin/env bash
# Cập nhật lõi luật (references/law/, examples/, scan.sh, fetch-site.sh) từ vn-law-check upstream.
#
#   bash scripts/sync_upstream.sh                 # tải bản mới nhất từ GitHub về thư mục tạm, in diff
#   bash scripts/sync_upstream.sh --apply         # chép đè sau khi đã xem diff
#   UPSTREAM_DIR=/path/vn-law-check bash scripts/sync_upstream.sh   # dùng bản đã clone sẵn
#
# Không đụng tới phần riêng của vn-law-guard (platforms, templates, dynamic_scan.py...).
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
APPLY="${1:-}"
if [ -z "${UPSTREAM_DIR:-}" ]; then
  UPSTREAM_DIR="$(mktemp -d)/vn-law-check"
  git clone --depth 1 https://github.com/mhfed/vn-law-check.git "$UPSTREAM_DIR" >/dev/null
fi
STAGE="$(mktemp -d)"
mkdir -p "$STAGE/references/law" "$STAGE/examples" "$STAGE/scripts"
cp "$UPSTREAM_DIR"/references/*.md "$STAGE/references/law/"
cp "$UPSTREAM_DIR/sources/legal-references.md" "$STAGE/references/law/"
cp "$UPSTREAM_DIR"/examples/privacy-policy-template.md "$UPSTREAM_DIR"/examples/sample-audit-report.md "$STAGE/examples/"
cp "$UPSTREAM_DIR"/scripts/scan.sh "$UPSTREAM_DIR"/scripts/fetch-site.sh "$STAGE/scripts/"
cp "$UPSTREAM_DIR/LICENSE" "$STAGE/LICENSE.upstream"
# Đổi đường dẫn nội bộ sang bố cục references/law/
sed -i 's#`references/0#`references/law/0#g; s#`references/1#`references/law/1#g; s#sources/legal-references.md#references/law/legal-references.md#g' \
  "$STAGE"/references/law/*.md "$STAGE"/examples/*.md
echo "Upstream: $(git -C "$UPSTREAM_DIR" log -1 --format='%h %cd' 2>/dev/null || echo 'không rõ commit')"
head -3 "$STAGE/references/law/legal-references.md" | tail -1
for f in $(cd "$STAGE" && find . -type f | sort); do
  diff -q "$STAGE/$f" "$HERE/$f" >/dev/null 2>&1 || echo "thay đổi: $f"
done
if [ "$APPLY" = "--apply" ]; then
  cp -r "$STAGE"/. "$HERE"/
  echo "Đã chép. Kiểm tra RULES.md (trích từ SKILL.md upstream) có cần cập nhật tay không, và sửa ngày trong NOTICE.md."
else
  echo "Chưa ghi gì. Xem diff: diff -ru '$HERE/references/law' '$STAGE/references/law'  rồi chạy lại với --apply."
fi
