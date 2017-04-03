#!/usr/bin/env python
# coding: utf8

import logging
import os
import json
import datetime
import plistlib
import shutil
from urllib import parse
import string

ITUNES_EXPORT_CONFIGURATION_FILE = 'PlaylistExportConfig.json'
ITUNES_EXPORT_KEY_ITUNESLIB = 'iTunesLib'
ITUNES_EXPORT_KEY_OUTPUTFOLDER = 'OutputFolder'
ITUNES_EXPORT_KEY_PLAYLISTS = 'Playlists'

ITUNES_LIB_APPLICATIONVERSION = 'Application Version'
ITUNES_LIB_DATE = 'Date'
ITUNES_LIB_PLAYLISTS = 'Playlists'
ITUNES_LIB_TRACKS = 'Tracks'
ITUNES_LIB_MUSICFOLDER = 'Music Folder'
ITUNES_LIB_PLAYLISTNAME = 'Name'
ITUNES_LIB_TRACKID = 'Track ID'
ITUNES_LIB_TRACKLOCATION = 'Location'
ITUNES_LIB_TRACKARTIST = 'Artist'
ITUNES_LIB_TRACKNAME = 'Name'

class PlaylistExport:
    def __init__(self, dataConfiguration):
        # Set the configuration
        self.dataConfiguration = dataConfiguration

        # Check the iTunes XML database file
        if not os.path.exists(self.dataConfiguration[ITUNES_EXPORT_KEY_ITUNESLIB]):
            logging.critical('Failed to load iTunes database at path: %s', dataConfiguration[ITUNES_EXPORT_KEY_ITUNESLIB])
            exit(1)

    def loadDatabase(self):
        try:
            with open(self.dataConfiguration[ITUNES_EXPORT_KEY_ITUNESLIB], 'rb') as fp:
                self.iTunesLib = plistlib.load(fp)
                fp.close()

            logging.info('iTunes version: %s', self.iTunesLib[ITUNES_LIB_APPLICATIONVERSION])
            logging.info('Last edit: %s', self.iTunesLib[ITUNES_LIB_DATE].strftime("%Y-%m-%d %H:%M:%S"))
            self.iTunesLibPlaylists = self.iTunesLib[ITUNES_LIB_PLAYLISTS]
            logging.info('Playlists: %s', str(len(self.iTunesLibPlaylists)))
            self.iTunesLibTracks = self.iTunesLib[ITUNES_LIB_TRACKS]
            logging.info('Tracks: %s', str(len(self.iTunesLibTracks)))
            self.strMusicFolder = self.iTunesLib[ITUNES_LIB_MUSICFOLDER]
            logging.info('Music folder: %s', self.strMusicFolder)
        except Exception as e:
            logging.critical('Failed to load iTunes database file: %s', str(e))
            exit(1)

    def exportPlaylists(self):
        for strActualPlaylist in self.dataConfiguration[ITUNES_EXPORT_KEY_PLAYLISTS]:
            logging.info('=======')
            logging.info('Working at playlist: %s', strActualPlaylist)

            # Getting index of actual playlist
            try:
                intActualPlaylistIndex = next(index for (index, d) in enumerate(self.iTunesLibPlaylists) if d[ITUNES_LIB_PLAYLISTNAME] == strActualPlaylist)
            except Exception as e:
                logging.critical('Can not find playlist: %s in iTunes Library!', strActualPlaylist)
                continue

            # Getting playlist items
            try:
                listTracks = self.iTunesLibPlaylists[intActualPlaylistIndex]['Playlist Items']
                if len(listTracks) == 0:
                    logging.info('Playlist is empty!')
                    continue
            except Exception as e:
                logging.critical('Can not get playlist items!', strActualPlaylist)
                continue

            # Check path in target
            strTargetFolderOfThisPlaylist = self.dataConfiguration[ITUNES_EXPORT_KEY_OUTPUTFOLDER] + os.path.sep + strActualPlaylist
            logging.info('Target folder: %s', strTargetFolderOfThisPlaylist)

            if not os.path.exists(strTargetFolderOfThisPlaylist):
                # create
                os.makedirs(strTargetFolderOfThisPlaylist)
            else:
                # remove items
                shutil.rmtree(strTargetFolderOfThisPlaylist, True, None)
                os.makedirs(strTargetFolderOfThisPlaylist)

            # Copy tracks to folder
            for intIndex, dictActualTrackID in enumerate(listTracks, start=1):
                logging.info('Track: %i of %i', intIndex, len(listTracks))
                intActualTrackID = dictActualTrackID[ITUNES_LIB_TRACKID]
                logging.info('Track ID: %i', intActualTrackID)
                dictTrack = self.iTunesLibTracks[str(intActualTrackID)]
                strActualTrackSource = parse.unquote(dictTrack[ITUNES_LIB_TRACKLOCATION]).replace("file://", "")
                logging.info('Track source: %s', strActualTrackSource)
                strActualTrackDestination = strTargetFolderOfThisPlaylist + os.path.sep + self._getValidFilename(self._createFileName(dictTrack, intIndex))
                logging.info('Track destination: %s', strActualTrackDestination)

                # Copy the file
                if self._copyTrack(strActualTrackSource, strActualTrackDestination):
                    logging.info('Copy successful.')

    def _createFileName(self, dictTrack, intIndex):
        # Track number padding to 3
        strTrackNumber = str(intIndex).zfill(3)

        # Track extension
        strTrackFileExtension = os.path.splitext(dictTrack[ITUNES_LIB_TRACKLOCATION])[1]

        # Track artist
        strTrackArtist = dictTrack[ITUNES_LIB_TRACKARTIST]

        # Track name
        strTrackName = dictTrack[ITUNES_LIB_TRACKNAME]

        # Filename
        strTrackFilename = strTrackNumber + ' - ' + strTrackArtist + ' - ' + strTrackName + strTrackFileExtension
        return strTrackFilename

    def _getValidFilename(self, strFilename):
        valid_chars = ".-_ %s%s" % (string.ascii_letters, string.digits)
        valid_chars = frozenset(valid_chars)
        strValidFilename = ''.join(c if c in valid_chars else '' for c in strFilename)
        return strValidFilename

    def _copyTrack(self, strSource, strDestination):
        try:
            shutil.copy2(strSource, strDestination)
            return True
        except Exception as e:
            logging.critical('Can not copy track from %s to %s !', strSource, strDestination)
            return False

