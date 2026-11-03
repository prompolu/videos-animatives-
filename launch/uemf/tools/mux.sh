#!/bin/sh
# usage: tools/mux.sh <render_dir> <mix.wav> <out.mp4>
set -e
R=$1; printf "file '%s/s0.mp4'\nfile '%s/s1.mp4'\nfile '%s/s2.mp4'\n" "$R" "$R" "$R" > "$R/list.txt"
ffmpeg -v error -y -f concat -safe 0 -i "$R/list.txt" -i "$2" -map 0:v -map 1:a -c:v copy -c:a aac -b:a 320k -movflags +faststart -shortest "$3"
