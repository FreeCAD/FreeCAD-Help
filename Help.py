# -*- coding: utf-8 -*-

# ***************************************************************************
# *   Copyright (c) 2021 Yorik van Havre <yorik@uncreated.net>              *
# *                                                                         *
# *   This program is free software; you can redistribute it and/or modify  *
# *   it under the terms of the GNU Lesser General Public License (LGPL)    *
# *   as published by the Free Software Foundation; either version 2 of     *
# *   the License, or (at your option) any later version.                   *
# *   for detail see the LICENCE text file.                                 *
# *                                                                         *
# *   This program is distributed in the hope that it will be useful,       *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
# *   GNU Library General Public License for more details.                  *
# *                                                                         *
# *   You should have received a copy of the GNU Library General Public     *
# *   License along with this program; if not, write to the Free Software   *
# *   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
# *   USA                                                                   *
# *                                                                         *
# ***************************************************************************

"""
Provide tools to access the FreeCAD documentation.

The main usage is using the "show" function. It can retrieve an URL,
a local file (markdown or html), or find a page automatically from
the settings set under Preferences->General->Help.

It doesn't matter what you give, the system will recognize if the contents are
HTML or Markdown and render it appropriately.

Basic usage:

    import Help
    Help.show("Draft Line")
    Help.show("Draft_Line") # works with spaces or underscores
    Help.show("https://wiki.freecadweb.org/Draft_Line")
    Help.show("https://gitlab.com/freecad/FreeCAD-documentation/-/raw/main/wiki/Draft_Line.md")
    Help.show("/home/myUser/.FreeCAD/Documentation/Draft_Line.md")
    Help.show("http://myserver.com/myfolder/Draft_Line.html")

Preferences keys (in "User parameter:BaseApp/Preferences/Mod/Help"):

    optionBrowser/optionTab/optionDialog (bool): Where to open the help dialog
    optionOnline/optionOffline (bool): where to fetch the documentation from
    URL (string): online location
    Location (string): offline location
    Suffix (string): a suffix to add to the URL, ex: /fr
    StyleSheet (string): optional CSS stylesheet to style the output
"""

import os
import urllib
import re
import FreeCAD
from PySide2 import QtCore

translate = FreeCAD.Qt.translate
QT_TRANSLATE_NOOP = FreeCAD.Qt.QT_TRANSLATE_NOOP

# texts and icons
ERRORTXT = translate("Help","Contents for this page could not be retrieved. Please check settings under menu Edit -> Preferences -> General -> Help")
LOCTXT = translate("Help","Help files location could not be determined. Please check settings under menu Edit -> Preferences -> General -> Help")
LOGTXT = translate("Help","PySide2 QtWebEngineWidgets module is not available. Help rendering is done with the Web module")
CONVERTTXT = translate("Help","There is no markdown renderer installed on your system, so this help page is rendered as is. Please install the markdown or pandoc python modules to improve the rendering of this page.")
PREFS = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Help")
ICON = ":/icons/help-browser.svg"

# menu building - not uesd yet
MENU_LINKS =    [ [translate("Help", "Home"),             "https://freecad.org"],
                  [translate("Help", "Forum"),            "https://forum.freecad.org"],
                  [translate("Help", "Wiki"),             "https://wiki.freecad.org"],
                  [translate("Help", "Issues"),           "https://github.com/FreeCAD/FreeCAD/issues"],
                  [translate("Help", "Code repository"),  "https://github.com/FreeCAD/FreeCAD"],
                ]
MENU_COMMANDS = [ ["applications-python.svg", translate("Help","Auto Python modules"), None,       "Std_PythonHelp"],
                  ["freecad.svg",             translate("Help","About FreeCAD"),       None,       "Std_About"],
                  ["WhatsThis.svg",           translate("Help","What's this?"),        "Shift+F1", "Std_WhatsThis"],
                ]

