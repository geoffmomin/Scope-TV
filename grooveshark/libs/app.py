import sys, os, mc
import xbmc, xbmcgui
import cPickle as pickle
import traceback
import urllib

__debugging__ = False
__scriptid__ = mc.GetApp().GetId()
__cwd__ = mc.GetApp().GetAppDir()
__settings__ = mc.GetApp().GetLocalConfig()
__window__ = mc.GetWindow(14000)
__windowlist__ = __window__.GetList(50)

sys.path.append(os.path.join(__cwd__, 'libs'))
from GrooveAPI import *
from GrooveLib import *
from GrooveGUI import *
import GVlanguage

__language__ = GVlanguage.lg

#MAIN CLASS
##########################
class GrooveClass(object):
    #INIT FUNCTIONS
    def __init__(self):
        mc.ShowDialogWait()
        self.useCoverArt = True
        self.player = mc.GetPlayer()
        self.defaultCoverArt = 'default-cover.png'
        self.xbmcPlaylist = mc.PlayList(mc.PlayList.PLAYLIST_MUSIC)
        self.gs = GrooveAPI(enableDebug = __debugging__, cwd = __cwd__ ,clientUuid = None, clientVersion = None)
        username = __settings__.GetValue("username")
        password = __settings__.GetValue("password")
        self.gs.startSession(username, password)
        self.gs.setRemoveDuplicates(True)
        self._search = None

        self.start()
        mc.HideDialogWait()

    def start(self):
        try:
            searchLabel = 'Found ' + str(self._search.countResults()) + ' for "' + self._search.queryText + '"'
        except:
            searchLabel = 'Start a new search in the menu'
            traceback.print_exc()
        dict = [\
                {'label':__language__(128), 'label2':searchLabel, 'thumbnail':'gs_search.png', 'action':'searchshow'},\
                {'label':__language__(108), 'label2':__language__(3041), 'thumbnail':'gs_popular.png', 'action':'popular'},\
                {'label':__language__(129), 'label2':'Your favorites', 'thumbnail':'gs_favorites.png', 'action':'favorites'},\
                {'label':__language__(117), 'label2':__language__(3039), 'thumbnail':'gs_playlist.png', 'action':'playlist'},\
                {'label':__language__(107), 'label2':'Have a look at the tunes you\'re playing', 'thumbnail':'gs_song.png', 'action':'playing'}\
              ]
        listItems = mc.ListItems()
        for item in dict:
            listItem = createItem(item)
            listItems.append(listItem)
        __windowlist__.SetItems(listItems)

    def windowCheck(self):
        try:
            mc.GetActiveWindow().GetList(50)
            return False
        except: return True
    #NAV FUNCTIONS
    def action(self, id, list):
        mc.ShowDialogWait()
        listitems = __window__.GetList(list).GetItems()
        action = listitems[id].GetProperty('action')
        action_id = id
        
        handle_id = __windowlist__.GetFocusedItem()
        listItems = __windowlist__.GetItems()
        try: handle = pickle.loads(listItems[handle_id].GetProperty('handle'))
        except: handle = ''
        
        if list == 500:
            __window__.GetControl(50).SetFocus()
            __windowlist__.SetFocusedItem(handle_id)

        print 'Grooveshark::Navigation: '+action
        self.setStateLabel(action.upper())
        __window__.GetControl(300011).SetVisible(False)

        #MAIN MENU
        if action == 'searchshow':
            self.searchshow()
        elif action == 'popular':
            mc.GetActiveWindow().ClearStateStack(True)
            mc.GetActiveWindow().PushState()
            api = GS_PopularSongs()
            data = api._getPopular(self.gs)
            songs = Songs(data, defaultCoverArt = self.defaultCoverArt)
            [obj, listItems] = songs._list(self, self.gs)
            __windowlist__.SetItems(listItems)
        elif action == 'favorites':
            try:
                mc.GetActiveWindow().ClearStateStack(True)
                mc.GetActiveWindow().PushState()
                api = Favorites(gui = self, gsapi = self.gs, defaultCoverArt = self.defaultCoverArt)
                [obj, listItems] = api._list(self, self.gs)
                __windowlist__.SetItems(listItems)
            except:
                mc.HideDialogWait()
                self.notification(__language__(3027)) #checkpass
                mc.GetActiveWindow().ClearStateStack(True)
                return
        elif action == 'playlist':
            try:
                mc.GetActiveWindow().ClearStateStack(True)
                mc.GetActiveWindow().PushState()
                api = Playlists(gui = self, defaultCoverArt = self.defaultCoverArt)
                [obj, listItems] = api._list(self, self.gs)
                __windowlist__.SetItems(listItems)
            except:
                mc.HideDialogWait()
                self.notification(__language__(3027)) #checkpass
                mc.GetActiveWindow().ClearStateStack(True)
                return
        elif action == 'playing':
            mc.GetActiveWindow().ClearStateStack(True)
            mc.GetActiveWindow().PushState()
            obj, listItems = self.NowPlaying()
            __windowlist__.SetItems(listItems)

        #LEFTMENU
        elif action == 'search':
            self.search()

        elif action == 'settings':
            print 'settings called'
            mc.ActivateWindow(16000)

        elif action == 'exit':
            mc.GetApp().Close()

        #RIGHTMENU
        #navigate down
        elif action == 'down':
            obj = handle.get(action_id)
            mc.GetActiveWindow().PushState()
            [obj, listItems] = obj._list(self, self.gs)
            __windowlist__.SetItems(listItems)

        elif action == 'addSongToPlaylistExec':
            [playlist, song] = pickle.loads(listitems[action_id].GetProperty('handle'))
            self.addSongToPlaylistExec(playlist, song)


        #Song Parameters
        elif action == 'play':
            handle.play(handle_id, self.gs)
        elif action == 'queueSong':
            self.queueSong(handle_id, handle)
        elif action == 'queueAllSongs':
            self.queueAllSongs(handle)
        elif action == 'addSongToPlaylist':
            self.addSongToPlaylist(handle_id, handle)
        elif action == 'findSimilarFromSong':
            self.findSimilarFromSong(handle_id, handle)
        elif action == 'songsOnAlbum':
            self.songsOnAlbum(handle_id, handle)

        #album
        elif action == 'playAlbum':
            self.playAlbum(handle_id, handle)
        elif action == 'queueAlbum':
            self.queueAlbum(handle_id, handle)
        elif action == 'saveAlbumAsPlaylist':
            self.saveAlbumAsPlaylist(handle_id, handle)
        elif action == 'findSimilarFromAlbum':
            self.findSimilarFromAlbum(handle_id, handle)

        #PLaylist
        elif action == 'renamePlaylist':
            self.renamePlaylist(handle_id, handle)
        elif action == 'deletePlaylist':
            self.deletePlaylist(handle_id, handle)

        #Artist
        elif action == 'playSongsByArtist':
            self.playSongsByArtist(handle_id, handle)
        elif action == 'findSimilarFromArtist':
            self.findSimilarFromArtist(handle_id, handle)

        mc.HideDialogWait()

    def search(self):
        setMain()
        result = mc.ShowDialogKeyboard(__language__(1000), "", False)
        if len(result) > 0:
            try:
                self._search = Search(self, defaultCoverArt = self.defaultCoverArt)
                self._search.search(self.gs, result)
                self.start()
                self.searchshow()
            except:
                self.notification('Sorry')
                traceback.print_exc()

    def searchshow(self):
        if int(self._search.countResults()) > 0:
            mc.GetActiveWindow().ClearStateStack(True)
            mc.GetActiveWindow().PushState()
            [obj, listItems] = self._search._list(self, self.gs)
            __windowlist__.SetItems(listItems)

    def queueSong(self, selected, obj = None):
	try:
            song = obj.get(selected)
            obj.queue(self.gs, song, playlist = self.xbmcPlaylist)
            checkPlayback(self.xbmcPlaylist)
            self.notification('Queued')
	except:
            self.notification('Sorry')
            traceback.print_exc()

    def queueAllSongs(self, obj = None):
	try:
            obj.queueAll(self.gs, playlist = self.xbmcPlaylist, append = True)
            checkPlayback(self.xbmcPlaylist)
            self.notification('Queued')
	except:
            self.notification('Sorry')

    def playAlbum(self, selected = 0, obj = None):
	try:
            album = obj.get(selected)
            songs = album.getSongs(self.gs)
            songs.queueAll(playlist = self.xbmcPlaylist, append = False)
            checkPlayback(self.xbmcPlaylist)
	except:
            traceback.print_exc()
            self.notification('Sorry')

    def queueAlbum(self, selected = 0, obj = None):
    	try:
            album = obj.get(selected)
            songs = album.getSongs(self.gs)
            songs.queueAll(playlist = self.xbmcPlaylist, append = True)
            checkPlayback(self.xbmcPlaylist)
            self.notification('Queued')
	except:
            self.notification('Sorry')

    def playSongsByArtist(self, selected = 0, obj = None):
	try:
            artist = obj.get(selected)
            songs = artist.getSongs(self.gs)
            songs.play(selected = 0, gsapi = self.gs, playlist = self.xbmcPlaylist)
	except:
            self.notification('Sorry')

    def findSimilarFromSong(self, selected = 0, obj = None):
        try:
            song = obj.get(selected)
            artist = Artist(song.artistID)
            artists = artist.similar(gsapi = self.gs)
            mc.GetActiveWindow().PushState()
            [obj, listItems] = artists._list(self, self.gs)
            __windowlist__.SetItems(listItems)
	except:
            self.notification('Sorry')

    def songsOnAlbum(self, selected = 0, obj = None):
        try:
            song = obj.get(selected)
            albumId = song.albumID
            songs = Album(albumId, defaultCoverArt = self.defaultCoverArt).getSongs(gsapi = self.gs)
            mc.GetActiveWindow().PushState()
            [obj, listItems] = songs._list(self, self.gs)
            __windowlist__.SetItems(listItems)

        except:
            self.notification('Sorry')

    def findSimilarFromAlbum(self, selected = 0, obj = None):
        try:
            album = obj.get(selected)
            artist = Artist(album.artistID)
            artists = artist.similar(gsapi = self.gs)
            mc.GetActiveWindow().PushState()
            [obj, listItems] = artists._list(self, self.gs)
            __windowlist__.SetItems(listItems)
	except:
            self.notification('Sorry')

    def findSimilarFromArtist(self, selected = 0, obj = None):
	try:
            artist = obj.get(selected)
            artists = artist.similar(gsapi = self.gs)
            mc.GetActiveWindow().PushState()
            [obj, listItems] = artists._list(self, self.gs)
            __windowlist__.SetItems(listItems)
	except:
            self.notification('Sorry')

    def addSongToPlaylist(self, selected = 0, obj = None):
        try:
            song = obj.get(selected)
            setOptionsPlaylists(self, song)
	except:
            self.notification('Sorry')
            traceback.print_exc()

    def addSongToPlaylistExec(self, playlist = None, song = None):
	playlist.getSongs(self.gs)
	playlist.addSong(song)
	playlist.save(self.gs)
	self.notification('Added')

    def saveAlbumAsPlaylist(self, selected = 0, obj = None):
	album = obj.get(selected)
	name = album.artistName + ' - ' + album.name
	name = self.getInput('Name for playlist', default=name)
	if name == None:
            return
        if name != '':
            try:
                songs = album.getSongs(self.gs)
		info = {'Name': name, 'PlaylistID': -1, 'About': ''}
		Playlist(info, songs = songs).saveAs(self.gs)
		self.notification('Saved')
            except:
                self.notification('Sorry')
	else:
            self.notification('Type a name')

    def deletePlaylist(self, selected = 0, obj = None):
	try:
            playlist = obj.get(selected)
            playlist.delete(self.gs)
            api = Playlists(gui = self, defaultCoverArt = self.defaultCoverArt)
            [obj, listItems] = api._list(self, self.gs)
            __windowlist__.SetItems(listItems)
            self.notification('Deleted')
	except:
            self.notification('Sorry')

    def renamePlaylist(self, selected = 0, obj = None):
	playlist = obj.get(selected)
	name = self.getInput(__language__(111), default=playlist.name)
	if name != '' and name != None:
            try:
                playlist.rename(self.gs, name)
                api = Playlists(gui = self, defaultCoverArt = self.defaultCoverArt)
                [obj, listItems] = api._list(self, self.gs)
                __windowlist__.SetItems(listItems)
		self.notification('Renamed')
            except:
		self.notification('Sorry')




    #GUI Functions
    def notification(self, message):
        cnt = __window__.GetControl(7001)
	label = __window__.GetLabel(7003)
        label.SetLabel(message)
	cnt.SetFocus()
	xbmc.sleep(100)
	setMain()

    def setStateLabel(self, msg):
	__window__.GetLabel(3000).SetLabel(msg)

    def setInfoLabel(self, msg):
	cnt = __window__.GetLabel(300011)
	cnt.SetLabel(msg)
	__window__.GetControl(300011).SetVisible(True)

    def getInput(self, title, default="", hidden=False):
	response  = mc.ShowDialogKeyboard(str(title), str(default), hidden)
	if response != '':
            return response
	else:
            return None



    #OTHER FUNCTIONS
    def NowPlaying(self):
	playlist = mc.PlayList(mc.PlayList.PLAYLIST_MUSIC)
	n = playlist.Size()
	data = []
	songs = []
	for i in range(n):
            song = playlist.GetItem(i)
            name = song.GetProperty('info')
            if 'play?' in name:
                name = name.split('?')[1]
                parts = name.split('&')
                songId = parts[0].split('=')[1]
                artistId = parts[1].split('=')[1]
                albumId = parts[2].split('=')[1]
                image = decode(parts[3].split('=')[1])
                songName = decode(parts[4].split('=')[1])
                artistName = decode(parts[5].split('=')[1])
                albumName = decode(parts[6].split('=')[1])
                options = parts[7].split('=')[1]
                item = {'SongID': songId, 'Name': songName, 'AlbumName':albumName, 'ArtistName':artistName, 'ArtistID':artistId, 'AlbumID':albumId, 'ArtistID':artistId, 'CoverArt':image}
                data.append(item)
            else: print 'Song passed'
	songs = Songs(data, defaultCoverArt = self.defaultCoverArt)
	return songs._list(self, self.gs)


