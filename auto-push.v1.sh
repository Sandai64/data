#!/usr/bin/env bash
# -*- coding: utf-8 -*-

abort_script () {
  echo "An error occured in the script, aborting."
  exit 1
}

# Abort if Python is not installed.
if ! command -v python3 &> /dev/null
then
  echo "Python 3 could not be found on this system."
  echo "Please install Python 3 with the dependencies listed in 'requirements.txt'."
  echo "Aborting."
  exit 2
fi


if [ -f "./tools/v1/_.lock" ]; then
  # We can't push the repo if the generator is currently running
  echo "Lock file present, generator already running, aborting."
  exit 0
fi

cd ./tools/v1/ || abort_script
./generate.py

date_time=$(date '+%d/%m/%Y %H:%M:%S')

echo "Running batch git commands (add, commit, push-force)"
cd ../.. || exit
git add .
git commit -am "Auto-Push: update ${date_time}"

git push --force
echo "End script."