def main():
    # get the actual path
    strActualPath = os.path.dirname(os.path.realpath(__file__))

    # define configuration file
    strConfigurationFile = strActualPath + os.path.sep + ITUNES_EXPORT_CONFIGURATION_FILE

    # Load configuration
    try:
        with open(strConfigurationFile, 'r') as data_file:
            dataConfiguration = json.loads(data_file.read())
    except Exception as e:
        print('Can not load configuration file! --> Error: ' + str(e))
        exit(1)

    # Output folder
    if not os.path.exists(dataConfiguration[ITUNES_EXPORT_KEY_OUTPUTFOLDER]):
        try:
            os.makedirs(dataConfiguration[ITUNES_EXPORT_KEY_OUTPUTFOLDER])
        except Exception as e:
            print('Can not create output folder! --> Error: ' + str(e))
            exit(1)

    # Logging into destination folder
    striTunesExportLoggingFile = dataConfiguration[ITUNES_EXPORT_KEY_OUTPUTFOLDER] + os.path.sep + datetime.datetime.today().strftime('%Y_%m_%d__%H_%M_%S.log')
    logging.basicConfig(filename=striTunesExportLoggingFile, level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

    # Basic log
    logging.info('Starting a new iTunesExport session with process id: %s', str(os.getpid()))
    logging.info('Configuration: --> %s', dataConfiguration)

    # Init playlist exporter
    thePlaylistExporter = PlaylistExport(dataConfiguration)
    thePlaylistExporter.loadDatabase()
    thePlaylistExporter.exportPlaylists()

if __name__ == "__main__":
    main()