#SONG INSTANCES
##########################
class Songs(GS_Songs):
    def __init__(self, data, defaultCoverArt = None, sort = None):
        GS_Songs.__init__(self, data, defaultCoverArt = defaultCoverArt, sort = sort)

    def setContainers(self):
        self.songContainer = Song

    def _list(self, gui, gsapi):
        try:
            n = self.count()
            self.info = str(n) + ' ' + __language__(3023)
            listItems = mc.ListItems()
            handle = pickle.dumps(self, pickle.HIGHEST_PROTOCOL)
            for i in range(self.count()):
                song = self.get(i)
                try:
                    durMin = int(song.duration/60.0)
                    durSec = int(song.duration - durMin*60)
                    if durSec < 10:
                        durStr = '(' + str(durMin) + ':0' + str(durSec) + ')'
                    else:
                        durStr = '(' + str(durMin) + ':' + str(durSec) + ')'
                except:
                    durStr = ''
                if gui.useCoverArt == True:
                    path = song.coverart
                    if path == None:
                        path = 'Invalid cover path: ' + str(path)
                        print path
                else:
                    path = 'default-cover.png'
                l1 = song.name
                l2 = 'By ' + song.artistName + '\n From ' + song.albumName
                if song.year != None:
                    try:
                        lYear = ' (' + str(int(song.year)) + ')'
                    except:
                        lYear = ''
                else:
                    lYear = ''
                l2 = l2 + lYear
                path2 = 'gs_smile.png'

                item = {'label':l1, 'label2':l2, 'action':'play', 'handle':handle, 'thumbnail':path, 'icon':path2, 'state':'song'}
                listItem = createItem(item)
                listItems.append(listItem)
            gui.setInfoLabel(str(self.count()) + ' Songs')
            return [self, listItems]
        except:
            xbmc.log('GrooveShark Exception (listSongs): ' + str(sys.exc_info()[0]))
            traceback.print_exc()
        return [self, mc.ListItems()]

    def queueAll(self, gsapi, playlist = None, append = False):
        if playlist == None:
            playlist = mc.PlayList(mc.PlayList.PLAYLIST_MUSIC)
        if append == False:
            playlist.Clear()
            offset = 0
        else:
            offset = playlist.Size()
        for i in range(self.count()):
            song = self.get(i)
            self.queue(gsapi, song, playlist = playlist, index = i + offset)

    def play(self, selected, gsapi, playlist = None):
        if playlist == None:
            playlist =  mc.PlayList(mc.PlayList.PLAYLIST_MUSIC)

        song = self.get(selected)
        url = gsapi.getStreamURL(str(song.id))
        url2 = self.defaultUrl(song)

        count = playlist.Size()
        direct = True
        itemnr = 0
        if count > 0:
            for i in range(count):
                item = playlist.GetItem(i)
                if item.GetTitle() == song.name.encode('utf-8'):
                    direct = False
                    itemnr = i
        if direct:
            listItem = self.createListItem(url, song, url2)
            playlist.Clear()
            playlist.Add(listItem)
            mc.GetPlayer().PlaySelected(0)
        else:
            mc.GetPlayer().PlaySelected(itemnr-1)
        

    def queue(self, gsapi, song = None, playlist = None, index = -1, options = '', url = None):
        if playlist == None:
            playlist = mc.PlayList(mc.PlayList.PLAYLIST_MUSIC)

        url2 = self.defaultUrl(song)
        if playlist.Size() > 1:
            url = url2
        else:
            url = gsapi.getStreamURL(str(song.id))
        listItem = self.createListItem(url, song, url2)
        playlist.Add(listItem)


    def defaultUrl(self, song, options = ''):
        return 'app://%s/libs/play?playSong=%s&artistId=%s&albumId=%s&image=%s&songName=%s&artistName=%s&albumName=%s&options=%s' % (__scriptid__, song.id, song.artistID, song.albumID, self.encode(song.coverart), self.encode(song.name), self.encode(song.artistName), self.encode(song.albumName), options) # Adding plugin:// to the url makes xbmc call the script to resolve the real url

    def encode(self, s):
        try:
            return urllib.quote_plus(s.encode('latin1','ignore'))
        except:
            print '########## GS Encode error'
            print s
            return '### encode error ###'

    def createListItem(self, url, song, url2):
        listItem = mc.ListItem(mc.ListItem.MEDIA_AUDIO_MUSIC)
        listItem.SetTitle(song.name.encode('utf-8'))
        listItem.SetThumbnail(str(song.coverart))
        listItem.SetIcon(str(song.coverart))
        listItem.SetAlbum(song.albumName.encode('utf-8'))
        listItem.SetArtist(song.artistName.encode('utf-8'))
        listItem.SetProperty('action','songs')
        listItem.SetContentType('audio/mpeg')
        listItem.SetProperty('info', str(url2))
        listItem.SetPath(str(url))
        return listItem

