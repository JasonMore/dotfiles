---
name: merge-from-main
description: steps to take every time requested a merge from main for branch or PR
license: MIT
author: JasonMore
tags: [git, merge, ci, testing]
version: 1.0.0
---

# Merge from Main Workflow

Follow these steps every time you need to merge from main for a branch or PR:

1. Look at the pull request if provided
2. `git pull origin main`
3. Resolve conflicts
4. For every github-ui package that is in the PR, run:
   1. tsc
   2. lint
   3. test
5. Fix any failure, run step 4 again
6. DO NOT COMMIT THE CHANGES OR PUSH TO MAIN
7. Once all local checks are passing, invoke the watch-ci skill to monitor the PR's CI/CD checks in the background
8. The watch-ci skill will notify when all CI checks complete (pass or fail)
