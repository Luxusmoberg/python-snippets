#!/bin/bash
# Daily grind runner — invoked by launchd each day.
# Uses the login shell's PATH so `gh` and `git` resolve correctly.
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
cd "$HOME/Developer/daily-grind" || exit 1
exec /usr/bin/python3 grind.py >> "$HOME/Developer/daily-grind/.grind-out.log" 2>&1