class Albums(GS_Albums):
    def __init__(self, data, defaultCoverArt = None):
        GS_Albums.__init__(self, data, defaultCoverArt = defaultCoverArt)
        
    def setContainers(self):
        self.albumContainer = Album

    def _list(self, gui, gsapi):
        n = self.count()
        self.info = str(n) + ' ' + __language__(3025)
        listItems = mc.ListItems()
        handle = pickle.dumps(self, pickle.HIGHEST_PROTOCOL)
        for i in range(self.count()):
            album = self.get(i)
            item = {'label':album.name, 'label2':album.artistName, 'action':'down', 'handle':handle, 'thumbnail':album.coverart, 'icon':album.coverart, 'state':'album'}
            listItem = createItem(item)
            listItems.append(listItem)
        gui.setInfoLabel(str(self.count()) + ' Albums')
        return [self, listItems]

class Artists(GS_Artists):
    def __init__(self, data, defaultCoverArt = None):
        GS_Artists.__init__(self, data, defaultCoverArt = defaultCoverArt)

    def setContainers(self):
        self.artistContainer = Artist

    def _list(self, gui, gsapi):
        n = self.count()
        self.info = str(n) + ' ' + __language__(3024)
        handle = pickle.dumps(self, pickle.HIGHEST_PROTOCOL)
        listItems = mc.ListItems()
        for i in range(self.count()):
            artist = self.get(i)
            item = {'label':artist.name, 'action':'down', 'handle':handle, 'thumbnail':'default-cover.png', 'state':'artist'}
            listItem = createItem(item)
            listItems.append(listItem)
        gui.setInfoLabel(str(self.count()) + ' Artists')
        return [self, listItems]

