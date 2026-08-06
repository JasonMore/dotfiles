#!/usr/bin/env bash
# Behavioral tests for the dotfiles installer.
#
# These tests run the real `install` script (and its helper scripts) end to
# end, but with:
#   - an isolated, throwaway $HOME under tests/.scratch/ (never /tmp, never
#     the real $HOME)
#   - CODESPACES=1 so the Codespaces-only branch is exercised
#   - a PATH pointing at tests/mocks/bin so sudo/chsh/git/gh/npx/curl never
#     touch the real network, system shell config, or GitHub account
#
# No real account, network, or system state is ever changed by this file.
set -euo pipefail

TESTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "${TESTS_DIR}/.." && pwd)"
MOCK_BIN="${TESTS_DIR}/mocks/bin"
SCRATCH_ROOT="${TESTS_DIR}/.scratch"
SAFE_PATH="/usr/bin:/bin:/usr/sbin:/sbin"

REAL_GIT="$(command -v git)"

PASS_COUNT=0
FAIL_COUNT=0
FAILED_TESTS=()

# --- assertion helpers -------------------------------------------------
#
# Test functions always run inside a command-substitution subshell (see
# run_test below), so assertion failures use `exit 1` rather than `return 1`:
# `return` would only unwind the assert_* helper itself and let the
# calling test function keep running (masking the failure behind whatever
# the *last* assertion happens to do), whereas `exit` cleanly terminates
# just that subshell and is captured as the test's exit status.

fail() {
	echo "    FAIL: $*" >&2
	exit 1
}

assert_file_exists() {
	local path="$1" msg="${2:-file exists: ${1}}"
	if [[ ! -e "${path}" ]]; then
		fail "${msg} (missing: ${path})"
	fi
}

assert_symlink_to() {
	local link="$1" expected_target="$2"
	if [[ ! -L "${link}" ]]; then
		fail "expected symlink at ${link}"
	fi
	local actual
	actual="$(readlink "${link}")"
	if [[ "${actual}" != "${expected_target}" ]]; then
		fail "symlink ${link} -> ${actual}, expected ${expected_target}"
	fi
}

assert_contains() {
	local haystack="$1" needle="$2" msg="${3:-expected output to contain '${2}'}"
	if [[ "${haystack}" != *"${needle}"* ]]; then
		fail "${msg}"
	fi
}

assert_not_contains() {
	local haystack="$1" needle="$2" msg="${3:-expected output not to contain '${2}'}"
	if [[ "${haystack}" == *"${needle}"* ]]; then
		fail "${msg}"
	fi
}

assert_equals() {
	local actual="$1" expected="$2" msg="${3:-expected '${2}', got '${1}'}"
	if [[ "${actual}" != "${expected}" ]]; then
		fail "${msg}"
	fi
}

# --- test harness --------------------------------------------------------

# fresh_home NAME
# Creates (recreating if needed) an isolated $HOME for a test, under the
# repo's own tests/.scratch directory (never /tmp).
fresh_home() {
	local name="$1"
	local home_dir="${SCRATCH_ROOT}/${name}"
	rm -rf -- "${home_dir}"
	mkdir -p "${home_dir}"
	echo "${home_dir}"
}

# run_install HOME_DIR [EXTRA_ENV_ASSIGNMENT...]
# Runs the real install script against an isolated HOME with mocked PATH.
# Extra args are "NAME=value" pairs layered on top of the base environment
# (e.g. to unset/set Atuin secrets or trigger a mock failure).
run_install() {
	local home_dir="$1"
	shift
	env -i \
		HOME="${home_dir}" \
		PATH="${MOCK_BIN}:${SAFE_PATH}" \
		CODESPACES=1 \
		REAL_GIT="${REAL_GIT}" \
		LOGNAME="${LOGNAME:-tester}" \
		"$@" \
		bash "${REPO_DIR}/install" 2>&1
}

