import mc, ba, re, datetime, time
from BeautifulSoup import BeautifulSoup
import cPickle as pickle

config = mc.GetApp().GetLocalConfig()

week = {0:'Zondag', 1:'Maandag',2:'Dinsdag',3:'Woensdag',4:'Donderdag',5:'Vrijdag',6:'Zaterdag'}

def StartUp():
    mc.ShowDialogWait()
    if ba.Cache('database' + '{0}', 3600): refresh = False
    else: refresh = True

    if refresh:
        mc.ShowDialogNotification("Loading streams...")
        url = "http://query.yahooapis.com/v1/public/yql?q=select%20*%20from%20xml%20where%20url%3D'http%3A%2F%2Fadaptive.rtl.nl%2Fxl%2FVideoItem%2FIpadXML'&_maxage=3600"
        data = ba.FetchUrl(url, 3600)
        soup = BeautifulSoup(data, convertEntities="xml", smartQuotesTo="xml")

        items = []
        for info in soup.findAll( 'item' ):
            if info.serienaam.string == info.title.string:
                item = {}
                daynr = getDate(info.broadcastdatetime.string.split('T')[0])
                item['time'] = daynr
                item['label'] = info.serienaam.string.encode('utf-8')
                item['thumb'] = str(info.thumbnail.string)
                item['desc'] = str(week[daynr]) +' - '+ info.samenvattingkort.string.encode('utf-8')
                item['path'] = str(info.movie.string)
                items.append(item)

        config.Reset('database')
        config.Reset('database')
        config.PushBackValue('database', str(time.time()).split('.')[0])
        config.PushBackValue('database', pickle.dumps(items))
    mc.HideDialogWait()

def filter_data(data, predicate=lambda k, v: True):
    for d in data:
         for k, v in d.items():
               if predicate(k, v):
                    yield d

def ShowDay(day):
    mc.ShowDialogWait()
    targetcontrol  	= 51
    targetwindow   	= 14000

    database = pickle.loads(config.GetValue('database{1}'))
    selection = list(filter_data(database, lambda k, v: k == 'time' and v == day))

    listref = mc.GetWindow(targetwindow).GetList(targetcontrol)
    list_items = mc.ListItems()

    for item in selection:
        list_item = mc.ListItem(mc.ListItem.MEDIA_VIDEO_OTHER)
        list_item.SetLabel(item['label'])
        list_item.SetThumbnail(item['thumb'])
        list_item.SetDescription(item['desc'])
        list_item.SetPath(item['path'])
        list_items.append(list_item)

    mc.HideDialogWait()
    listref.SetItems(list_items)

def getDate(datestring):
    c = time.strptime(datestring,"%Y-%m-%d")
    return int(time.strftime("%w",c))

def getToday():
    now = datetime.datetime.now()
    return int(now.strftime("%w"))