class Song(GS_Song):
    def __init__(self, data, defaultCoverArt = None):
        GS_Song.__init__(self, data, defaultCoverArt = defaultCoverArt)

    def _list(self, gui, gsapi):
        return [None, None]

    def setContainers(self):
        self.albumContainer = Album

class Album(GS_Album):
    def __init__(self, data, defaultCoverArt = None):
        GS_Album.__init__(self, data, defaultCoverArt = defaultCoverArt)

    def setContainers(self):
        self.songsContainer = Songs

    def _list(self, gui, gsapi):
        songs = self.getSongs(gsapi)
        return songs._list(gui, gsapi)

class Artist(GS_Artist):
    def __init__(self, data, defaultCoverArt = None):
        GS_Artist.__init__(self, data, defaultCoverArt = defaultCoverArt)

    def setContainers(self):
        self.songsContainer = Songs
        self.albumsContainer = Albums
        self.artistsContainer = Artists

    def _list(self, gui, gsapi):
        songs = self.getSongs(gsapi)
        return songs._list(gui, gsapi)

class Search(GS_Search):
    def __init__(self, gui, defaultCoverArt = None):
        self.gui = gui
        GS_Search.__init__(self, defaultCoverArt = defaultCoverArt, songContainer = Song, songsContainer = Songs, albumContainer = Album, albumsContainer = Albums, artistContainer = Artist, artistsContainer = Artists)

    def newSongContainer(self, item):
        return self.songContainer(item, defaultCoverArt = self.defaultCoverArt)

    def newSongsContainer(self, item, sort = 'Score'):
        return self.songsContainer(item, defaultCoverArt = self.defaultCoverArt)

    def newArtistContainer(self, item):
        return self.artistContainer(item, defaultCoverArt = self.defaultCoverArt)

    def newArtistsContainer(self, item):
        return self.artistsContainer(item, defaultCoverArt = self.defaultCoverArt)

    def newAlbumContainer(self, item):
	return self.albumContainer(item, defaultCoverArt = self.defaultCoverArt)

    def newAlbumsContainer(self, item):
	return self.albumsContainer(item, defaultCoverArt = self.defaultCoverArt)

    def get(self, n):
	if n == 0:
            return self.songs
	if n == 1:
            return self.artists
	if n == 2:
            return self.albums
        if n == 3:
            return self.songs

    def _list(self, gui, gsapi):
        if self.queryText == None:
            return
	search = self
        handle = pickle.dumps(SearchHandle(self.songs, self.artists, self.albums))
        dict = [\
                {'label':__language__(3023), 'label2':str(search.countSongs()) + ' ' + __language__(3026), 'thumbnail':'gs_song.png', 'action':'down', 'handle':handle, 'state':'search'},\
                {'label':__language__(3024), 'label2':str(search.countArtists()) + ' ' + __language__(3026), 'thumbnail':'gs_artist.png', 'action':'down', 'handle':handle, 'state':'search'},\
                {'label':__language__(3025), 'label2':str(search.countAlbums()) + ' ' + __language__(3026), 'thumbnail':'gs_album.png', 'action':'down', 'handle':handle, 'state':'search'}\
                #{'label':__language__(3042), 'label2':str(0) + ' ' + __language__(3026), 'thumbnail':'gs_playlist.png', 'action':'down', 'handle':handle, 'state':'search'}
              ]
        listItems = mc.ListItems()
        for item in dict:
            listItem = createItem(item)
            listItems.append(listItem)
	return [self, listItems]