run_test() {
	local test_name="$1"
	echo "-- ${test_name}"
	local output
	local status=0
	output="$("${test_name}" 2>&1)" || status=$?
	if [[ ${status} -eq 0 ]]; then
		echo "${output}" | sed 's/^/    /'
		echo "  PASS"
		PASS_COUNT=$((PASS_COUNT + 1))
	else
		echo "${output}" | sed 's/^/    /'
		echo "  FAIL"
		FAIL_COUNT=$((FAIL_COUNT + 1))
		FAILED_TESTS+=("${test_name}")
	fi
}

# --- tests -----------------------------------------------------------------

test_missing_atuin_secrets_warns_and_continues() {
	local home_dir output status=0
	home_dir="$(fresh_home "missing-atuin-secrets")"
	output="$(run_install "${home_dir}")" || status=$?

	assert_equals "${status}" "0" "install should exit 0 even when Atuin secrets are absent"
	assert_contains "${output}" "skipping Atuin login; missing env var(s): ATUIN_USERNAME ATUIN_KEY ATUIN_PASSWORD"
	assert_not_contains "${output}" "unbound variable" "install must not fail with an unbound variable error"
	assert_contains "${output}" "Install complete; all steps succeeded."
}

test_partial_atuin_secrets_reports_only_missing_vars() {
	local home_dir output status=0
	home_dir="$(fresh_home "partial-atuin-secrets")"
	output="$(run_install "${home_dir}" ATUIN_USERNAME=test-user)" || status=$?

	assert_equals "${status}" "0"
	assert_contains "${output}" "skipping Atuin login; missing env var(s): ATUIN_KEY ATUIN_PASSWORD"
	assert_not_contains "${output}" "test-user" "secret/username values must never be printed"
}

test_atuin_network_failure_does_not_abort_install() {
	# Regression test for the original bug: a failed Atuin download must not
	# prevent agent config or personal AI skills from being installed.
	local home_dir output status=0
	home_dir="$(fresh_home "atuin-network-failure")"
	output="$(run_install "${home_dir}" MOCK_CURL_ATUIN_FAIL=1)" || status=$?

	assert_equals "${status}" "0" "install must exit 0 even if the Atuin download fails"
	assert_contains "${output}" "optional step failed (exit 1): Atuin install"
	assert_contains "${output}" "Copied Copilot agent configuration"
	assert_contains "${output}" "mock-ai-skills] install ran"
	assert_file_exists "${home_dir}/.copilot/ai-skills/.marker/personal-ai-skills-installed"
}

test_optional_failures_continue_to_later_steps() {
	# gh-stack extension install fails; every later optional step (aliases,
	# skill, caveman, copilot plugin, personal ai-skills) must still run.
	# (Agent skills also uses `gh extension install` internally, so the same
	# mock flag causes it to fail too -- exercising two independent
	# failures continuing through to the end in a single run.)
	local home_dir output status=0
	home_dir="$(fresh_home "optional-failure-continuation")"
	output="$(run_install "${home_dir}" MOCK_GH_EXTENSION_FAIL=1)" || status=$?

	assert_equals "${status}" "0"
	assert_contains "${output}" "optional step failed (exit 1): Agent skills"
	assert_contains "${output}" "optional step failed (exit 1): gh-stack extension"
	assert_contains "${output}" "Optional step succeeded: gh-stack aliases"
	assert_contains "${output}" "Optional step succeeded: gh-stack skill"
	assert_contains "${output}" "Optional step succeeded: Caveman skills"
	assert_contains "${output}" "Optional step succeeded: Copilot coder plugin"
	assert_contains "${output}" "Optional step succeeded: Personal AI skills sync"
	assert_contains "${output}" "Optional step succeeded: Personal AI skills install"
	assert_contains "${output}" "Install finished with 2 optional step(s) needing attention"
	assert_contains "${output}" "gh-stack extension (exit 1)"
}

