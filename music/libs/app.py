from default import *

import os
import sys
import re
import xbmc
import glob
from xmltom3u import *
import shutil


#from urllib import quote_plus
try:    import cPickle as pickle
except: import pickle


if 'linux' in sys.platform:
    sys.path.append(os.path.join( mc.App().GetAppDir(),'external', 'Linux') )
elif 'win32' in sys.platform:
    sys.path.append(os.path.join( mc.App().GetAppDir(),'external', 'win32') )
elif 'darwin' in sys.platform:
    sys.path.append(os.path.join( mc.App().GetAppDir(),'external', 'OSX') )

from pysqlite2 import dbapi2 as sqlite

def getImage(str1, str2):
    #return "http://boxee.bartsidee.nl/music_pipe.php?q=%%22%s%%22+%%22%s%%22" % ( quote_plus( str1 ), quote_plus( str2 ) )
    return ''

def Duration(seconds):
    m, s = divmod(seconds, 60)
    return "%02d:%02d" % (m, s)

###Retreive new data
def down(**kwargs):
    mc.ShowDialogWait()
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

    elif 'pl://' in path:
        items = _pl.GetDirectory( str( path ) )
        if len(items) < 1:
            mc.ShowDialogNotification("No items found")
            return

        try:    label = re.compile('pl\://(.*?)/').findall(path)[0]
        except: label = path.replace('pl://', '')

        if kwargs.get('push', True) and 'scan=true' not in path:
            mc.GetWindow(_id).PushState()

        for item in items:
            item.SetProperty('header', label)

        mc.GetWindow(_id).GetList(55).SetItems( items )

    elif path == 'home':
        items = mc.ListItems()

        home = [{'label':'Artists', 'path':'boxeedb://artists', 'header':'HOME', 'thumb':'artists.png'},
                {'label':'Albums', 'path':'boxeedb://albums', 'header':'HOME', 'thumb':'albums.png'},
                {'label':'Genre', 'path':'boxeedb://genres', 'header':'HOME', 'thumb':'genre.png'},
                {'label':'Playlists', 'path':'pl://playlist', 'header':'HOME', 'thumb':'genre.png'},
                {'label':'Search', 'path':'search', 'header':'HOME', 'thumb':'search.png'},
		{'label':'Shuffle Random', 'path':'boxeedb://random/?limit=40', 'header':'HOME', 'thumb':'shuffle.png'},
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

        search = [
                {'label':'Songs', 'path':'boxeedb://search/?id=songs', 'header':'SEARCH', 'thumb':'search.png'},
                {'label':'Artists', 'path':'boxeedb://search/?id=artists', 'header':'SEARCH', 'thumb':'search.png'},
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
        elif item.GetProperty('header') == 'playlist':
            _player.play('play', 'selected')
        else:
            mc.GetWindow(_id).PushState()
            mc.GetWindow(_id).GetControl(7000).SetVisible(True)
            mc.GetWindow(_id).GetControl(5).SetFocus()
    mc.HideDialogWait()


###Player
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


###Processing
class dbAcces:
    def __init__(self):
        self.db_raw = xbmc.translatePath('special://home/Database/boxee_catalog.db')
        self.db = getPath(self.db_raw)

    def buildSQL(self, path):
        path2 = path.replace('boxeedb://', '')
        data = path2.split('/')
        if len(data) == 0:
            data = [path]

        if data[0] not in ['artists', 'albums', 'genres', 'album', 'artist', 'genre', 'random', 'search' ]:
            return ''

        params = {}
        if len(data) > 1:
            params = parse_qs(data[1])

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
                elif params['id'] == 'songs':
                    sql = '%s%saudio_files.strTitle LIKE "%%%s%%"' % (sql_files, sql_and, response)
                    order = 'order_files'

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


class plAcces:
    def __init__(self):
        self.sources = self.getSources()

    def getSources(self):
        response = xbmc.executehttpapi("GetShares(music)")
        sources = response.split('<li>')
        source_path = [source.split(';')[1] for source in sources if source != '']
        return (path.replace('\n', '') for path in source_path if 'special:' not in path)

    def getSMB(self, path, dir=False):
        response = xbmc.executehttpapi("GetDirectory(%s)" % path)
        dirs_raw = response.replace('\n', '').split('<li>')
        dirs_raw.pop(0)
        try:
            if dir:
                return [ dir.split("/")[-2] for dir in dirs_raw]
            else:
                return [ dir.split(".m3u")[0]+'.m3u' for dir in dirs_raw if '.m3u' in dir]
        except:
            print path
            print dirs_raw
            return []

    def getPlaylist(self):
        data = mc.GetApp().GetLocalConfig().GetValue("playlists")
        if data != '':
            try:    return pickle.loads(data)
            except: return []
        else:
            return []

    def savePlaylist(self, playlist):
        data = pickle.dumps(playlist)
        mc.GetApp().GetLocalConfig().SetValue("playlists", data)

    def resetPlaylist(self):
        mc.GetApp().GetLocalConfig().SetValue("playlists", '')

    def walkM3U(self, path):
        playlist = []
        for plname in glob.glob( path ):
            playlist.append( {'label':os.path.basename(plname).replace('.m3u','').encode("utf-8"), 'path':plname, 'thumb':''} )
        return playlist


    def process(self, path):
        path2 = path.replace('pl://', '')
        data = path2.split('/')
        if len(data) == 0:
            data = [path]

        if data[0] not in ['playlist']:
            return mc.ListItems(), False

        params = {}
        if len(data) > 1:
            params = parse_qs(data[1])

        items = mc.ListItems()
        playlist = []
            
        if params.get('scan', False):
            mc.ShowDialogNotification("Scanning sources...")
            itunes = []
            m3u = []
            self.resetPlaylist()

            for source in self.sources:
                if 'smb://' in source:
                    dirs = self.getSMB(source, True)
                else:
                    try:    dirs = os.listdir(source)
                    except: dirs = []
                    
                for item in dirs:
                    if item == 'iTunes':
                        itunes.append(source)
                    elif item == 'Playlists':
                        m3u.append(source)

            if len(itunes) > 0:
                mc.ShowDialogNotification("Loading iTunes playlists...")
                boxee_playlists = os.path.join(mc.GetTempDir(),'playlists')
                    
                if not os.path.exists(boxee_playlists):
                    os.makedirs(boxee_playlists)

                for root, dirs, files in os.walk(boxee_playlists):
                    for f in files:
                        os.unlink(os.path.join(root, f))
                    for d in dirs:
                        shutil.rmtree(os.path.join(root, d))
                
                for source in itunes:
                    if '\\' in source:
                        itunes_path = source + '\\itunes\\iTunes Music Library.xml'
                    else:
                        itunes_path = source + '/itunes/iTunes Music Library.xml'

                    itunesconvert(itunes_path, source, boxee_playlists)
                    m3u_path = os.path.join(boxee_playlists,'*.m3u')
                    playlist += self.walkM3U( m3u_path )

            if len(m3u) > 0:
                mc.ShowDialogNotification("Loading m3u playlists...")
                for source in m3u:
                    if '\\' in source:
                        m3u_path = source + '\\Playlists\\*.m3u'
                        playlist += self.walkM3U(m3u_path)
                    elif 'smb://' in source:
                        files = self.getSMB(source + '/Playlists/')
                        print files
                        list = []
                        for plname in files:
                            list.append( {'label':os.path.basename(plname).replace('.m3u','').encode("utf-8"), 'path':plname, 'thumb':''} )
                        playlist += list
                    else:
                        m3u_path = source + '/Playlists/*.m3u'
                        playlist += self.walkM3U(m3u_path)
            self.savePlaylist(playlist)
            
        else:
            playlist += self.getPlaylist()

        playlist.insert(0, {'label':'[COLOR FFFFFFFF]Refresh playlists[/COLOR]', 'path':'pl://playlist/?scan=true', 'thumb':'shuffle.png'})

        for i in playlist:
            item = mc.ListItem(mc.ListItem.MEDIA_UNKNOWN)
            item.SetLabel(i['label'])
            item.SetPath(i['path'])
            item.SetThumbnail(i['thumb'])
            items.append(item)

        return items

    def GetDirectory(self, path):
        return self.process(path)

def parse_qs(u):
    return '?' in u and dict(p.split('=') for p in u[u.index('?') + 1:].split('&')) or {}

def getPath(path):
    if _embedded:
        temp_dir = mc.GetTempDir()
        temp_path = os.path.join( temp_dir, os.path.basename(path) )

        if os.path.exists(temp_path) or os.path.islink(temp_path):
            os.remove(temp_path)

        os.symlink( path, temp_path )
        return temp_path
    else:
        return path

#INIT APP
try:    _embedded   = mc.IsEmbedded()
except: _embedded   = False
_id                 = 14000
_http               = mc.Http()
_player             = myPlayer()
_db                 = dbAcces()
_pl                 = plAcces()