class SearchHandle(object):
    def __init__(self, songs, artists, albums):
        self.songs = songs
        self.artists = artists
        self.albums = albums
    def get(self, n):
	if n == 0:
            return self.songs
	if n == 1:
            return self.artists
	if n == 2:
            return self.albums
        if n == 3:
            return self.songs

class Playlists(GS_Playlists):
    def __init__(self, gui, defaultCoverArt = None):
        self.gui = gui
	GS_Playlists.__init__(self, defaultCoverArt = defaultCoverArt)

    def setContainers(self):
        self.playlistContainer = Playlist
    
    def _list(self, gui, gsapi):
	if self.getPlaylists(gsapi) == False:
            gui.notification(__language__(3027))
            return [None, None]
	n = self.count()
	self.info = str(n) + ' ' + __language__(3042)
	listItems = mc.ListItems()
        playobj = PlaylistHandle(self)
        handle = pickle.dumps(playobj, pickle.HIGHEST_PROTOCOL)
	for i in range(self.count()):
            playlist = self.get(i)
            if playlist.about == None:
		l2 = ''
            else:
		l2 = str(playlist.about)
            item = {'label':playlist.name, 'label2':l2, 'action':'down', 'handle':handle, 'thumbnail':'default-cover.png', 'icon':'default-cover.png', 'state':'playlist'}
            listItem = createItem(item)
            listItems.append(listItem)
        return [self, listItems]

