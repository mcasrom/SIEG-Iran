#!/bin/bash
# SIEG-Iran — Git sync
# Cron: 45 * * * * /bin/bash /home/dietpi/SIEG-Iran/update_iran.sh >> /home/dietpi/iran_cron.log 2>&1
LOCK="/tmp/sieg_iran.lock"
DIR="/home/dietpi/SIEG-Iran"

[ -f "$LOCK" ] && exit 0
echo $$ > "$LOCK"
trap "rm -f $LOCK" EXIT

cd "$DIR" || exit 1
/usr/bin/python3 iran_scanner.py

git add data/live/
if ! git diff --cached --quiet; then
    git commit -m "auto: iran scan $(date '+%Y-%m-%d %H:%M')"
    git push origin main
fi
