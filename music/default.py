import mc

try:    app._cover.start()
except: pass

if ( __name__ == "__main__" ):
    mc.ActivateWindow(17000)

    import app
    app._cover.start()
    app.down(id=55, path="home", push=False)