class PlaylistHandle(object):
    def __init__(self, obj):
        self.data = []
        for i in range(obj.count()):
            self.data.append(obj.get(i))

    def get(self, n):
	return self.data[n]


class Playlist(GS_Playlist):
	def setContainers(self):
		self.songsContainer = Songs

	def _list(self, gui, gsapi):
		data = self.getSongs(gsapi)
		return self.songs._list(gui, gsapi)

class Favorites(GS_FavoriteSongs):
    def __init__(self, gui, gsapi, defaultCoverArt = None):
        self.defaultCoverArt = defaultCoverArt
	self.gui = gui
	self.type = type
	GS_FavoriteSongs.__init__(self, defaultCoverArt = defaultCoverArt)

    def setContainers(self):
        self.songContainer = Song

    def _list(self, gui, gsapi):
        data = self._favorites(gsapi)
	if data == None:
            gui.notification(__language__(3027)) #Wrong username/password
            return None
	return Songs(data, self.defaultCoverArt)._list(gui, gsapi)





#Menu Items
#############
def setLeftMenu():
    cnt = __window__.GetControl(500)
    cnt.SetEnabled(True)
    dict = [\
        {'label':__language__(106), 'action':'search', 'icon':'gs_search.png'},\
        {'label':__language__(107), 'action':'playing', 'icon':'gs_playlist.png'},\
        {'label':__language__(117), 'action':'playlist', 'icon':'gs_song.png'},\
        {'label':__language__(109), 'action':'settings', 'icon':'gs_wrench.png'},\
        {'label':__language__(121), 'action':'exit', 'icon':'gs_exit.png'}\
            ]
    listItems = mc.ListItems()
    for item in dict:
        listItem = createItem(item)
        listItems.append(listItem)
    __window__.GetLabel(4100).SetLabel('')
    __window__.GetImage(410).SetTexture('gs_home.png')
    __window__.GetList(500).SetItems(listItems)
    cnt.SetFocus()

