#!/usr/bin/env bash
# 교육생용 규칙 ZIP 생성 → demo/ide/downloads/ (StaticFiles /ide/downloads/ 로 서빙)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAGE="$(mktemp -d)"
trap 'rm -rf "${STAGE}"' EXIT

PKG_NAME="idr-cursor-rules-student"
PKG="${STAGE}/${PKG_NAME}"
OUT="${ROOT}/demo/ide/downloads"
TEMPLATE="${ROOT}/demo/ide/student_package_template"

mkdir -p "${PKG}/.cursor/rules" "${PKG}/.cursor/skills/idr-session-workflow" "${PKG}/docs/rules"
mkdir -p "${OUT}"

DATE="$(date +%Y%m%d)"
echo "idr-cursor-rules-student r${DATE}" > "${PKG}/VERSION.txt"
echo "Built from lis_cursor at $(date -Iseconds 2>/dev/null || date)" >> "${PKG}/VERSION.txt"

cp "${TEMPLATE}/README_교육생.md" "${PKG}/README_교육생.md"
cp "${ROOT}/.cursor/rules/git-commit-korean.mdc" "${PKG}/.cursor/rules/"
cp "${ROOT}/.cursor/skills/idr-session-workflow/SKILL.md" "${PKG}/.cursor/skills/idr-session-workflow/"
cp "${ROOT}/.cursorrules" "${PKG}/cursorrules.example"

for f in workflow_gates.md project_context.md backend_architecture.md dify_integration.md error_analysis.md; do
  cp "${ROOT}/docs/rules/${f}" "${PKG}/docs/rules/"
done

(
  cd "${STAGE}"
  zip -rq "${OUT}/${PKG_NAME}.zip" "${PKG_NAME}"
)

(
  cd "${OUT}"
  sha256sum "${PKG_NAME}.zip" > "${PKG_NAME}.zip.sha256"
)

echo "OK: ${OUT}/${PKG_NAME}.zip"
echo "     ${OUT}/${PKG_NAME}.zip.sha256"
