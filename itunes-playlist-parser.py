#!/usr/bin/env python

from __future__ import print_function
import argparse
import os
import plistlib
import re
import urllib2

GREEN="\033[1;32m"
RESET="\033[0m"

def info(text):
    return GREEN + text + RESET

class SmartPlaylist(object):
    """Define ordering for a subsection of smart playlists"""

    @staticmethod
    def recentlyAdded(tracks, limit=None):
        recent = sorted(tracks, key=lambda t: t["Date Added"], reverse=True)
        if limit:
            recent = recent[:limit]
        return recent

    @staticmethod
    def mostPlayed(tracks, limit=50):
        popular = sorted(tracks, key=lambda t: t.get("Play Count", 0), reverse=True)
        if limit:
            popular = popular[:limit]
        return popular

class PlaylistParser(object):
    """Class to make playlist files compatible with some music players on Android (i.e. BlackPlayer)"""

    def __init__(self):
        itunes_lib_xml_path = os.path.expanduser("~/Music/iTunes/iTunes Music Library.xml")
        itunes_lib = plistlib.readPlist(itunes_lib_xml_path)
        self.tracks = itunes_lib["Tracks"]
        self.playlists = itunes_lib["Playlists"]

    def listTrackTypes(self):
        return set([t.get("Kind") for t in self.tracks.itervalues()])

    def getTracksOfType(self, typeName):
        return [t for t in self.tracks.itervalues() if t.get("Kind") == typeName]

    def getAudioTracks(self):
        audio_tracks = self.getTracksOfType("MPEG audio file")
        audio_tracks += self.getTracksOfType("AAC audio file")
        # NOTE: not taking "Ringtone"
        return audio_tracks

    def getAudioPlaylists(self):
        audio_playlists = filter(lambda p: not p.get("Distinguished Kind"), self.playlists)
        # NOTE: drop Smart Playlists since ordering is not well understood on those
        audio_playlists = filter(lambda p: not p.get("Smart Criteria"), audio_playlists)
        # NOTE: drop "####!####" because it is list of all audio
        audio_playlists = filter(lambda p: p["Name"] != "####!####", audio_playlists)
        return audio_playlists

    def listAudioPlaylists(self):
        return [p["Name"] for p in self.getAudioPlaylists()]

    def getPlaylistByName(self, name):
        for p in self.playlists:
            if p["Name"] == name:
                return p
        return None

    def getAudioTracksOfPlaylist(self, playlist):
        if type(playlist) is str:
            playlist = self.getPlaylistByName(playlist)
        playlist_tracks = [self.tracks[str(t["Track ID"])] for t in playlist["Playlist Items"]]
        return playlist_tracks

    @staticmethod
    def getM3UForTracks(tracks):
        m3u = ["#EXTM3U"]
        for track in tracks:
            time = track["Total Time"] / 1000
            name = track["Name"]
            artist = track["Artist"]
            path = urllib2.unquote(track["Location"]).decode("utf8")
            m3u += ["#EXTINF:%d,%s - %s" % (time, name, artist)]
            m3u += [re.sub("^.*/iTunes/iTunes Media/", "", path)]
        m3u += [""] # end with an empty line
        return m3u

    def getM3UForPlaylist(self, playlist):
        tracks = self.getAudioTracksOfPlaylist(playlist)
        return PlaylistParser.getM3UForTracks(tracks)

    @staticmethod
    def writeM3UForTracks(tracks, filename):
        m3u = PlaylistParser.getM3UForTracks(tracks)
        with open(filename + ".m3u", "w") as f:
            f.write('\r'.join(m3u).encode('utf8'))

    def writeM3UForPlaylist(self, playlist):
        m3u = self.getM3UForPlaylist(playlist)
        if type(playlist) is not str:
            playlist = playlist["Name"]
        with open(playlist + ".m3u", "w") as f:
            f.write('\r'.join(m3u).encode('utf8'))

    def writeAllPlaylists(self):
        for playlist in self.getAudioPlaylists():
            self.writeM3UForPlaylist(playlist)
        PlaylistParser.writeM3UForTracks(SmartPlaylist.recentlyAdded(self.getAudioTracks()), "Recently Added")
        PlaylistParser.writeM3UForTracks(SmartPlaylist.mostPlayed(self.getAudioTracks()), "Most Played")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="command line iTunes playlist parser")
    ap.add_argument("-i", "--interactive", action="store_true", default=False, help="launch in iPython shell")
    ap.add_argument("-w", "--write_all", action="store_true", default=False, help="write all playlists to M3U files")
    args = ap.parse_args()

    pp = PlaylistParser()

    if args.interactive:
        from IPython import embed
        print(info("Defined custom class PlaylistParser with instance `pp`..."))
        print("\n")
        embed()
    elif args.write_all:
        pp.writeAllPlaylists()
    else:
        ap.print_help()