# redirects
SUBSTITUTES =   { "Main_Page":             "README",
                  "Online_Help_Startpage": "README",
                }

def show(page,view=None,conv=None):

    """
    show(page,view=None):
    Opens a help viewer and shows the given help page.
    The given help page can be a URL pointing to a markdown or HTML file,
    a name page / command name, or a file path pointing to a markdown
    or HTML file. If view is given (an instance of openBrowserHTML.HelpPage or
    any other object with a 'setHtml()' method), the page will be
    rendered there, otherwise a new tab/widget will be created according to
    preferences settings. If conv is given (markdown, pandoc, github, builtin or
    none), the corresponding markdown conversion method is used. Otherwise, the
    module will use the best available.
    In non-GUI mode, this function simply outputs the markdown or HTML text.
    """

    page = underscore_page(page)
    location = get_location(page)
    FreeCAD.Console.PrintLog("Help: opening "+location+"\n")
    if not location:
        FreeCAD.Console.PrintError(LOCTXT+"\n")
        return
    md = get_contents(location)
    html = convert(md,conv)
    baseurl = get_uri(location)
    pagename = os.path.basename(page.replace("_"," ").replace(".md",""))
    title = translate("Help","Help")+": " + pagename
    if FreeCAD.GuiUp:
        if PREFS.GetBool("optionBrowser",False): # desktop web browser
            show_browser(location)
        elif PREFS.GetBool("optionDialog",False): # floating dock window
            show_dialog(html,baseurl,title,view)
        else: # MDI tab
            show_tab(html,baseurl,title,view)
    else:
        # console mode, we just print the output
        print(md)



def underscore_page(page):

    """change spaces by underscores in the given page name"""

    if "/" in page:
        page = page.split("/")
        page[-1] = page[-1].replace(" ","_")
        page = "/".join(page)
    else:
        page.replace(" ","_")
    return page



def get_uri(location):
    
    """returns a valid URI from a disk or network location"""

    baseurl = os.path.dirname(location) + "/"
    if baseurl.startswith("/"): # unix path
        baseurl = "file://" + baseurl
    if baseurl[0].isupper() and (baseurl[1] == ":"): # windows path
        baseurl = baseurl.replace("\\","/")
        baseurl = "file:///" + baseurl
    return baseurl



def get_location(page):

    """retrieves the location (online or offline) of a given page"""

    location = ""
    if page.startswith("http"):
        return page
    if page.startswith("file://"):
        return page[7:]
    # offline location
    if os.path.exists(page):
        return page
    page = page.replace(".md","")
    page = page.replace(" ","_")
    page = page.replace("wiki/","")
    page = page.split("#")[0]
    if PREFS.GetBool("optionOnline",True):
        location = PREFS.GetString("URL","")
        if not location:
            if PREFS.GetBool("optionBrowser",False):
                location = "https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/"
            else:
                location = "https://raw.githubusercontent.com/FreeCAD/FreeCAD-documentation/main/wiki"
        if (page in SUBSTITUTES) and not ("wiki." in location):
            page = SUBSTITUTES[page]
        if page.endswith("README") and location.endswith("wiki"):
            # use README outside the wiki folder for now...
            location = location[:-4]
        if not location.endswith("/"):
            location += "/"
        location += page
        if not ("wiki." in location):
            location += ".md"
    else:
        location = PREFS.GetString("Location","")
        if not location:
            location = os.path.join(FreeCAD.getUserAppDataDir(),"Mod","Documentation","wiki")
        if (page in SUBSTITUTES):
            page = SUBSTITUTES[page]
        if page.endswith("README") and location.endswith("wiki"):
            # use README outside the wiki folder for now...
            location = location[:-4]
        if os.path.exists(os.path.join(location,page+".html")):
            location = os.path.join(location,page)
        else:
            location = os.path.join(location,page+".md")
    suffix = PREFS.GetString("Suffix","")
    if suffix:
        if not suffix.startswith("/"):
            suffix = "/" + suffix
        location += suffix
    return location



