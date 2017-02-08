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

class SmartCriteria(object):
    """Define ordering for a subsection of smart playlists"""
    pass

class PlaylistParser(object):
    """Playlist files compatible with some music players on Android. Tested on Pulsar, BlackPlayer, Shuttle"""

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

    def getM3UForPlaylist(self, playlist):
        m3u = ["#EXTM3U"]
        for track in self.getAudioTracksOfPlaylist(playlist):
            time = track["Total Time"] / 1000
            name = track["Name"]
            artist = track["Artist"]
            path = urllib2.unquote(track["Location"]).decode("utf8")
            m3u += ["#EXTINF:%d,%s - %s" % (time, name, artist)]
            m3u += [re.sub("^.*/iTunes/iTunes Media/", "", path)]
            #m3u += [path[7:]]
        m3u += [""] # end with an empty line
        return m3u

    def writeM3UForPlaylist(self, playlist):
        m3u = self.getM3UForPlaylist(playlist)
        if type(playlist) is not str:
            playlist = playlist["Name"]
        with open(playlist + ".m3u", "w") as f:
            f.write('\r'.join(m3u).encode('utf8'))

    def writeAllPlaylists(self):
        for playlist in self.getAudioPlaylists():
            self.writeM3UForPlaylist(playlist)

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

        import mutagen
        s = sorted(pp.getAudioTracksOfPlaylist("Recently Added"), key=lambda x: x["Date Added"], reverse=True)
        fs = [urllib2.unquote(i["Location"]).decode("utf8")[7:] for i in s]
        mfs = [mutagen.File(m) for m in fs]
        mfsnp = [{k:v for k,v in mf.items() if k != u'APIC:'} for mf in mfs]
        png_x = int(filter(lambda c: c.isdigit(), mfs[0][u'APIC:'].data.split("PixelXDimension")[1]))
        known_tags = {
            u'APIC:' : 'album art',
            'TALB' : 'album',
            'TCON' : 'genre',
            'TDRC' : 'year',
            'TIT2' : 'track',
            'TPE1' : 'artist',
            'TPOS' : 'disc#/total#',
            'TRCK' : 'track#/total#',
        }
        opt_tags = {
            'TPE2' : 'album artist', # Anderson Paak for NxWorries, etc
            'TSOA' : 'sort album', # grab from album
            'TSOP' : 'sort artist', # grab from artist
            'TSOT' : 'sort track', # grab from track
            'TSO2' : 'album artist', # grab from album artist (iTunes unofficial tag)
            'TCMP' : 'compilation flag', # (iTunes unofficial tag)
            'TSSE' : 'encoded with', # LAME, iTunes, etc
            'TENC' : 'non-visible encoded with', # grab from encoded if no 'TSSE' key?
            u'COMM::eng' : 'comments', # soundcloud, etc
        }
        ignore_tags = {
            'TPE3' : 3, # artist repeat?
            'TLAN' : 2, # language
            'TPUB' : 4, # publisher
            'TDRL' : 0, # release date (not record date)
            'COMM:iTunNORM:eng' : 4,
            'COMM:iTunPGAP:eng' : 4,
            'COMM:iTunSMPB:eng' : 4,
            'COMM:iTunes_CDDB_IDs:eng' : 4,
        }
        # http://id3.org/id3v2.4.0-frames
        # http://id3.org/Developer%20Information

        from collections import defaultdict
        alltags = defaultdict(int)
        for id3f in mfs:
            for k in id3f.keys():
                alltags[k] += 1
        commontags = {k:v for k,v in alltags.items() if v == 100}

        def findWithTag(tag):
            return filter(lambda mf: mf.get(tag), mfsnp)

        embed()
    elif args.write_all:
        pp.writeAllPlaylists()
    else:
        ap.print_help()
