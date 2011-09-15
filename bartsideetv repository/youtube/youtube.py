from default import *
from library import *
import tools

sys.path.append(os.path.join(CWD, 'external'))

import simplejson as json
from BeautifulSoup import BeautifulSoup
from urllib import quote_plus, unquote_plus
from itertools import izip

class Module(BARTSIDEE_MODULE):
    def __init__(self, app):
        self.app            = app
        BARTSIDEE_MODULE.__init__(self, app)

        self.name           = "Youtube"                     #Name of the channel
        self.type           = ['search']                    #Choose between 'search', 'list', 'genre'
        self.episode        = True                          #True if the list has episodes
        self.country        = ''                            #2 character country id code
        self.content_type   = ''

        self.url_base       = 'http://gdata.youtube.com'


    def Search(self, search):
        url  = 'http://suggestqueries.google.com/complete/search?client=youtube&jsonp=yt&q=' + quote_plus(search)
        data = tools.urlopen(self.app, url)
        data = re.compile('yt\((.*?)\)$', re.DOTALL + re.IGNORECASE).search(data).group(1)
        json_data = json.loads(data)

        streamlist = list()
        for info in json_data[1]:
            stream          = CreateList()
            stream.name     = info[0]
            stream.id       = info[0]
            streamlist.append(stream)

        return streamlist

    def Episode(self, show_name, show_id, page, totalpage):
        url = self.url_base + '/feeds/api/videos?q=' + quote_plus(show_id) + '&start-index=1&max-results=20&format=5&orderby=viewCount'
        data = tools.urlopen(self.app, url)
        soup = BeautifulSoup(data, convertEntities="xml", smartQuotesTo="xml")

        title = [info.string for info in soup.findAll('title')]
        path  = [re.compile('v\/(.*?)\?').search(info['url']).group(1) for info in soup.findAll('media:content', {'isdefault' : 'true'})]
        thumb = [info['url'] for info in soup.findAll('media:thumbnail', {'height' : '360'})]
        desc  = [info.string for info in soup.findAll('content')]
        pup   = [info.string[0:10] for info in soup.findAll('published')]


        title.pop(0)

        episodelist = list()
        for title_i,path_i,thumb_i,desc_i,pup_i in izip(title,path,thumb,desc,pup):
            episode             = CreateEpisode()
            episode.name        = title_i
            episode.id          = path_i
            episode.description = desc_i
            episode.thumbnails  = thumb_i
            episode.date        = pup_i
            episode.page        = page
            episode.totalpage   = totalpage
            episodelist.append(episode)

        return episodelist

    def Play(self, stream_name, stream_id, subtitle):
        url, ext = self.YouTube(stream_id)

        play        = CreatePlay()
        play.path   = url
        play.content_type   =   'video/%s' % ext

        return play


    def YouTube(self, id):

        url = 'http://www.youtube.com/get_video_info?video_id=%s' % id
        html = tools.urlopen(self.app, url)

        try:
            results    = re.compile('(%26itag%3D)').search(html).groups()[0]
            searchdata = html
        except: results = ''

        if not results:
            url  = 'http://www.youtube.com/watch?v=%s' % id
            html = tools.urlopen(self.app, url)
            searchdata = re.compile('flashvars="([^"]+)').search(html).groups()[0]

        formats = {
            '17': 'mp4',
            '18': 'mp4',
            '22': 'mp4',
            '37': 'mp4',
            '38': 'video',
            '43': 'webm',
            '45': 'webm',
            '34': 'flv',
            '5' : 'flv',
            '0' : 'flv',
            }
        result = None
        ext = None

        searchdata = unquote_plus(searchdata)
        for key in formats.keys():
            if result:
                continue

            try:    playurl = re.compile('[=,]url=([^&]+)[^,]+&itag=%s' % key).search(searchdata).groups()[0]
            except: playurl = ''

            print playurl

            if playurl:
                result = unquote_plus(playurl)
                ext    = formats[key]

        return result, ext