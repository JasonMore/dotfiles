---
name: merge-from-main
description: steps to take every time requested a merge from main for branch or PR
---

1. Look at the pull request if provided
1. `git pull origin main`
2. resolve conflicts
3. for every github-ui package that is in the PR, run 
   1. tsc
   2. lint
   3. test
4. Fix any failure, run step 3 again
5. DO NOT COMMIT THE CHANGES OR PUSH TO MAIN
6. Once all checks are passing, let user know