def show_browser(url):
    
    """opens the desktop browser with the given URL"""
    
    from PySide2 import QtGui
    try:
        QtGui.QDesktopServices.openUrl(QtCore.QUrl(url))
    except:
        # some users reported problems with the above
        import webbrowser
        webbrowser.open_new(url)



def show_dialog(html,baseurl,title,view=None):
    
    """opens a dock dialog with the given html"""

    if get_qtwebwidgets(html,baseurl,title):
        if view: # reusing existing view
            view.setHtml(html,baseUrl=QtCore.QUrl(baseurl))
            view.parent().parent().setWindowTitle(title)
        else:
            openBrowserHTML(html,baseurl,title,ICON,dialog=True)



def show_tab(html,baseurl,title,view=None):
    
    """opens a MDI tab with the given html"""

    if get_qtwebwidgets(html,baseurl,title):
        if view: # reusing existing view
            view.setHtml(html,baseUrl=QtCore.QUrl(baseurl))
            view.parent().parent().setWindowTitle(title)
        else:
            openBrowserHTML(html,baseurl,title,ICON)



def get_qtwebwidgets(html,baseurl,title):
    
    """opens a web module view if qtwebwidgets module is not available, and returns False"""

    try:
        from PySide2 import QtGui, QtWebEngineWidgets
    except:
        FreeCAD.Console.PrintLog(LOGTXT+"\n")
        import WebGui
        WebGui.openBrowserHTML(html,baseurl,title,ICON)
        return False
    else:
        return True



def get_contents(location):

    """retrieves text contents of a given page"""

    if location.startswith("http"):
        import urllib.request
        try:
            r = urllib.request.urlopen(location)
        except:
            return ERRORTXT
        contents = r.read().decode("utf8")
        return contents
    else:
        if os.path.exists(location):
            with open(location, mode='r', encoding='utf8') as f:
                contents = f.read()
            return contents
    return ERRORTXT



def convert(content,force=None):

    """converts the given markdown code to html. Force can be None (automatic)
    or markdown, pandoc, github or raw/builtin"""

    def convert_markdown(m):
        try:
            import markdown
            from markdown.extensions import codehilite
            return markdown.markdown(m,extensions=['codehilite'])
        except:
            return None

    def convert_pandoc(m):
        try:
            import pypandoc
            return pypandoc.convert_text(m,"html",format="md")
        except:
            return None

    def convert_github(m):
        try:
            import json
            import urllib.request
            data = {"text": m, "mode": "markdown"}
            bdata = json.dumps(data).encode('utf-8')
            return urllib.request.urlopen("https://api.github.com/markdown",data=bdata).read().decode("utf8")
        except:
            return None

    def convert_raw(m):
        # simple and dirty regex-based markdown to html
        f = re.DOTALL|re.MULTILINE
        m = re.sub(r"^##### (.*?)\n",r"<h5>\1</h5>\n",m,flags=f) # ##### titles
        m = re.sub(r"^#### (.*?)\n", r"<h4>\1</h4>\n",m,flags=f) # #### titles
        m = re.sub(r"^### (.*?)\n",  r"<h3>\1</h3>\n",m,flags=f) # ### titles
        m = re.sub(r"^## (.*?)\n",   r"<h2>\1</h2>\n",m,flags=f) # ## titles
        m = re.sub(r"^# (.*?)\n",    r"<h1>\1</h1>\n",m,flags=f) # # titles
        m = re.sub(r"!\[(.*?)\]\((.*?)\)", r'<img alt="\1" src="\2">',m,flags=f) # images
        m = re.sub(r"\[(.*?)\]\((.*?)\)",  r'<a href="\2">\1</a>',m,flags=f) # links
        m = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>",m) # bold
        m = re.sub(r"\*(.*?)\*", r"<i>\1</i>",m) # italic
        m = re.sub(r"\n\n", r"<br/>",m,flags=f) # double new lines
        m += "\n<br/><hr/><small>" + CONVERTTXT + "</small>"
        return m

    if "<html" in content:
        # this is html already
        return content

    if force == "markdown":
        html = convert_markdown(content)
    elif force == "pandoc":
        html = convert_pandoc(content)
    elif force == "github":
        html = convert_github(content)
    elif force in ["raw","builtin"]:
        html = convert_raw(content)
    elif force == "none":
        return content
    else:
        # auto mode
        html = convert_pandoc(content)
        if not html:
            html = convert_markdown(content)
            if not html:
                html = convert_raw(content)
    if not "<html" in html:
        html = "<html>\n<head>\n<meta charset=\"utf-8\"/>\n</head>\n<body>\n\n"+html+"</body>\n</html>"
    # insert css
    css = None
    cssfile = PREFS.GetString("StyleSheet","")
    if not cssfile:
        cssfile = os.path.join(os.path.dirname(__file__),"default.css")
    if False: # linked CSS file
        # below code doesn't work in FreeCAD apparently because it prohibits cross-URL stuff
        cssfile = urllib.parse.urljoin('file:',urllib.request.pathname2url(cssfile))
        css = "<link rel=\"stylesheet\" type=\"text/css\" href=\""+cssfile+"\"/>"
    else:
        if os.path.exists(cssfile):
            with open(cssfile) as cf:
                css = cf.read()
            if css:
                css = "<style>\n"+css+"\n</style>"
        else:
            print("Debug: Help: Unable to open css file:",cssfile)
    if css:
        html = html.replace("</head>",css+"\n</head>")
    return html



