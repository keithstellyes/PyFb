VIDEOS_URL=$1
youtube-dl --get-id --get-title --get-thumbnail "$VIDEOS_URL" > videos.txt