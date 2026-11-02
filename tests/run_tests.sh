#!/usr/bin/env bash
# Behavioral tests for the dotfiles installer.
#
# These tests run the real `install` script (and its helper scripts) end to
# end, but with:
#   - an isolated, throwaway $HOME under tests/.scratch/ (never /tmp, never
#     the real $HOME)
#   - CODESPACES=1 by default, with an empty value for local install tests
#   - uname reports Linux so local tests cannot load a macOS launch agent
#   - a PATH pointing at tests/mocks/bin so installers and account commands
#     never touch the real network, system shell config, or GitHub account
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
		bash -c 'uname() { case "${1:-}" in -m) echo "${MOCK_UNAME_ARCH:-x86_64}" ;; *) echo "${MOCK_UNAME_OS:-Linux}" ;; esac; }; export -f uname; bash "$1"' \
		bash "${REPO_DIR}/install" 2>&1
}

run_mergiraf_install() {
	local home_dir="$1"
	shift
	env -i \
		HOME="${home_dir}" \
		PATH="${home_dir}/.local/bin:${MOCK_BIN}:${SAFE_PATH}" \
		REAL_GIT="${REAL_GIT}" \
		"$@" \
		bash -c 'uname() { case "${1:-}" in -m) echo "${MOCK_UNAME_ARCH:-x86_64}" ;; *) echo "${MOCK_UNAME_OS:-Linux}" ;; esac; }; export -f uname; bash "$1"' \
		bash "${REPO_DIR}/install-mergiraf" 2>&1
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
	# skill, copilot plugin, i-have-adhd, personal ai-skills) must still run.
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
	assert_contains "${output}" "Optional step succeeded: Copilot coder plugin"
	assert_contains "${output}" "Optional step succeeded: i-have-adhd skill"
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

test_i_have_adhd_skill_install_is_noninteractive_and_global() {
	local home_dir output status=0
	home_dir="$(fresh_home "i-have-adhd-skill-flags")"
	output="$(run_install "${home_dir}")" || status=$?

	assert_equals "${status}" "0"
	assert_contains "${output}" "[mock-npx] skills add ayghri/i-have-adhd --agent github-copilot --global --yes"
	assert_contains "${output}" "Optional step succeeded: i-have-adhd skill"
}

test_impeccable_installs_to_agents_skills_and_reruns() {
	local home_dir output status=0
	home_dir="$(fresh_home "impeccable-skills")"
	output="$(run_install "${home_dir}")" || status=$?

	assert_equals "${status}" "0"
	assert_contains "${output}" "[mock-npx] --yes impeccable install --providers=codex --scope=global --no-hooks --yes"
	assert_contains "${output}" "Optional step succeeded: Impeccable skills"
	assert_file_exists "${home_dir}/.agents/skills/impeccable/SKILL.md"

	output="$(run_install "${home_dir}")" || status=$?
	assert_equals "${status}" "0"
	assert_contains "${output}" "Optional step succeeded: Impeccable skills"
	assert_file_exists "${home_dir}/.agents/skills/impeccable/SKILL.md"
}

test_impeccable_failure_does_not_abort_install() {
	local home_dir output status=0
	home_dir="$(fresh_home "impeccable-failure")"
	output="$(run_install "${home_dir}" MOCK_IMPECCABLE_FAIL=1)" || status=$?

	assert_equals "${status}" "0"
	assert_contains "${output}" "optional step failed (exit 1): Impeccable skills"
	assert_contains "${output}" "Optional step succeeded: gh-stack skill"
	assert_contains "${output}" "Optional step succeeded: Personal AI skills install"
	assert_contains "${output}" "Install finished with 1 optional step(s) needing attention"
}

test_impeccable_missing_skill_is_reported() {
	local home_dir output status=0
	home_dir="$(fresh_home "impeccable-missing-skill")"
	output="$(run_install "${home_dir}" MOCK_IMPECCABLE_MISSING_SKILL=1)" || status=$?

	assert_equals "${status}" "0"
	assert_contains "${output}" "Error: Impeccable skill not found at ${home_dir}/.agents/skills/impeccable/SKILL.md"
	assert_contains "${output}" "optional step failed (exit 1): Impeccable skills"
	assert_contains "${output}" "Optional step succeeded: Personal AI skills install"
}

test_local_install_skips_impeccable() {
	local home_dir output status=0
	home_dir="$(fresh_home "local-no-impeccable")"
	output="$(run_install "${home_dir}" CODESPACES=)" || status=$?

	assert_equals "${status}" "0"
	assert_not_contains "${output}" "impeccable install"
	assert_not_contains "${output}" "Optional step: Impeccable skills"
	if [[ -e "${home_dir}/.agents/skills/impeccable" ]]; then
		fail "local install must not install Impeccable"
	fi
}

test_mergiraf_installs_in_codespaces_and_reruns() {
	local architecture expected_arch home_dir output status
	for architecture in x86_64 aarch64 arm64; do
		expected_arch="${architecture}"
		if [[ "${architecture}" == "arm64" ]]; then
			expected_arch="aarch64"
		fi
		status=0
		home_dir="$(fresh_home "mergiraf-codespaces-${architecture}")"
		output="$(run_install "${home_dir}" "MOCK_UNAME_ARCH=${architecture}")" || status=$?

		assert_equals "${status}" "0"
		assert_contains "${output}" "[mock-curl] downloaded Mergiraf for ${expected_arch}"
		assert_contains "${output}" "Optional step succeeded: Mergiraf"
		assert_file_exists "${home_dir}/.local/bin/mergiraf"
		assert_equals "$("${REAL_GIT}" config --file "${home_dir}/.gitconfig" --get merge.default)" "mergiraf"
		assert_equals "$("${REAL_GIT}" config --file "${home_dir}/.gitconfig" --get merge.conflictStyle)" "diff3"
		assert_contains "$("${REAL_GIT}" config --file "${home_dir}/.gitconfig" --get merge.mergiraf.driver)" \
			"merge --git %O %A %B -s %S -x %X -y %Y -p %P -l %L"

		status=0
		output="$(run_install "${home_dir}" "MOCK_UNAME_ARCH=${architecture}" MOCK_CURL_MERGIRAF_FAIL=1)" || status=$?
		assert_equals "${status}" "0"
		assert_contains "${output}" "Mergiraf already installed: ${home_dir}/.local/bin/mergiraf"
		assert_contains "${output}" "Optional step succeeded: Mergiraf"
		assert_not_contains "${output}" "simulated Mergiraf download failure"
	done
}

test_mergiraf_installs_for_local_linux() {
	local home_dir output status=0
	home_dir="$(fresh_home "mergiraf-local-linux")"
	output="$(run_install "${home_dir}" CODESPACES=)" || status=$?

	assert_equals "${status}" "0"
	assert_contains "${output}" "Optional step succeeded: Mergiraf"
	assert_file_exists "${home_dir}/.local/bin/mergiraf"
}

test_mergiraf_uses_homebrew_on_macos() {
	local home_dir output status=0
	home_dir="$(fresh_home "mergiraf-macos")"
	output="$(run_mergiraf_install "${home_dir}" MOCK_UNAME_OS=Darwin)" || status=$?

	assert_equals "${status}" "0"
	assert_contains "${output}" "[mock-brew] installed mergiraf"
	assert_contains "${output}" "Mergiraf is configured as the default Git merge driver"
	assert_equals "$("${REAL_GIT}" config --file "${home_dir}/.gitconfig" --get merge.default)" "mergiraf"
}

test_mergiraf_preserves_existing_git_settings() {
	local home_dir attributes output status=0 existing_driver
	home_dir="$(fresh_home "mergiraf-existing-settings")"
	attributes="${home_dir}/custom-attributes"
	existing_driver="mergiraf merge --git %O %A %B --compact"
	printf '*.special merge=binary\n' > "${attributes}"
	"${REAL_GIT}" config --file "${home_dir}/.gitconfig" core.attributesFile "${attributes}"
	"${REAL_GIT}" config --file "${home_dir}/.gitconfig" merge.conflictStyle zdiff3
	"${REAL_GIT}" config --file "${home_dir}/.gitconfig" merge.mergiraf.driver "${existing_driver}"

	output="$(run_install "${home_dir}")" || status=$?

	assert_equals "${status}" "0"
	assert_contains "${output}" "Optional step succeeded: Mergiraf"
	assert_equals "$(cat "${attributes}")" "*.special merge=binary"
	assert_equals "$("${REAL_GIT}" config --file "${home_dir}/.gitconfig" --get core.attributesFile)" "${attributes}"
	assert_equals "$("${REAL_GIT}" config --file "${home_dir}/.gitconfig" --get merge.conflictStyle)" "zdiff3"
	assert_equals "$("${REAL_GIT}" config --file "${home_dir}/.gitconfig" --get merge.mergiraf.driver)" "${existing_driver}"
	assert_equals "$("${REAL_GIT}" config --file "${home_dir}/.gitconfig" --get merge.default)" "mergiraf"
}

test_mergiraf_preserves_existing_default_and_continues() {
	local home_dir output status=0
	home_dir="$(fresh_home "mergiraf-existing-default")"
	"${REAL_GIT}" config --file "${home_dir}/.gitconfig" merge.default custom-driver

	output="$(run_install "${home_dir}")" || status=$?

	assert_equals "${status}" "0"
	assert_contains "${output}" "existing merge.default 'custom-driver' was not changed"
	assert_contains "${output}" "optional step failed (exit 1): Mergiraf"
	assert_contains "${output}" "Optional step succeeded: Personal AI skills install"
	assert_equals "$("${REAL_GIT}" config --file "${home_dir}/.gitconfig" --get merge.default)" "custom-driver"
}

test_mergiraf_does_not_enable_an_empty_existing_driver() {
	local home_dir output status=0
	home_dir="$(fresh_home "mergiraf-empty-driver")"
	"${REAL_GIT}" config --file "${home_dir}/.gitconfig" merge.mergiraf.driver ""

	output="$(run_install "${home_dir}")" || status=$?

	assert_equals "${status}" "0"
	assert_contains "${output}" "existing merge.mergiraf.driver is empty"
	assert_contains "${output}" "optional step failed (exit 1): Mergiraf"
	assert_contains "${output}" "Optional step succeeded: Personal AI skills install"
	if "${REAL_GIT}" config --file "${home_dir}/.gitconfig" --get merge.default >/dev/null; then
		fail "an empty Mergiraf driver must not become the default"
	fi
}

test_mergiraf_install_failures_do_not_enable_driver() {
	local failure home_dir output status
	for failure in MOCK_CURL_MERGIRAF_FAIL MOCK_MERGIRAF_CHECKSUM_FAIL; do
		status=0
		home_dir="$(fresh_home "mergiraf-failure-${failure}")"
		output="$(run_install "${home_dir}" "${failure}=1")" || status=$?

		assert_equals "${status}" "0"
		assert_contains "${output}" "optional step failed (exit 1): Mergiraf"
		assert_contains "${output}" "Optional step succeeded: Personal AI skills install"
		if [[ -e "${home_dir}/.local/bin/mergiraf" ]]; then
			fail "failed Mergiraf install must not leave an executable"
		fi
		if "${REAL_GIT}" config --file "${home_dir}/.gitconfig" --get merge.default >/dev/null; then
			fail "failed Mergiraf install must not enable the driver"
		fi
	done

	status=0
	home_dir="$(fresh_home "mergiraf-unsupported-arch")"
	output="$(run_install "${home_dir}" MOCK_UNAME_ARCH=unsupported)" || status=$?
	assert_equals "${status}" "0"
	assert_contains "${output}" "no configured Linux release for unsupported"
	assert_contains "${output}" "optional step failed (exit 1): Mergiraf"

	status=0
	home_dir="$(fresh_home "mergiraf-brew-failure")"
	output="$(run_mergiraf_install "${home_dir}" MOCK_UNAME_OS=Darwin MOCK_BREW_MERGIRAF_FAIL=1)" || status=$?
	assert_equals "${status}" "1"
	assert_contains "${output}" "simulated Mergiraf install failure"
	if [[ -e "${home_dir}/.gitconfig" ]]; then
		fail "failed Homebrew install must not change Git configuration"
	fi
}

test_mergiraf_driver_is_used_without_overriding_attributes() {
	local home_dir repo output status=0
	home_dir="$(fresh_home "mergiraf path 'quote' %O")"
	output="$(run_install "${home_dir}")" || status=$?
	assert_equals "${status}" "0"
	assert_contains "${output}" "Optional step succeeded: Mergiraf"

	repo="${home_dir}/merge-test"
	mkdir -p "${repo}"
	(
		export HOME="${home_dir}" REAL_GIT GIT_CONFIG_NOSYSTEM=1
		export PATH="${MOCK_BIN}:${SAFE_PATH}"
		"${REAL_GIT}" -C "${repo}" init -q -b main
		"${REAL_GIT}" -C "${repo}" config user.name "Merge Test"
		"${REAL_GIT}" -C "${repo}" config user.email "merge-test@example.invalid"
		printf 'override.txt merge=binary\n' > "${repo}/.gitattributes"
		printf 'base\n' > "${repo}/conflict.txt"
		printf 'base\n' > "${repo}/override.txt"
		"${REAL_GIT}" -C "${repo}" add .
		"${REAL_GIT}" -C "${repo}" -c commit.gpgsign=false commit -qm base
		"${REAL_GIT}" -C "${repo}" switch -qc other
		printf 'theirs\n' > "${repo}/conflict.txt"
		printf 'theirs\n' > "${repo}/override.txt"
		"${REAL_GIT}" -C "${repo}" add .
		"${REAL_GIT}" -C "${repo}" -c commit.gpgsign=false commit -qm theirs
		"${REAL_GIT}" -C "${repo}" switch -q main
		printf 'ours\n' > "${repo}/conflict.txt"
		printf 'ours\n' > "${repo}/override.txt"
		"${REAL_GIT}" -C "${repo}" add .
		"${REAL_GIT}" -C "${repo}" -c commit.gpgsign=false commit -qm ours
		status=0
		"${REAL_GIT}" -C "${repo}" merge other > "${home_dir}/merge-output" 2>&1 || status=$?
		assert_equals "${status}" "1"
	)

	assert_file_exists "${home_dir}/.mock-mergiraf-merges"
	assert_contains "$(cat "${home_dir}/.mock-mergiraf-merges")" "-p conflict.txt"
	assert_not_contains "$(cat "${home_dir}/.mock-mergiraf-merges")" "-p override.txt"
	assert_contains "$(cat "${home_dir}/merge-output")" "CONFLICT (content): Merge conflict in override.txt"
}

test_codespaces_zsh_finds_user_local_mergiraf() {
	local home_dir output status=0
	home_dir="$(fresh_home "mergiraf-zsh-path")"
	mkdir -p "${home_dir}/.local/bin"
	cp "${TESTS_DIR}/mocks/mergiraf" "${home_dir}/.local/bin/mergiraf"

	output="$(env -i HOME="${home_dir}" PATH="${SAFE_PATH}" CODESPACES=1 \
		zsh -fc 'source "$1" >/dev/null; source "$1" >/dev/null; print -r -- "$PATH"; whence -p mergiraf' \
		zsh "${REPO_DIR}/.zshrc" 2>&1)" || status=$?
	assert_equals "${status}" "0"
	assert_contains "${output}" "${home_dir}/.local/bin:${SAFE_PATH}"
	assert_contains "${output}" "${home_dir}/.local/bin/mergiraf"
	assert_not_contains "${output}" "${home_dir}/.local/bin:${home_dir}/.local/bin"
}

test_core_dotfile_links_are_created() {
	local home_dir output status=0
	home_dir="$(fresh_home "core-links")"
	output="$(run_install "${home_dir}")" || status=$?

	assert_equals "${status}" "0"
	assert_symlink_to "${home_dir}/.tmux.conf" "${REPO_DIR}/.tmux.conf"
	if [[ -e "${home_dir}/.local/bin/workspace.sh" || -L "${home_dir}/.local/bin/workspace.sh" ]]; then
		fail "Codespaces must not install the workspace helper"
	fi
	assert_contains "${output}" "Skipping workspace script in Codespaces"
	assert_symlink_to "${home_dir}/.copilot/copilot-instructions.md" "${REPO_DIR}/.copilot/copilot-instructions.md"
	assert_symlink_to "${home_dir}/.copilot/mcp-config.json" "${REPO_DIR}/.copilot/mcp-config.json"
	assert_symlink_to "${home_dir}/.zshrc" "${REPO_DIR}/.zshrc"
	assert_contains "$(cat "${home_dir}/.copilot/copilot-instructions.md")" "## ADHD output style (always on)"
	assert_contains "$(cat "${home_dir}/.copilot/copilot-instructions.md")" "## Generated artifacts"

	if ! grep -q "autoSetupRemote" "${home_dir}/.gitconfig" 2>/dev/null; then
		fail "expected autoSetupRemote setting in ${home_dir}/.gitconfig"
	fi
}

test_local_install_keeps_workspace_helper() {
	local home_dir output status=0
	home_dir="$(fresh_home "local-workspace")"
	output="$(run_install "${home_dir}" CODESPACES=)" || status=$?

	assert_equals "${status}" "0"
	assert_symlink_to "${home_dir}/.local/bin/workspace.sh" "${REPO_DIR}/workspace.sh"
	assert_contains "${output}" "Installing workspace script"
}

test_zsh_loads_workspace_only_locally() {
	local home_dir output status=0
	home_dir="$(fresh_home "zsh-workspace")"
	mkdir -p "${home_dir}/.local/bin"
	ln -s "${REPO_DIR}/workspace.sh" "${home_dir}/.local/bin/workspace.sh"

	output="$(env -i HOME="${home_dir}" PATH="${SAFE_PATH}" CODESPACES=1 \
		zsh -fc 'source "$1"; whence -w workspace' zsh "${REPO_DIR}/.zshrc" 2>&1)" || status=$?
	assert_equals "${status}" "1" "Codespaces must not load an existing workspace helper"
	assert_not_contains "${output}" "workspace: function"

	status=0
	output="$(env -i HOME="${home_dir}" PATH="${SAFE_PATH}" \
		zsh -fc 'source "$1"; whence -w workspace' zsh "${REPO_DIR}/.zshrc" 2>&1)" || status=$?
	assert_equals "${status}" "0"
	assert_contains "${output}" "workspace: function"
}

test_workspace_rejects_codespaces_before_changes() {
	local argument output status
	for argument in "" "test-branch" "--list" "--delete"; do
		status=0
		output="$(env -i PATH="${SAFE_PATH}" CODESPACES=1 \
			bash -c 'source "$1"; git() { echo "unexpected git call"; }; code() { echo "unexpected code call"; }; workspace "$2"' \
			bash "${REPO_DIR}/workspace.sh" "${argument}" 2>&1)" || status=$?
		assert_equals "${status}" "1"
		assert_contains "${output}" "workspace is disabled in Codespaces"
		assert_not_contains "${output}" "unexpected"
	done
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

# --- run all tests -----------------------------------------------------

mkdir -p "${SCRATCH_ROOT}"

run_test test_missing_atuin_secrets_warns_and_continues
run_test test_atuin_install_is_noninteractive
run_test test_partial_atuin_secrets_reports_only_missing_vars
run_test test_atuin_network_failure_does_not_abort_install
run_test test_existing_atuin_outside_path_is_reused
run_test test_optional_failures_continue_to_later_steps
run_test test_gh_stack_skill_install_is_noninteractive_and_global
run_test test_i_have_adhd_skill_install_is_noninteractive_and_global
run_test test_impeccable_installs_to_agents_skills_and_reruns
run_test test_impeccable_failure_does_not_abort_install
run_test test_impeccable_missing_skill_is_reported
run_test test_local_install_skips_impeccable
run_test test_mergiraf_installs_in_codespaces_and_reruns
run_test test_mergiraf_installs_for_local_linux
run_test test_mergiraf_uses_homebrew_on_macos
run_test test_mergiraf_preserves_existing_git_settings
run_test test_mergiraf_preserves_existing_default_and_continues
run_test test_mergiraf_does_not_enable_an_empty_existing_driver
run_test test_mergiraf_install_failures_do_not_enable_driver
run_test test_mergiraf_driver_is_used_without_overriding_attributes
run_test test_codespaces_zsh_finds_user_local_mergiraf
run_test test_core_dotfile_links_are_created
run_test test_local_install_keeps_workspace_helper
run_test test_zsh_loads_workspace_only_locally
run_test test_workspace_rejects_codespaces_before_changes
run_test test_personal_ai_skills_install_last_and_present
run_test test_personal_ai_skills_clone_does_not_need_gh_auth
run_test test_plugin_update_failure_preserves_existing_install
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
