.PHONY: check_remote playlists sync clean_local clean_remote

check_remote:
	adb start-server
	adb shell ls /data/local/tmp/
	adb shell ls /sdcard/Music/iTunes/

playlists: clean_local
	./itunes-playlist-parser.py --write_all

sync: playlists ./bin/rsync-3.1.2-androideabi
	adb start-server
	adb push ./*.m3u /sdcard/Music/iTunes/
	adb push ./bin/rsync-3.1.2-androideabi /data/local/tmp/rsync
	# TODO: rsync mp3s
	echo ""
	echo "May need to restart the device and wait a minute"
	echo "for changes to take effect... try `adb reboot`"

clean_local:
	rm -f ./*.m3u

clean_remote:
	adb shell rm -f /sdcard/Music/iTunes/*.m3u
	adb shell rm -f /data/local/tmp/rsync