test_core_dotfile_links_are_created() {
	local home_dir output status=0
	home_dir="$(fresh_home "core-links")"
	output="$(run_install "${home_dir}")" || status=$?

	assert_equals "${status}" "0"
	assert_symlink_to "${home_dir}/.tmux.conf" "${REPO_DIR}/.tmux.conf"
	assert_symlink_to "${home_dir}/.local/bin/workspace.sh" "${REPO_DIR}/workspace.sh"
	assert_symlink_to "${home_dir}/.copilot/copilot-instructions.md" "${REPO_DIR}/.copilot/copilot-instructions.md"
	assert_symlink_to "${home_dir}/.copilot/mcp-config.json" "${REPO_DIR}/.copilot/mcp-config.json"
	assert_symlink_to "${home_dir}/.zshrc" "${REPO_DIR}/.zshrc"

	if ! grep -q "autoSetupRemote" "${home_dir}/.gitconfig" 2>/dev/null; then
		fail "expected autoSetupRemote setting in ${home_dir}/.gitconfig"
	fi
}

test_personal_ai_skills_install_last_and_present() {
	local home_dir output status=0
	home_dir="$(fresh_home "personal-skills-ordering")"
	output="$(run_install "${home_dir}")" || status=$?

	assert_equals "${status}" "0"
	assert_file_exists "${home_dir}/.copilot/ai-skills/.marker/personal-ai-skills-installed"

	# Ordering: the personal AI skills steps must be the last two "Optional
	# step:" lines emitted, after every other Codespaces optional integration.
	local last_two total
	total="$(echo "${output}" | grep -c '^\[dotfiles\] Optional step: ')"
	last_two="$(echo "${output}" | grep '^\[dotfiles\] Optional step: ' | tail -n 2)"
	assert_contains "${last_two}" "Optional step: Personal AI skills sync"
	assert_contains "${last_two}" "Optional step: Personal AI skills install"
	if [[ "${total}" -lt 2 ]]; then
		fail "expected several optional steps to have run, saw ${total}"
	fi
}

test_second_run_is_idempotent() {
	local home_dir first_output second_output first_status=0 second_status=0
	home_dir="$(fresh_home "idempotent-rerun")"

	first_output="$(run_install "${home_dir}")" || first_status=$?
	second_output="$(run_install "${home_dir}")" || second_status=$?

	assert_equals "${first_status}" "0" "first run should succeed"
	assert_equals "${second_status}" "0" "second run should succeed"
	assert_contains "${first_output}" "Install complete; all steps succeeded."
	assert_contains "${second_output}" "Install complete; all steps succeeded."
	assert_not_contains "${second_output}" "unbound variable"

	# Core links and personal skills marker must still be correct/present.
	assert_symlink_to "${home_dir}/.tmux.conf" "${REPO_DIR}/.tmux.conf"
	assert_file_exists "${home_dir}/.copilot/ai-skills/.marker/personal-ai-skills-installed"

	# Second run should sync via `git pull` (repo already present), not a
	# fresh clone.
	assert_contains "${second_output}" "Syncing personal AI skills"
	assert_contains "${second_output}" "mock-git] pull (mocked, no-op)"
}

# --- run all tests -----------------------------------------------------

mkdir -p "${SCRATCH_ROOT}"

run_test test_missing_atuin_secrets_warns_and_continues
run_test test_partial_atuin_secrets_reports_only_missing_vars
run_test test_atuin_network_failure_does_not_abort_install
run_test test_optional_failures_continue_to_later_steps
run_test test_core_dotfile_links_are_created
run_test test_personal_ai_skills_install_last_and_present
run_test test_second_run_is_idempotent

rm -rf -- "${SCRATCH_ROOT}"

echo ""
echo "================================"
echo "Results: ${PASS_COUNT} passed, ${FAIL_COUNT} failed"
if [[ ${FAIL_COUNT} -gt 0 ]]; then
	echo "Failed tests:"
	for t in "${FAILED_TESTS[@]}"; do
		echo "  - ${t}"
	done
	exit 1
fi
exit 0
