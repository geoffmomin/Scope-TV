from default import *

import os
import sys
import re
import xbmc
import traceback
import unicodedata

from threading import Thread
try: import json
except: import simplejson as json
from urllib import quote_plus


if 'linux' in sys.platform:
    sys.path.append(os.path.join( mc.App().GetAppDir(),'external', 'Linux') )
elif 'win32' in sys.platform:
    sys.path.append(os.path.join( mc.App().GetAppDir(),'external', 'win32') )
elif 'darwin' in sys.platform:
    sys.path.append(os.path.join( mc.App().GetAppDir(),'external', 'OSX') )

from pysqlite2 import dbapi2 as sqlite

def getImage(str1, str2):
    return "http://www.scripts.allalla.com/music_pipe.php?q=%%22%s%%22+%%22%s%%22" % ( quote_plus( str1 ), quote_plus( str2 ) )

def Duration(seconds):
    m, s = divmod(seconds, 60)
    return "%02d:%02d" % (m, s)

def down(**kwargs):
    if kwargs.get('id', False):
        list = mc.GetWindow(_id).GetList(kwargs['id'])
        item = list.GetItem(list.GetFocusedItem())
        path = item.GetPath()

    if kwargs.get('path', False):
        path = kwargs['path']

    if 'boxeedb:' in path:
        items = _db.GetDirectory( str( path ) )
        if len(items) < 1:
            mc.ShowDialogNotification("No items found")
            return
        
        try:    label = re.compile('boxeedb\://(.*?)/').findall(path)[0]
        except: label = path.replace('boxeedb://', '')

        if kwargs.get('push', True):
            mc.GetWindow(_id).PushState()

        for item in items:
            item.SetProperty('header', label)

        mc.GetWindow(_id).GetList(55).SetItems( items )

    elif path == 'home':
        items = mc.ListItems()

        home = [{'label':'Artists', 'path':'boxeedb://artists', 'header':'HOME', 'thumb':'artists.png'},
                {'label':'Albums', 'path':'boxeedb://albums', 'header':'HOME', 'thumb':'albums.png'},
                {'label':'Genre', 'path':'boxeedb://genres', 'header':'HOME', 'thumb':'genre.png'},
                {'label':'Random', 'path':'boxeedb://random/?limit=40', 'header':'HOME', 'thumb':'shuffle.png'},
                {'label':'Search', 'path':'search', 'header':'HOME', 'thumb':'search.png'},
                {'label':'Now Playing', 'path':'nowplaying', 'header':'HOME', 'thumb':'now.png'},]

        for i in home:
            item = mc.ListItem(mc.ListItem.MEDIA_UNKNOWN)
            item.SetLabel(i['label'])
            item.SetPath(i['path'])
            item.SetThumbnail(i['thumb'])
            item.SetProperty('header', i['header'])
            items.append(item)
        mc.GetWindow(_id).GetList(55).SetItems( items )

    elif path == 'search':
        mc.GetWindow(_id).PushState()
        items = mc.ListItems()

        search = [{'label':'Artists', 'path':'boxeedb://search/?id=artists', 'header':'SEARCH', 'thumb':'search.png'},
                {'label':'Albums', 'path':'boxeedb://search/?id=albums', 'header':'SEARCH', 'thumb':'search.png'},
                {'label':'Genre', 'path':'boxeedb://search/?id=genres', 'header':'SEARCH', 'thumb':'search.png'},
        ]
        for i in search:
            item = mc.ListItem(mc.ListItem.MEDIA_UNKNOWN)
            item.SetLabel(i['label'])
            item.SetPath(i['path'])
            item.SetThumbnail(i['thumb'])
            item.SetProperty('header', i['header'])
            items.append(item)
        mc.GetWindow(_id).GetList(55).SetItems( items )

    elif path == 'nowplaying':
        playlist = mc.PlayList(mc.PlayList.PLAYLIST_MUSIC)
        if playlist.Size() > 0:
            mc.GetWindow(_id).PushState()
            items = mc.ListItems()
            for i in xrange(playlist.Size()):
                item = playlist.GetItem(i)
                item.SetProperty('header', 'Now Playing')
                items.append(item)
            mc.GetWindow(_id).GetList(55).SetItems( items )
        else:
            mc.ShowDialogNotification("No music playing")

    else:
        if item.GetProperty('header') == 'Now Playing':
            _player.PlaySelected(list.GetFocusedItem())
        else:
            mc.GetWindow(_id).PushState()
            mc.GetWindow(_id).GetControl(7000).SetVisible(True)
            mc.GetWindow(_id).GetControl(5).SetFocus()

