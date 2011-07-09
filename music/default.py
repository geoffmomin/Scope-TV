import mc
import os, sys
__cwd__ = os.getcwd().replace(";","")
sys.path.append(os.path.join(__cwd__, 'libs'))
sys.path.append(os.path.join(__cwd__, 'external'))

import tracker
myTracker = tracker.Tracker('UA-19866820-2')

if ( __name__ == "__main__" ):
    mc.ActivateWindow(14000)

    import app
    app.down(id=55, path="home", push=False)
    myTracker.trackView('home')


