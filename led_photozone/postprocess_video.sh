#!/usr/bin/env bash
# Обработка ролика 16:9 (с полями) → две стены угловой LED-фотозоны.
# Использование: postprocess_video.sh input_16x9.mp4 out_prefix
#  1) вырезаем центр 3:2 (поля по бокам добавлялись pad16x9.py)
#  2) левая/правая половины → 1080x1440 каждая (стены 1,5 x 2,0 м)
#  3) превью-развёртка обеих стен
set -euo pipefail
in="$1"; out="$2"
IFS=, read W H < <(ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0 "$in")
CW=$(( (W * 1620 / 1920) / 2 * 2 ))     # картинка занимала 1620 из 1920 px по ширине (pad16x9.py)
X=$(( (W - CW) / 2 ))
HALF=$(( CW / 2 ))
enc="-c:v libx264 -preset slow -crf 15 -pix_fmt yuv420p -movflags +faststart -an"
ffmpeg -loglevel error -y -i "$in" -filter_complex \
 "[0:v]crop=${CW}:${H}:${X}:0,split=3[a][b][c];\
  [a]crop=${HALF}:${H}:0:0,scale=1080:1440:flags=lanczos[l];\
  [b]crop=${HALF}:${H}:${HALF}:0,scale=1080:1440:flags=lanczos[r];\
  [c]scale=2160:1440:flags=lanczos[w]" \
 -map "[l]" $enc "${out}_wall_LEFT_1080x1440.mp4" \
 -map "[r]" $enc "${out}_wall_RIGHT_1080x1440.mp4" \
 -map "[w]" $enc "${out}_walls_2160x1440.mp4"
echo "ok ${out} (src ${W}x${H}, crop ${CW}x${H}+${X})"
