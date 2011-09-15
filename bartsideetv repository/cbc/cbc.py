from default import *
from library import *
import tools

sys.path.append(os.path.join(CWD, 'external'))

import simplejson as json
from BeautifulSoup import BeautifulSoup
from urllib import quote_plus, unquote

class Module(BARTSIDEE_MODULE):
    def __init__(self, app):
        self.app            = app
        BARTSIDEE_MODULE.__init__(self, app)

        self.name           = "CBC"                         #Name of the channel
        self.type           = ['search']                    #Choose between 'search', 'list', 'genre'
        self.episode        = False                         #True if the list has episodes
        self.content_type   = 'video/x-flv'                 #Mime type of the content to be played
        self.country        = 'CA'                          #2 character country id code
         
    def Search(self, search):
        url = 'http://www.cbc.ca/search/cbc?json=true&sitesearch=www.cbc.ca/video/watch&q=' + quote_plus(search)
        data = tools.urlopen(self.app, url)
        json_data = json.loads(data)

        streamlist = list()
        if json_data['searchResults']['numOfResults'] == "":
            return streamlist

        for info in json_data['searchResults']['items']:
            title = unquote(info['title']).replace('&amp;','&').replace('&lt;','<').replace('&gt;','>').replace('&quot;','"').replace('&#39;',"'")
            if title != "CBC.ca Player":
                stream          =   CreateList()
                stream.name     =   ''.join(BeautifulSoup(title).findAll(text=True))
                stream.id       =   info['urlEncoded']
                streamlist.append(stream)

        return streamlist
        
    def Play(self, stream_name, stream_id, subtitle):
        url = "http://tarek.org/cbc/index.php?id="+ stream_id[-10:]

        play = CreatePlay()
        play.path       =   url
        play.domain     =   'www.cbc.ca'
        play.jsactions  =   'http://www.bartsidee.nl/boxee/apps/js/cbc.js'

        return play