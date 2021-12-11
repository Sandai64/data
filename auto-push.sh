#!/usr/bin/env bash
# -*- coding: utf-8 -*-

if [ -f "./tools/_generator_lock" ]; then
  # We can't push the repo if the generator is currently running
  echo "Lock file present, generator already running, aborting."
  exit 0
fi

date_time=$(date '+%d/%m/%Y %H:%M:%S')

echo "Running batch git commands (add, commit, push-force)"

git add .
git commit -am "Auto-Push: update ${date_time}"
git push --force

echo "End script."
