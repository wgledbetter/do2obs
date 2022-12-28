#!/bin/sh

jBackup="/home/wgledbetter/pCloudSync/journal/"
jPrefix=$jBackup
journals=(
  "3feb22/Export-Journal-3feb22/Export-Journal-3feb22/Journal.json"
  "3feb22/Export-Food-3feb22/Export-Food-3feb22/Food.json"
  "3feb22/Export-Dream-3feb22/Export-Dream-3feb22/Dream.json"
)
obsOut="/home/wgledbetter/notes/dayone-test/dayone-test/dayOne"

for j in "${journals[@]}"; do
  python main.py --dayOneFile="$jPrefix$j" --obsidianFolder="$obsOut"
done