def add_preferences_page():

    """adds the Help preferences page to the UI"""

    import FreeCADGui
    page = os.path.join(os.path.dirname(__file__),"dlgPreferencesHelp.ui")
    FreeCADGui.addPreferencePage(page,QT_TRANSLATE_NOOP("QObject", "General"))



def add_menu():

    """adds the Help menu of FreeCAD"""

    import FreeCADGui
    if hasattr(FreeCADGui,"HelpMenu"):
        mb = FreeCADGui.getMainWindow().menuBar()
        mb.addMenu(FreeCADGui.HelpMenu)



def build_menu():

    """creates and populates a help menu. Menu creation takes several
    seconds to fullfill due to the big number of entries."""

    import FreeCADGui
    from PySide2 import QtGui
    menu = QtGui.QMenu(translate("Help","Help"))
    menu.setObjectName("Help")

    # On the web
    sub =  QtGui.QMenu(translate("Help","On the web"), menu)
    for it in MENU_LINKS:
        act = QtGui.QAction(it[0], sub)
        act.setToolTip(it[1])
        act.triggered.connect(lambda f=show,arg=it[1]:f(arg))
        sub.addAction(act)
    menu.addMenu(sub)

    # Documentation
    cache = os.path.join(FreeCAD.getUserAppDataDir(),"Help","menu.md")
    if not os.path.exists(cache):
        get_menu_structure()
    if os.path.exists(cache):
        doc =  QtGui.QMenu(translate("Help","Documentation"), menu)
        act = QtGui.QAction("Index", doc)
        act.setShortcut("F1")
        act.setToolTip(translate("Help","Shows the index page of the FreeCAD documentation"))
        act.triggered.connect(lambda: show("Main Page"))
        doc.addAction(act)
        with open(cache) as f:
            for line in f:
                name = line[line.index("[")+1:line.index("]")]
                link = line[line.index("(")+1:line.index(")")]
                if line.startswith("-"):
                    sub = QtGui.QMenu(name, menu)
                    doc.addMenu(sub)
                else:
                    act = QtGui.QAction(name, sub)
                    act.setToolTip(link)
                    act.triggered.connect(lambda f=show,arg=link:f(arg))
                    sub.addAction(act)
        menu.addMenu(doc)

    # Special FreeCAD Help commands
    for it in MENU_COMMANDS:
        if it[0]:
            act = QtGui.QAction(QtGui.QIcon(":/icons/"+it[0]),it[1], menu)
        else:
            act = QtGui.QAction(it[1], menu)
        if it[2]:
            act.setShortcut(it[2])
        act.triggered.connect(lambda f=FreeCADGui.runCommand,arg=it[3]:f(arg))
        menu.addAction(act)

    # store menu to FreeCAD for faster access and possible modification by addons
    FreeCADGui.HelpMenu = menu