def setMain():
    cnt = __window__.GetControl(500)
    cnt.SetEnabled(False)
    __window__.GetControl(50).SetFocus()

def setOptionsPlaylists(obj, song):
    playlists = Playlists(obj, defaultCoverArt = obj.defaultCoverArt)
    playlists.getPlaylists(obj.gs)

    print 'setOptionsPlaylists() called'
    cnt = __window__.GetControl(500)
    cnt.SetEnabled(True)
    listItems = mc.ListItems()
    for i in range(playlists.count()):
        playlist = playlists.get(i)
	item = {'label': playlist.name, 'action':'addSongToPlaylistExec', 'handle': pickle.dumps([playlist, song], pickle.HIGHEST_PROTOCOL)}
	listItem = createItem(item)
        listItems.append(listItem)

    __window__.GetLabel(4100).SetLabel('Which?')
    __window__.GetImage(410).SetTexture('gs_addsong.png')
    __window__.GetList(500).SetItems(listItems)
    cnt.SetFocus()


def setRightMenu():
    listitems = __windowlist__.GetItems()
    listitem = listitems[0]
    state = listitem.GetProperty('state')

    listItems = False
    listImage = ''
    dict = False
    if state == 'song':
        dict = [\
            {'label':__language__(102), 'action':'play', 'thumbnail':'gs_play_item.png'},\
            {'label':__language__(101), 'action':'queueSong', 'thumbnail':'gs_enqueue.png'},\
            {'label':__language__(103), 'action':'queueAllSongs', 'thumbnail':'gs_enqueue.png'},\
            {'label':__language__(104), 'action':'addSongToPlaylist', 'thumbnail':'gs_addsong.png'},\
            {'label':__language__(119), 'action':'findSimilarFromSong', 'thumbnail':'gs_similar.png'},\
            {'label':__language__(120), 'action':'songsOnAlbum', 'thumbnail':'gs_album.png'}\
            ]
        listItems = mc.ListItems()
        listImage = 'gs_song.png'

    elif state == 'album':
        dict = [\
            {'label':__language__(125), 'action':'playAlbum', 'thumbnail':'gs_play_item.png'},\
            {'label':__language__(126), 'action':'queueAlbum', 'thumbnail':'gs_enqueue.png'},\
            {'label':__language__(127), 'action':'saveAlbumAsPlaylist', 'thumbnail':'gs_savealbum.png'},\
            {'label':__language__(119), 'action':'findSimilarFromAlbum', 'thumbnail':'gs_similar.png'}\
            ]
        listItems = mc.ListItems()
        listImage = 'gs_album.png'

    elif state == 'playlist':
	dict = [\
            {'label':__language__(111), 'action':'renamePlaylist', 'thumbnail':'gs_rename.png'},\
            {'label':__language__(112), 'action':'deletePlaylist', 'thumbnail':'gs_delete2.png'},\
            ]
        listItems = mc.ListItems()
        listImage = 'gs_playlist.png'

    elif state == 'artist':
 	dict = [\
            {'label':'Play songs', 'action':'playSongsByArtist', 'thumbnail':'gs_play_item.png'},\
            {'label':__language__(119), 'action':'findSimilarFromArtist', 'thumbnail':'gs_similar.png'},\
            ]
        listItems = mc.ListItems()
        listImage = 'gs_artist.png'

    elif state == 'search':
        cnt = __window__.GetControl(500)
        cnt.SetEnabled(False)
        return

    elif state == 'root':
        cnt = __window__.GetControl(500)
        cnt.SetEnabled(False)
        return

    if dict:
        cnt = __window__.GetControl(500)
        cnt.SetEnabled(True)
        for item in dict:
            listItem = createItem(item)
            listItems.append(listItem)
        __window__.GetLabel(4100).SetLabel('')
        __window__.GetImage(410).SetTexture(listImage)
        __window__.GetList(500).SetItems(listItems)
        cnt.SetFocus()


