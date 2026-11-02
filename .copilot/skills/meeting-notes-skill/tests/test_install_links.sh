#!/usr/bin/env bash

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
SANDBOX="${REPO_ROOT}/.installer-test-home"
SKILL_TARGET="${SANDBOX}/.copilot/skills/meeting-notes-skill"
SKILL_BACKUP="${SKILL_TARGET}.pre-dotfiles-backup"
IMPORT_TARGET="${SANDBOX}/.local/bin/krisp-import"
COPY_SOURCE="${SANDBOX}/copy-source"
OTHER_SKILL="${SANDBOX}/.copilot/skills/other-skill"

cleanup() {
	if [[ -L "${SKILL_TARGET}" || -f "${SKILL_TARGET}" ]]; then
		rm -f -- "${SKILL_TARGET}"
	elif [[ -d "${SKILL_TARGET}" ]]; then
		rm -f -- "${SKILL_TARGET}/marker"
		rmdir "${SKILL_TARGET}" 2>/dev/null || true
	fi
	rm -f -- "${IMPORT_TARGET}"
	rm -f -- "${OTHER_SKILL}/marker"
	rmdir "${OTHER_SKILL}" 2>/dev/null || true
	rm -f -- "${COPY_SOURCE}/meeting-notes-skill/marker"
	rm -f -- "${COPY_SOURCE}/other-skill/marker"
	rmdir "${COPY_SOURCE}/meeting-notes-skill" 2>/dev/null || true
	rmdir "${COPY_SOURCE}/other-skill" 2>/dev/null || true
	rmdir "${COPY_SOURCE}" 2>/dev/null || true
	rm -f -- "${SKILL_BACKUP}/marker"
	rmdir "${SKILL_BACKUP}" 2>/dev/null || true
	rmdir "${SANDBOX}/.copilot/skills" 2>/dev/null || true
	rmdir "${SANDBOX}/.copilot" 2>/dev/null || true
	rmdir "${SANDBOX}/.local/bin" 2>/dev/null || true
	rmdir "${SANDBOX}/.local" 2>/dev/null || true
	rmdir "${SANDBOX}" 2>/dev/null || true
}
trap cleanup EXIT

cleanup
mkdir -p "${SKILL_TARGET}"
printf 'keep\n' > "${SKILL_TARGET}/marker"
mkdir -p "${COPY_SOURCE}/meeting-notes-skill" "${COPY_SOURCE}/other-skill"
printf 'overwrite\n' > "${COPY_SOURCE}/meeting-notes-skill/marker"
printf 'copied\n' > "${COPY_SOURCE}/other-skill/marker"

HOME="${SANDBOX}" \
	DOTFILES_LINKS_ONLY=1 \
	DOTFILES_COPY_COPILOT_SKILLS=1 \
	DOTFILES_SKILLS_SOURCE="${COPY_SOURCE}" \
	bash "${REPO_ROOT}/install" >/dev/null

[[ -L "${SKILL_TARGET}" ]]
[[ "$(readlink "${SKILL_TARGET}")" == "${REPO_ROOT}/.copilot/skills/meeting-notes-skill" ]]
[[ -f "${SKILL_BACKUP}/marker" ]]
[[ -L "${IMPORT_TARGET}" ]]
[[ "$(readlink "${IMPORT_TARGET}")" == "${REPO_ROOT}/.local/bin/krisp-import" ]]
[[ "$(cat "${SKILL_BACKUP}/marker")" == "keep" ]]
[[ "$(cat "${OTHER_SKILL}/marker")" == "copied" ]]

HOME="${SANDBOX}" DOTFILES_LINKS_ONLY=1 bash "${REPO_ROOT}/install" >/dev/null
[[ -L "${SKILL_TARGET}" ]]

rm -f -- "${SKILL_TARGET}"
mkdir "${SKILL_TARGET}"
printf 'current\n' > "${SKILL_TARGET}/marker"
if HOME="${SANDBOX}" DOTFILES_LINKS_ONLY=1 bash "${REPO_ROOT}/install" >/dev/null 2>&1; then
	echo "installer should refuse when target and backup both exist" >&2
	exit 1
fi
[[ -f "${SKILL_TARGET}/marker" ]]
[[ -f "${SKILL_BACKUP}/marker" ]]

echo "installer link tests passed"
