# Clear Writing Examples

Before/after pairs showing the rules in action.

## PR Description

**Before (wordy, grade 14):**

> This pull request implements comprehensive modifications to the authentication
> middleware in order to facilitate seamless integration with the newly introduced
> OAuth2 provider. Additionally, it incorporates significant refactoring of the
> session management functionality to ensure compatibility with the updated
> token refresh methodology. The aforementioned changes have been thoroughly
> validated through extensive unit and integration testing.

**After (clear, grade 6):**

> This PR updates the auth middleware to work with our new OAuth2 provider.
> It also refactors session management to handle the new token refresh flow.
> All changes have unit and integration tests.

---

## Issue Description

**Before:**

> We have been experiencing intermittent failures in the CI pipeline that
> appear to be predominantly caused by race conditions in the database
> connection pooling implementation. This is not an insignificant issue as
> it substantially impacts developer productivity due to the fact that
> engineers are required to repeatedly re-run their builds.

**After:**

> CI fails at random due to race conditions in the DB connection pool.
> This blocks developers who have to re-run builds each time it happens.

---

## Release Notes

**Before:**

> Version 2.4.0 introduces a comprehensive suite of enhancements to the
> application's performance characteristics. Users will observe significantly
> improved response times for API endpoints, particularly those that
> previously exhibited latency issues when processing large datasets.
> Additionally, this release incorporates memory optimization improvements
> that substantially reduce the application's resource footprint.

**After:**

> **v2.4.0**
>
> - API responses are 3x faster, especially for large datasets
> - Memory usage is down 40%
> - Fixed slow endpoints that caused timeouts under load

---

## Code Review Comment

**Before:**

> I would recommend that we consider implementing a caching mechanism
> at this particular juncture, as the current implementation necessitates
> a database query for each individual request, which could potentially
> result in performance degradation under high-traffic conditions.

**After:**

> Add a cache here. Right now every request hits the database.
> Under high traffic, this will be slow.

---

## Documentation

**Before:**

> In order to successfully configure the development environment, it is
> necessary to first install all prerequisite dependencies by executing
> the package manager's installation command. Subsequently, you will
> need to create a local configuration file by duplicating the example
> configuration template and modifying the relevant values to match
> your local development setup.

**After:**

> To set up your dev environment:
>
> 1. Install dependencies: `npm install`
> 2. Copy the config template: `cp .env.example .env`
> 3. Edit `.env` with your local settings

---

## Key Patterns

**Numbers over vague claims:**
- Bad: "significantly faster"
- Good: "3x faster" or "200ms faster"

**Lists over long paragraphs:**
- If you have three or more items, use a bullet list.

**Direct verbs over noun phrases:**
- Bad: "perform an investigation of"
- Good: "investigate"
- Bad: "make a determination about"
- Good: "decide"

**Short headings:**
- Bad: "Comprehensive Overview of Configuration Options"
- Good: "Config Options"
