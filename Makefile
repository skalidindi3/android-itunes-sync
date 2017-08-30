.PHONY: playlists
playlists: clean_local
	./itunes-playlist-parser.py --write_all

.PHONY: check_remote
check_remote:
	adb start-server
	-adb shell ls /data/local/tmp/
	-adb shell ls /sdcard/Music/iTunes/

.PHONY: prep_sync_server
prep_sync_server: ./bin/rsync-3.1.2-androideabi
	adb start-server
	adb push ./bin/rsync-3.1.2-androideabi /data/local/tmp/rsync
	adb push ./rsyncd.conf /data/local/tmp/rsyncd.conf
	adb shell '/data/local/tmp/rsync --daemon --config=/data/local/tmp/rsyncd.conf &'
	adb forward tcp:6010 tcp:1873

.PHONY: disconnect_sync_server
disconnect_sync_server:
	-adb forward --remove tcp:6010

.PHONY: changelist
changelist: prep_sync_server ./bin/rsync-3.1.2-osx
	adb shell mkdir -p /sdcard/Music/iTunes/Music/
	./bin/rsync-3.1.2-osx -rlzni --size-only --delete-before --prune-empty-dirs \
    ${HOME}/Music/iTunes/iTunes\ Media/Music \
    rsync://localhost:6010/root/sdcard/Music/iTunes/.

.PHONY: sync_only
sync_only: playlists ./bin/rsync-3.1.2-osx
	adb shell mkdir -p /sdcard/Music/iTunes/Music/
	adb push ./*.m3u /sdcard/Music/iTunes/
	./bin/rsync-3.1.2-osx -rlzi --size-only --delete-before --prune-empty-dirs --info=progress2 \
    ${HOME}/Music/iTunes/iTunes\ Media/Music \
    rsync://localhost:6010/root/sdcard/Music/iTunes/.
	@echo "\nMay need to restart the device and wait a minute"
	@echo "for changes to take effect... try 'adb reboot'\n"

.PHONY: sync
sync: prep_sync_server sync_only clean_remote_rsync clean_local disconnect_sync_server

.PHONY: clean_local
clean_local:
	rm -f ./*.m3u

.PHONY: clean_remote_rsync
clean_remote_rsync:
	-adb shell kill `pgrep rsync`
	adb shell rm -f /data/local/tmp/rsync /data/local/tmp/rsyncd.conf

.PHONY: clean_remote
clean_remote: clean_remote_rsync
	adb shell rm -f /sdcard/Music/iTunes/*.m3u