def decode(s):
    try:
        return urllib.unquote_plus(s)
    except:
        print s
        return "blabla"

def createItem(dict):
    listItem = mc.ListItem(mc.ListItem.MEDIA_UNKNOWN)
    try: listItem.SetLabel(dict['label'].encode('utf-8'))
    except:
        try: listItem.SetLabel(dict['label'])
        except: pass
    try: listItem.SetProperty('label2',dict['label2'].encode('utf-8'))
    except:
        try:listItem.SetProperty('label2',dict['label2'])
        except: pass
    try: listItem.SetProperty('action',dict['action'])
    except: pass
    try: listItem.SetProperty('state',dict['state'])
    except: pass
    try: listItem.SetProperty('handle',dict['handle'])
    except: pass
    try: listItem.SetThumbnail(str(dict['thumbnail']))
    except: pass
    try: listItem.SetIcon(str(dict['icon']))
    except: pass
    try: listItem.SetTitle(dict['title'].encode('utf-8'))
    except:
        try: listItem.SetTitle(dict['title'])
        except: pass
    try: listItem.SetArist(dict['artist'].encode('utf-8'))
    except:
        try: listItem.SetArist(dict['artist'])
        except: pass
    try: listItem.SetAlbum(dict['album'].encode('utf-8'))
    except:
        try: listItem.SetAlbum(dict['album'])
        except: pass
    return listItem

def checkPlayback(playlist):
    player = mc.GetPlayer()
    if playlist.Size() > 0 and not player.IsPlayingAudio() and not player.IsPaused():
        player.PlaySelected(0)