#!/bin/bash
# Evening auto-push script for TSB
# Pushes current draft branch to keep Moonglade in sync
#
# CRITICAL: Git remote must be set to use github-zelda host for SSH audit trail
# Verify: git remote -v should show github-zelda:Inturious-Labs/sundayblender.git

cd /Users/zire/matrix/zire/sundayblender

# Check if we're in a git repo
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "$(date): ERROR - Not in a git repository" >> ~/matrix/zire/sundayblender/scripts/push.log
    exit 1
fi

# Get current branch name
BRANCH=$(git rev-parse --abbrev-ref HEAD)

# Only push if there are commits to push
if git diff --quiet HEAD@{upstream} HEAD 2>/dev/null; then
    echo "$(date): No changes to push on branch $BRANCH" >> ~/matrix/zire/sundayblender/scripts/push.log
    exit 0
fi

# Push current branch
if git push origin $BRANCH; then
    echo "$(date): Successfully pushed branch $BRANCH" >> ~/matrix/zire/sundayblender/scripts/push.log
else
    echo "$(date): FAILED to push branch $BRANCH" >> ~/matrix/zire/sundayblender/scripts/push.log
    exit 1
fi