import mc
import os, sys
__cwd__ = os.getcwd().replace(";","")
sys.path.append(os.path.join(__cwd__, 'libs'))

import tracker
myTracker = tracker.Tracker('UA-19866820-2')

if ( __name__ == "__main__" ):
    mc.ActivateWindow(14000)
    myTracker.trackView('home')

    import app
    app.StartUp()
    app.ShowDay(app.getToday())
