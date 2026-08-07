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

test_atuin_install_is_noninteractive() {
	local home_dir output status=0
	home_dir="$(fresh_home "atuin-non-interactive")"
	output="$(run_install "${home_dir}")" || status=$?

	assert_equals "${status}" "0"
	assert_file_exists "${home_dir}/.atuin/non-interactive-install"
	assert_not_contains "${output}" "missing --non-interactive"
	assert_contains "${output}" "Optional step succeeded: Atuin install"
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

test_existing_atuin_outside_path_is_reused() {
	local home_dir output status=0
	home_dir="$(fresh_home "existing-atuin-outside-path")"
	mkdir -p "${home_dir}/.atuin/bin"
	cat > "${home_dir}/.atuin/bin/atuin" <<'ATUIN_EOF'
#!/usr/bin/env bash
exit 0
ATUIN_EOF
	chmod +x "${home_dir}/.atuin/bin/atuin"
	cat > "${home_dir}/.atuin/bin/env" <<ATUIN_ENV_EOF
export PATH="${home_dir}/.atuin/bin:\${PATH}"
ATUIN_ENV_EOF

	output="$(run_install "${home_dir}" MOCK_CURL_ATUIN_FAIL=1)" || status=$?

	assert_equals "${status}" "0"
	assert_contains "${output}" "Atuin already installed"
	assert_not_contains "${output}" "optional step failed (exit 1): Atuin install"
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

test_gh_stack_skill_install_is_noninteractive_and_global() {
	local home_dir output status=0
	home_dir="$(fresh_home "gh-stack-skill-flags")"
	output="$(run_install "${home_dir}")" || status=$?

	assert_equals "${status}" "0"
	assert_contains "${output}" "[mock-npx] skills add github/gh-stack --yes --global"
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

test_personal_ai_skills_clone_does_not_need_gh_auth() {
	local home_dir output status=0
	home_dir="$(fresh_home "personal-skills-without-gh-auth")"
	output="$(run_install "${home_dir}" MOCK_GH_CLONE_FAIL=1)" || status=$?

	assert_equals "${status}" "0"
	assert_file_exists "${home_dir}/.copilot/ai-skills/.marker/personal-ai-skills-installed"
	assert_contains "${output}" "Optional step succeeded: Personal AI skills sync"
	assert_contains "${output}" "Optional step succeeded: Personal AI skills install"
	assert_not_contains "${output}" "simulated 'repo clone' failure"
}

test_plugin_update_failure_preserves_existing_install() {
	local home_dir plugin_dir output status=0
	home_dir="$(fresh_home "plugin-update-preserves-existing")"
	plugin_dir="${home_dir}/.copilot/plugins/copilot-coder-plugin"
	mkdir -p "${plugin_dir}/.git"
	echo "keep-me" > "${plugin_dir}/sentinel"

	output="$(
		env -i \
			HOME="${home_dir}" \
			PATH="${MOCK_BIN}:${SAFE_PATH}" \
			REAL_GIT="${REAL_GIT}" \
			MOCK_GIT_PULL_FAIL=1 \
			bash "${REPO_DIR}/install-copilot-plugin" 2>&1
	)" || status=$?

	assert_equals "${status}" "1"
	assert_contains "${output}" "Update failed; keeping existing plugin"
	assert_file_exists "${plugin_dir}/sentinel"
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

test_grepika_skill_adaptation_preserves_paths_and_adapts_commands() {
	# Focused unit test for adapt_skill_for_copilot(), sourced directly (no
	# network, no full install) so it runs fast and in isolation. This is
	# the regression test for the /index sed rule that used to corrupt
	# file paths like src/index.ts (see be2ded/613fbf1 history): it proves
	# standalone slash-command references adapt while path-shaped
	# substrings are left untouched.
	local scratch_dir sample_file content status=0

	scratch_dir="$(fresh_home "grepika-adapt-unit")"
	mkdir -p "${scratch_dir}"
	sample_file="${scratch_dir}/sample.md"
	cat > "${sample_file}" <<'SAMPLE_EOF'
Run /index to build the index, then /index-status to check progress.
Call /apply-pattern once you /study the results.
Uses the mcp__grepika__search tool under the hood.
Blueprints live at ~/.claude/blueprints/example.
Invoke with $ARGUMENTS.

See src/index.ts and docs/index-status.md for the reference implementation;
these file paths must not be rewritten.
Also check lib/apply-pattern.rb and spec/study.rb, and `/index` in backticks.
SAMPLE_EOF

	(
		# shellcheck disable=SC1090
		source "${REPO_DIR}/install-grepika-skills"
		adapt_skill_for_copilot "${sample_file}"
	) || status=$?
	assert_equals "${status}" "0" "sourcing install-grepika-skills and adapting must not error"

	content="$(cat "${sample_file}")"

	# Slash-command references (standalone tokens) must be adapted.
	assert_contains "${content}" "Run grepika-index to build the index" "bare /index command should adapt"
	assert_contains "${content}" "then index-status to check progress" "/index-status command should adapt"
	assert_contains "${content}" "Call apply-pattern once you study the results" "/apply-pattern and /study commands should adapt"
	assert_contains "${content}" '`grepika-index` in backticks' "backticked /index command should adapt"
	assert_not_contains "${content}" "mcp__grepika__search" "Claude-only mcp tool name must be adapted"
	assert_contains "${content}" "grepika-search tool" "mcp tool name should map to grepika-search"
	assert_not_contains "${content}" ".claude/blueprints" "Claude blueprint path must be adapted"
	assert_contains "${content}" "~/.copilot/blueprints/example" "blueprint path should map to ~/.copilot/blueprints"
	assert_not_contains "${content}" '$ARGUMENTS' "literal \$ARGUMENTS placeholder must be adapted"

	# File paths that merely contain a slash-command substring must be
	# left byte-for-byte unchanged -- this is the regression case.
	assert_contains "${content}" "See src/index.ts and docs/index-status.md for the reference implementation" "file paths must survive adaptation unchanged"
	assert_contains "${content}" "Also check lib/apply-pattern.rb and spec/study.rb" "file paths must survive adaptation unchanged"
	assert_not_contains "${content}" "srcgrepika-index.ts" "src/index.ts must never be corrupted into srcgrepika-index.ts"
	assert_not_contains "${content}" "docsindex-status.md" "docs/index-status.md must never be corrupted"
	assert_not_contains "${content}" "libapply-pattern.rb" "lib/apply-pattern.rb must never be corrupted"
	assert_not_contains "${content}" "specstudy.rb" "spec/study.rb must never be corrupted"
}

test_grepika_skills_install_runs_after_other_installers_before_personal_skills() {
	# Integration test: exercises the real install-grepika-skills script
	# end to end (mocked network clone) as part of the full install, and
	# verifies both ordering (item 2: after other external installers,
	# before personal AI skills so they stay authoritative) and that the
	# installed skill content was actually adapted for Copilot, not just
	# copied verbatim.
	local home_dir output status=0
	home_dir="$(fresh_home "grepika-ordering")"
	output="$(run_install "${home_dir}")" || status=$?

	assert_equals "${status}" "0"
	assert_contains "${output}" "Optional step succeeded: grepika skills"

	local skill_file="${home_dir}/.copilot/skills/example-grepika-skill/SKILL.md"
	assert_file_exists "${skill_file}"
	local skill_content
	skill_content="$(cat "${skill_file}")"
	assert_not_contains "${skill_content}" "mcp__grepika__" "installed skill must be adapted, not raw upstream content"
	assert_contains "${skill_content}" "src/index.ts and docs/index-status.md" "installed skill file paths must remain unchanged"

	# Ordering: grepika skills must run after the other Codespaces optional
	# installers, but before personal AI skills sync/install.
	local step_order
	step_order="$(echo "${output}" | grep '^\[dotfiles\] Optional step: ')"
	local grepika_line copilot_plugin_line personal_sync_line
	grepika_line="$(echo "${step_order}" | grep -n 'grepika skills' | cut -d: -f1)"
	copilot_plugin_line="$(echo "${step_order}" | grep -n 'Copilot coder plugin' | cut -d: -f1)"
	personal_sync_line="$(echo "${step_order}" | grep -n 'Personal AI skills sync' | cut -d: -f1)"

	if [[ "${grepika_line}" -le "${copilot_plugin_line}" ]]; then
		fail "grepika skills must run after Copilot coder plugin (grepika at line ${grepika_line}, plugin at ${copilot_plugin_line})"
	fi
	if [[ "${grepika_line}" -ge "${personal_sync_line}" ]]; then
		fail "grepika skills must run before Personal AI skills sync (grepika at line ${grepika_line}, personal sync at ${personal_sync_line})"
	fi
}

test_grepika_skills_clone_does_not_need_gh_auth() {
	# agentika-labs/grepika is public: install-grepika-skills clones it
	# with plain `git clone` over HTTPS, never `gh`, so it must succeed
	# even when GitHub CLI auth/clone is broken (item 6/7).
	local home_dir output status=0
	home_dir="$(fresh_home "grepika-without-gh-auth")"
	output="$(run_install "${home_dir}" MOCK_GH_CLONE_FAIL=1 MOCK_GH_EXTENSION_FAIL=1)" || status=$?

	assert_equals "${status}" "0"
	assert_contains "${output}" "Optional step succeeded: grepika skills"
	assert_file_exists "${home_dir}/.copilot/skills/example-grepika-skill/SKILL.md"
	assert_not_contains "${output}" "optional step failed (exit 1): grepika skills" "grepika skills step itself must not be affected by unrelated gh auth/extension failures"
}

# --- run all tests -----------------------------------------------------

mkdir -p "${SCRATCH_ROOT}"

run_test test_missing_atuin_secrets_warns_and_continues
run_test test_atuin_install_is_noninteractive
run_test test_partial_atuin_secrets_reports_only_missing_vars
run_test test_atuin_network_failure_does_not_abort_install
run_test test_existing_atuin_outside_path_is_reused
run_test test_optional_failures_continue_to_later_steps
run_test test_gh_stack_skill_install_is_noninteractive_and_global
run_test test_core_dotfile_links_are_created
run_test test_personal_ai_skills_install_last_and_present
run_test test_personal_ai_skills_clone_does_not_need_gh_auth
run_test test_plugin_update_failure_preserves_existing_install
run_test test_second_run_is_idempotent
run_test test_grepika_skill_adaptation_preserves_paths_and_adapts_commands
run_test test_grepika_skills_install_runs_after_other_installers_before_personal_skills
run_test test_grepika_skills_clone_does_not_need_gh_auth

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
