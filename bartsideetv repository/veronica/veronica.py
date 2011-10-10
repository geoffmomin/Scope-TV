from default import *
from library import *
import tools

sys.path.append(os.path.join(CWD, 'external'))

from BeautifulSoup import BeautifulSoup
from urllib import quote_plus

import httplib
from pyamf import remoting

class Module(BARTSIDEE_MODULE):
    def __init__(self, app):
        self.app            = app
        BARTSIDEE_MODULE.__init__(self, app)

        self.name           = "Veronica Gemist"                     #Name of the channel
        self.type           = ['list']                          #Choose between 'search', 'list', 'genre'
        self.episode        = True                              #True if the list has episodes
        self.content_type   = 'video/x-flv'                     #Mime type of the content to be played
        self.country        = 'NL'                              #2 character country id code


        self.url_base       = 'http://www.veronicatv.nl'

    def List(self):
        index = ['0-9abcdef', 'ghijkl', 'mnopqr', 'stuvwxyz']
        data = []

        for i in index:
            url  = self.url_base + '/ajax/programFilter/day/0/genre/all/block/programs/range/' + i
            data.extend(self.process(url))

        streamlist = []
        for item in data:
            stream = CreateList()
            stream.name     =   item['label']
            stream.id       =   item['id']
            streamlist.append(stream)

        return streamlist

    def Episode(self, stream_name, stream_id, page, totalpage):
        url  = str(stream_id) + '/afleveringen'
        data = tools.urlopen(self.app, url, {'cache':3600})


        if data.rfind('Programma Video') != -1:
            parse = '/afleveringen'
        else:
            url   = str(stream_id) + '/videos'
            data  = tools.urlopen(self.app, url, {'cache':3600})
            parse = '/videos'
            
        soup = BeautifulSoup(data, convertEntities=BeautifulSoup.HTML_ENTITIES, smartQuotesTo="xml")
        
        try:
            submenu   = soup.findAll('div', {'class' : 'subMenu'})[0]
            pages     = submenu.findAll('li')
            totalpage = len(pages)
        except:
            totalpage = 1

        if page != 1:
            i    = totalpage - page
            id   = str(pages[i].a.contents[0])
            url  = str(stream_id) + parse + '/' + id.replace(' ', '-')
            data = tools.urlopen(self.app, url, {'cache':3600})
            soup = BeautifulSoup(data, convertEntities=BeautifulSoup.HTML_ENTITIES, smartQuotesTo="xml")
        else:
            try:    id   = str(pages[totalpage-1].a.contents[0])
            except: id = ''

        if parse == '/afleveringen':
            episodes = soup.findAll('div', {'class' : 'i iMargin iEpisode iBorder'})

            if not episodes:
                return []

            episodelist = []
            for item in episodes:
                body  = item.findAll('div', {'class' : 'iBody'})
                url   = item.findAll('a',   {'class' : 'btnSmall'})

                if not url or not body:
                    continue

                if not 'Video' in url[0].prettify():
                    continue

                p = body[0].findAll('p')

                episode                 =   CreateEpisode()
                episode.name            =   body[0].h2.string
                episode.id              =   self.url_base + url[0]['href']
                episode.thumbnails      =   self.url_base + item.find('img')['src']
                episode.date            =   p[0].string
                episode.description     =   id + ' ' + tools.encodeUTF8(p[1].string)
                episode.page            =   page
                episode.totalpage       =   totalpage
                episodelist.append(episode)

        elif parse == '/videos':
            episodes = soup.findAll('div', {'class' : 'i iGuide iGuideSlider'})

            if not episodes:
                return []

            episodelist = []
            for item in episodes:
                body  = item.findAll('div', {'class' : 'iBody'})
                url   = item.findAll('a',   {'class' : 'm mMargin'})

                if not url or not body:
                    continue

                p = body[0].findAll('p')

                episode                 =   CreateEpisode()
                episode.name            =   body[0].h2.string
                episode.id              =   self.url_base + url[0]['href']
                episode.thumbnails      =   self.url_base + item.find('img')['src']
                episode.description     =   id
                episode.date            =   p[0].string
                episode.page            =   page
                episode.totalpage       =   totalpage
                episodelist.append(episode)

        return episodelist

    def Play(self, stream_name, stream_id, subtitle):
        data  = tools.urlopen(self.app, str(stream_id), {'cache':3600})
        videoPlayer = re.compile('videoPlayer\\\\" value=\\\\"(.*?)\\\\"', re.DOTALL + re.MULTILINE).search(str(data)).group(1)

        const       = '0559229564fa55a266eeeac4b89a5b9f75568382'
        playerID    = 1150434888001
        publisherID = 585049245001

        data = get_clip_info(const, playerID, videoPlayer, publisherID)
        streams = {}
        for i in data['renditions']:
            stream = {}
            stream["uri"] = i["defaultURL"]
            streams[i["encodingRate"]] = stream

        sort = []
        for key in sorted(streams.iterkeys()):
            sort.append(int(key))
            sort = sorted(sort)

        quality = sort.pop()
        rtmp = streams[int(quality)]["uri"]
        domain, file  = rtmp.split('/&')

        play                =   CreatePlay()
        play.content_type   =   'video/x-flv'
        play.rtmpurl        =   file
        play.rtmpdomain     =   domain

        return play

    def process(self, url):
        html = tools.urlopen(self.app, url, {'cache':3600})
        soup = BeautifulSoup(html, convertEntities=BeautifulSoup.HTML_ENTITIES, smartQuotesTo="xml")
        data = []

        div_main = soup.findAll('div', {'class' : 'i iGrid'})
        if not div_main:
            return data

        for div in div_main:
            thumb = self.url_base + div.a.img['src']
            label = div.div.h2.a.contents[0]
            id   = self.url_base + div.div.h2.a['href']
            data.append({'label':label, 'thumb':thumb, 'id':id,})

        return data

def build_amf_request(const, playerID, videoPlayer, publisherID):
    env = remoting.Envelope(amfVersion=3)
    env.bodies.append(
        (
            "/1",
            remoting.Request(
                target="com.brightcove.player.runtime.PlayerMediaFacade.findMediaById",
                body=[const, playerID, videoPlayer, publisherID],
                envelope=env
            )
        )
    )
    return env

def get_clip_info(const, playerID, videoPlayer, publisherID):
    conn = httplib.HTTPConnection("c.brightcove.com")
    envelope = build_amf_request(const, playerID, videoPlayer, publisherID)
    conn.request("POST", "/services/messagebroker/amf?playerKey=AQ~~,AAAAiDenBUk~,YtnxvBxGO01r9gxOuuHWiaCghjgdvn7c", str(remoting.encode(envelope).read()), {'content-type': 'application/x-amf'})
    response = conn.getresponse().read()
    response = remoting.decode(response).bodies[0][1].body
    return response