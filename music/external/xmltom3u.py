import plistloader, os, urllib
import urlparse

def itunesconvert(library, musicpath, m3upath):
    m3uHeader = "#EXTM3U\n"

    if not os.path.isfile(library):
        print "Library doesn't exist."
	return
    if not os.path.isdir(m3upath):
        print "Playlist Directory doesn't exist."
	return

    # Load the playlist using the plistloader module
    playlist = plistloader.load(library)

    music_folder_path = playlist['Music Folder']
    seperator = getSeperator(musicpath)
    # Iterate through all playlists
    for p in playlist['Playlists']:

	# Be sure that it's a music playlist withs tracks items
	if 'Playlist Items' in p:

            name=p['Name']
            # dictionnary with all tracks {'Track ID : 4042},{'Track ID : 4046}, etc
            tracks = p['Playlist Items']

            # choose the file name from the playlist name
            outfn= os.path.join(m3upath, name+'.m3u')
            # open the future playlist file
            try:
                outf = open(outfn, 'w')
            except:
                continue
            # Write the m3u Header
            outf.write(m3uHeader)
	
            # Iterate through all tracks in the current playlist
            for t in tracks:
		track_id = t['Track ID']
		fileloc_quote = playlist['Tracks'][str(track_id)]['Location']
		# iTunes put quote to transform space to %20 and so, we have to convert them
		fileloc = urllib.unquote(fileloc_quote)

		# Replace old location to the new location
		fileloc = fileloc.replace(music_folder_path, musicpath).replace('/', seperator)
		# write the file location in the playlist file
		outf.write(fileloc+"\n")

            outf.close()

def getSeperator(path):
    if '\\' in path:
        return '\\'
    else:
        return '/'