def get_menu_structure():

    """fetches menu structure from documentation"""

    location = get_location("Online Help Toc")
    if not location:
        return
    md = get_contents(location)
    d = os.path.join(FreeCAD.getUserAppDataDir(),"Help")
    if not os.path.isdir(d):
        os.makedirs(d)
    cache = os.path.join(d,"menu.md")
    with open(cache,"w") as f:
        f.write(md)



def openBrowserHTML(html,baseurl,title,icon,dialog=False):

    """creates a browser view and adds it as a FreeCAD MDI tab or dockable dialog"""

    import FreeCADGui
    from PySide2 import QtGui, QtWidgets, QtWebEngineWidgets

    # turn an int into a qt dock area
    def getDockArea(area):
        if area == 1:
            return QtCore.Qt.LeftDockWidgetArea
        elif area == 4:
            return QtCore.Qt.TopDockWidgetArea
        elif area == 8:
            return QtCore.Qt.BottomDockWidgetArea
        else:
            return QtCore.Qt.RightDockWidgetArea

    # save dock widget size and location
    def onDockLocationChanged(area):
        PREFS.SetInt("dockWidgetArea",int(area))
        mw = FreeCADGui.getMainWindow()
        dock = mw.findChild(QtWidgets.QDockWidget,"HelpWidget")
        if dock:
            PREFS.SetBool("dockWidgetFloat",dock.isFloating())
            PREFS.SetInt("dockWidgetWidth",dock.width())
            PREFS.SetInt("dockWidgetHeight",dock.height())

    # a custom page that handles .md links
    class HelpPage(QtWebEngineWidgets.QWebEnginePage):
        def acceptNavigationRequest(self, url,  _type, isMainFrame):
            if _type == QtWebEngineWidgets.QWebEnginePage.NavigationTypeLinkClicked:
                show(url.toString(),view=self)
            return super().acceptNavigationRequest(url,  _type, isMainFrame)

    mw = FreeCADGui.getMainWindow()
    view = QtWebEngineWidgets.QWebEngineView()
    page = HelpPage(None,view)
    page.setHtml(html,baseUrl=QtCore.QUrl(baseurl))
    view.setPage(page)

    if dialog:
        area = PREFS.GetInt("dockWidgetArea",2)
        floating = PREFS.GetBool("dockWidgetFloat",True)
        height = PREFS.GetBool("dockWidgetWidth",200)
        width = PREFS.GetBool("dockWidgetHeight",300)
        dock = mw.findChild(QtWidgets.QDockWidget,"HelpWidget")
        if not dock:
            dock = QtWidgets.QDockWidget()
            dock.setObjectName("HelpWidget")
            mw.addDockWidget(getDockArea(area),dock)
            dock.setFloating(floating)
            dock.setGeometry(dock.x(),dock.y(),width,height)
            dock.dockLocationChanged.connect(onDockLocationChanged)
        dock.setWidget(view)
        dock.setWindowTitle(title)
        dock.setWindowIcon(QtGui.QIcon(icon))
        dock.show()
    else:
        mdi = mw.findChild(QtWidgets.QMdiArea)
        sw = mdi.addSubWindow(view)
        sw.setWindowTitle(title)
        sw.setWindowIcon(QtGui.QIcon(icon))
        sw.show()
        mdi.setActiveSubWindow(sw)