class myPlayer(mc.Player):
    def __init__(self):
        mc.Player.__init__(self, False)

    def playlist(self):
        return mc.PlayList(mc.PlayList.PLAYLIST_MUSIC)

    def play(self, type, id):
        list = mc.GetWindow(_id).GetList(55)
        focus = list.GetFocusedItem()
        item = list.GetItem(focus)
        item.SetAddToHistory(True)

        listitems = list.GetItems()

        if self.IsPlayingVideo():
            self.Stop()

        if type == 'play':
            self.playlist().Clear()
            if id == 'all':
                for item in listitems:
                    item.SetAddToHistory(True)
                    self.playlist().Add(item)
                self.PlaySelected(focus)
            else:
                self.playlist().Add(item)
                self.PlaySelected(0)

        elif type == 'queue':
            if id == 'all':
                for item in listitems:
                    item.SetAddToHistory(True)
                    self.playlist().Add(item)
                mc.ShowDialogNotification("Items Queued")

            else:
                self.playlist().Add(item)
                mc.ShowDialogNotification("Item Queued")

        mc.GetWindow(_id).GetControl(55).SetFocus()
        mc.GetWindow(_id).GetControl(7000).SetVisible(False)


class dbAcces:
    def __init__(self):
        self.temp = xbmc.translatePath('special://temp')
        self.db_raw = xbmc.translatePath('special://home/Database/boxee_catalog.db')
        if _embedded:
            self.db = os.path.join( self.temp, 'boxee_catalog.db' )
            self.createLink()
        else:
            self.db = self.db_raw

    def createLink(self):
        if os.path.exists(self.db) or os.path.islink(self.db):
            os.remove(self.db)
        os.symlink( self.db_raw, self.db )

    def buildSQL(self, path):
        path2 = path.replace('boxeedb://', '')
        data = path2.split('/')
        if len(data) == 0:
            data = [path]

        if data[0] not in ['artists', 'albums', 'genres', 'album', 'artist', 'genre', 'random', 'search' ]:
            return ''

        params = {}
        if len(data) > 1:
            params = self.parse_qs(data[1])

        sql = ''
        order = ''
        sql_artists = 'SELECT idArtist, strName, strPortrait FROM artists'
        sql_albums = 'SELECT albums.idAlbum, albums.strTitle, albums.strArtwork, artists.strName FROM albums, artists WHERE albums.idArtist = artists.idArtist'
        sql_genres = 'SELECT DISTINCT strGenre FROM albums'
        sql_files = 'SELECT audio_files.strTitle, audio_files.iDuration, audio_files.iTrackNumber, audio_files.strPath, albums.strArtwork, albums.strTitle, artists.strName FROM audio_files, albums, artists WHERE audio_files.idAlbum = albums.idAlbum AND albums.idArtist = artists.idArtist'
        sql_and = ' AND '
        sql_where = ' WHERE '

        if data[0] == 'artists':
            sql = sql_artists + ' ORDER BY strName COLLATE NOCASE'
            order = 'order_artists'

        elif data[0] == 'albums':
            sql = sql_albums + ' ORDER BY albums.strTitle COLLATE NOCASE'
            order = 'order_albums'

        elif data[0] == 'genres':
            sql = sql_genres + ' ORDER BY strGenre COLLATE NOCASE'
            order = 'order_genres'

        elif data[0] == 'search' and params.get('id', False):
            response = mc.ShowDialogKeyboard("Search - %s" % params['id'], "", False)
            if len(response) > 1:
                if params['id'] == 'artists':
                    sql = '%s%sstrName LIKE "%%%s%%"' % (sql_artists, sql_where, response)
                    order = 'order_artists'
                elif params['id'] == 'albums':
                    sql = '%s%salbums.strTitle LIKE "%%%s%%"' % (sql_albums, sql_and, response)
                    order = 'order_albums'
                elif params['id'] == 'genres':
                    sql = '%s%sstrGenre LIKE "%%%s%%"' % (sql_genres, sql_where, response)
                    order = 'order_genres'

        elif data[0] == 'artist':
            if params.get('songs', False) and params.get('id', False):
                sql = sql_files + sql_and +'audio_files.idArtist = "%s" ORDER BY RANDOM()' % params['id']
                order = 'order_files'
            elif params.get('id', False):
                sql = sql_albums + sql_and +'albums.idArtist = "%s"' % params['id']
                order = 'order_albums'

        elif data[0] == 'album':
            if params.get('id', False):
                sql = sql_files + sql_and +'audio_files.idAlbum = "%s"' % params['id']
                order = 'order_files'

        elif data[0] == 'genre':
            if params.get('songs', False) and params.get('id', False):
                sql = sql_files + sql_and +'albums.strGenre = "%s" ORDER BY RANDOM()' % params['id']
                order = 'order_files'
            elif params.get('id', False):
                sql = sql_albums + sql_and + 'albums.strGenre = "%s"' % params['id'].strip()
                order = 'order_albums'

        elif data[0] == 'random':
            sql = sql_files + ' ORDER BY RANDOM()'
            order = 'order_files'

        if params.get('limit', False):
            sql = sql + ' LIMIT %s' % params['limit']

        return sql, order

    def GetDirectory(self, path):
        sql, order = self.buildSQL(path)
        if sql == '':
            return mc.ListItems()

        conn = sqlite.connect(self.db)
        c = conn.cursor()
        data = c.execute(sql)

        items = mc.ListItems()
        if order == 'order_artists':
            for row in data:
                if not row[1] == '':
                    item = mc.ListItem(mc.ListItem.MEDIA_UNKNOWN)
                    item.SetLabel(row[1].encode("utf-8"))
                    item.SetArtist(row[1].encode("utf-8"))
                    item.SetPath('boxeedb://artist/?id=%s' % str(row[0]))
                    item.SetThumbnail(row[2].encode("utf-8"))
                    items.append(item)


        elif order == 'order_albums':
            if 'artist' in path or 'genre' in path:
                item = mc.ListItem(mc.ListItem.MEDIA_UNKNOWN)
                item.SetLabel('[COLOR FFFFFFFF]Shuffle all Songs[/COLOR]')
                item.SetPath(path + '&songs=all')
                item.SetThumbnail('shuffle.png')
                items.append(item)
            for row in data:
                if not row[1] == '':
                    item = mc.ListItem(mc.ListItem.MEDIA_UNKNOWN)
                    item.SetLabel(row[1].encode("utf-8"))
                    item.SetAlbum(row[1].encode("utf-8"))
                    item.SetPath('boxeedb://album/?id=%s' % str(row[0]))
                    if row[2] != '':
                        item.SetThumbnail(row[2].encode("utf-8"))
                    else:
                        item.SetThumbnail( getImage(row[3].encode("utf-8"), row[1].encode("utf-8")) )
                    item.SetArtist(row[3].encode("utf-8"))
                    items.append(item)
        elif order == 'order_genres':
            for row in data:
                if not row[0] == '':
                    item = mc.ListItem(mc.ListItem.MEDIA_UNKNOWN)
                    item.SetLabel(row[0].encode("utf-8"))
                    item.SetArtist(row[0].encode("utf-8"))
                    item.SetThumbnail( getImage('music genre', row[0].encode("utf-8")) )
                    item.SetPath('boxeedb://genre/?id=%s' % str(row[0]))
                    items.append(item)
        elif order == 'order_files':
            for row in data:
                if not row[0] == '':
                    item = mc.ListItem(mc.ListItem.MEDIA_UNKNOWN)
                    item.SetLabel(row[0].encode("utf-8"))
                    item.SetDuration( row[1] )
                    item.SetProperty( 'time', Duration(row[1]) )
                    item.SetTrackNumber( row[2] )
                    item.SetPath(row[3].encode("utf-8"))
                    if row[4] != '':
                        item.SetThumbnail(row[4].encode("utf-8"))
                    else:
                        item.SetThumbnail( getImage(row[6].encode("utf-8"), row[5].encode("utf-8")) )
                    item.SetAlbum(row[5].encode("utf-8"))
                    item.SetArtist(row[6].encode("utf-8"))
                    items.append(item)

        c.close()
        return items

    def parse_qs(self, u):
        return '?' in u and dict(p.split('=') for p in u[u.index('?') + 1:].split('&')) or {}




#INIT APP
try:    _embedded   = mc.IsEmbedded()
except: _embedded   = False
_id                 = 17000
_http               = mc.Http()
_player             = myPlayer()
_db                 = dbAcces()
