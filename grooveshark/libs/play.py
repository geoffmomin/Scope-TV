import os
import sys
import mc
import traceback

__scriptid__ = mc.GetApp().GetId()
__cwd__ = mc.GetApp().GetAppDir()
__settings__ = mc.GetApp().GetLocalConfig()
__debugging__ = False
__parameters__ = mc.GetApp().GetLaunchedScriptParameters()
sys.path.append(os.path.join(__cwd__, 'libs'))


print 'GrooveShark: play script started'

org_url = ''
for i in sys.argv:
    org_url += str(i).replace('.py','?')
for var in __parameters__.keys():
    vars()[var] = __parameters__[var]

from GrooveAPI import *
try:
    gs = GrooveAPI(enableDebug = __debugging__, cwd = __cwd__,clientUuid = None, clientVersion = None)
    gs.startSession('','')

    if (playSong != None):
        print 'GrooveShark: Song ID: ' + str(playSong)
        url = gs.getStreamURL(str(playSong))
        if url != "":
            listItem = mc.ListItem(mc.ListItem.MEDIA_AUDIO_MUSIC)
            listItem.SetPath(str(url))
            listItem.SetProperty('info', str(org_url))
            listItem.SetContentType('audio/mpeg')
            listItem.SetTitle(songName)
            listItem.SetThumbnail(image)
            listItem.SetIcon(image)
            listItem.SetAlbum(albumName)
            listItem.SetArtist(artistName)

            print 'GrooveShark: Found stream url: (' + url + ')'
            playlist = mc.PlayList(mc.PlayList.PLAYLIST_MUSIC)
            listItems = []
            append = False
            for i in range(playlist.Size()):
                item = playlist.GetItem(i)
                if item.GetTitle() == songName:
                    append = True
                    listItems.append(listItem)
                elif append: listItems.append(item)
            playlist.Clear()
            for item in listItems:
                playlist.Add(item)
            mc.GetPlayer().PlaySelected(0)
            print 'GrooveShark: ####### Finished'
        else:
            print 'GrooveShark: No stream url returned for song id' 
    else:
        print 'GrooveShark: Unknown command'
except:
    traceback.print_exc()
