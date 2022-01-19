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
    Help.show("Draft_Line") # works with spaces ro underscores
    Help.show("https://wiki.freecadweb.org/Draft_Line")
    Help.show("https://gitlab.com/freecad/FreeCAD-documentation/-/raw/main/wiki/Draft_Line.md")
    Help.show("/home/myUser/.FreeCAD/Documentation/Draft_Line.md")
    Help.show("http://myserver.com/myfolder/Draft_Line.html")
    
Preferences keys (in "User parameter:BaseApp/Preferences/Mod/Help"):

    optionBrowser/optionTab/optionDialog (bool): Where to open the help dialog
    URL (string): online location
    Location (string): offline location
    StyleSheet (string): optional CSS stylesheet to style the output
"""

import os
import FreeCAD
import urllib
import re

translate = FreeCAD.Qt.translate
QT_TRANSLATE_NOOP = FreeCAD.Qt.QT_TRANSLATE_NOOP
ERRORTXT = "###" + translate("Help","Error") + "\n\n" + translate("Help","Contents for this page could not be retrieved. Check settings under menu Edit -> Preferences -> General -> Help")
WARNINGTXT = translate("Help","PySide2 QtWebEngineWidgets module is not available. Rendering is done with the Web module")
LOCTXT = translate("Help","Help files location could not be determined. Please check Edit -> Preferences -> General -> Help")
CONVERTTXT = translate("Help","There is no markdown renderer installed on your system, so this help page is rendered as is. Please install the markdown or pandoc python modules to improve the rendering of this page.")
PREFS = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Help")
ICON = ":/icons/help-browser.svg"


def show(page,view=None):

    """
    show(page,view=None):
    Opens a help viewer and shows the given help page.
    The given help page can be a URL pointing to a markdown file,
    a name page / command name, or a file path pointing to a markdown
    file. If view is given (an instance of openBrowserHTML.HelpPage or
    any other widget with a 'setHtml()' method), the page will be
    rendered there, otherwise in a new tab/widget
    """

    page = page.replace(" ","_")
    location = get_location(page)
    FreeCAD.Console.PrintLog("Help: opening "+location+"\n")
    if not location:
        FreeCAD.Console.PrintError(LOCTXT+"\n")
        return
    md = get_contents(location)
    html = convert(md)
    baseurl = os.path.dirname(location) + "/"
    pagename = os.path.basename(page.replace("_"," ").replace(".md",""))
    title = translate("Help","Help")+": " + pagename
    if FreeCAD.GuiUp:
        from PySide2 import QtCore,QtGui
        if PREFS.GetBool("optionBrowser",True):
            QtGui.QDesktopServices.openUrl(QtCore.QUrl(location))
        else:
            try:
                from PySide2 import QtWebEngineWidgets
            except:
                # QtWebEngineWidgets not present, use the Web module
                FreeCAD.Console.PrintWarning(WARNINGTXT+"\n")
                import WebGui
                WebGui.openBrowserHTML(html,baseurl,title,ICON)
            else:
                if view:
                    view.setHtml(html,baseUrl=QtCore.QUrl(baseurl))
                    #view.parent.parent.setWindowTitle(title)
                elif PREFS.GetBool("optionDialog",True):
                    openBrowserHTML(html,baseurl,title,ICON,dialog=True)
                else:
                    openBrowserHTML(html,baseurl,title,ICON)
    else:
        # everything failed, we just print the output for now...
        print(md)



def get_location(page):

    """retrieves the location (online or offline) of a given page"""

    location = ""
    if page.startswith("http"):
        return page
    page = page.replace(".md","")
    if PREFS.GetBool("optionOnline",True):
        location = PREFS.GetString("URL","")
        if not location:
            location = "https://raw.githubusercontent.com/FreeCAD/FreeCAD-documentation/main/wiki"
        if not location.endswith("/"):
            location += "/"
        location += page
        if not ("wiki." in location):
            location += ".md"
    else:
        location = PREFS.GetString("Location","")
        if not location:
            location = os.path.join(FreeCAD.getUserAppDataDir(),"Mod","Documentation")
        if os.path.exists(os.path.join(location,page+".html")):
            location = os.path.join(location,page)
        else:
            location = os.path.join(location,page+".md")
    return location



def get_contents(location):

    """retrieves text contents of a given page"""

    if location.startswith("http"):
        try:
            r = urllib.request.urlopen(location)
        except:
            return ERRORTXT
        contents = r.read().decode("utf8")
        return contents
    else:
        if os.path.exists(location):
            with open(location) as f:
                contents = f.read()
            return contents
    return ERRORTXT



def convert(content,force=None):

    """converts the given markdown code to html. Force can be None (automatic)
    or markdown, pandoc, github or raw"""

    def convert_markdown(m):
        try:
            import markdown
            return markdown.markdown(m,extensions=[markdown.extensions.codehilite])
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
            data = {"text": m, "mode": "markdown"}
            return urllib.request.urlopen("https://api.github.com/markdown",json=data).text
        except:
            return None

    def convert_raw(m):
        # simple and dirty regex-based markdown t- html
        f = re.DOTALL|re.MULTILINE
        m = re.sub(r"^##### (.*?)\n",r"<h5>\1</h5>\n",m,flags=f) # ##### titles
        m = re.sub(r"^#### (.*?)\n", r"<h4>\1</h4>\n",m,flags=f) # #### titles
        m = re.sub(r"^### (.*?)\n",  r"<h3>\1</h3>\n",m,flags=f) # ### titles
        m = re.sub(r"^## (.*?)\n",   r"<h2>\1</h2>\n",m,flags=f) # ## titles
        m = re.sub(r"^# (.*?)\n",    r"<h1>\1</h1>\n",m,flags=f) # # titles
        m = re.sub(r"!\[(.*?)\]\((.*?)\)", r'<img alt="\1" src="\2">',m,flags=f) # images
        m = re.sub(r"\[(.*?)\]\((.*?)\)",  r'<a href="\2">\1</a>',m,flags=f) # links
        m = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>",s) # bold
        m = re.sub(r"\*(.*?)\*", r"<i>\1</i>",s) # italic
        m = re.sub(r"\n\n", r"<br/>",s,flags=f) # double new lines
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
    elif force == "raw":
        html = convert_raw(content)
    else:
        # auto mode
        html = convert_markdown(content)
        if not html:
            html = convert_pandoc(content)
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



def addPreferencesPage():

    """adds the Help preferences page to the UI"""

    import FreeCADGui
    page = os.path.join(os.path.dirname(__file__),"dlgPreferencesHelp.ui")
    FreeCADGui.addPreferencePage(page,QT_TRANSLATE_NOOP("QObject", "General"))



def openBrowserHTML(html,baseurl,title,icon,dialog=False):

    """creates a browser view in the FreeCAD MDI area"""

    import FreeCADGui
    from PySide2 import QtCore,QtGui,QtWidgets,QtWebEngineWidgets

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

    # save dock widget location
    def onDockLocationChanged(area):
        PREFS.SetInt("dockWidgetArea",int(area))
        mw = FreeCADGui.getMainWindow()
        dock = mw.findChild(QtWidgets.QDockWidget,"HelpWidget")
        if dock:
            PREFS.SetBool("dockWidgetFloat",dock.isFloating())

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
        dock = mw.findChild(QtWidgets.QDockWidget,"HelpWidget")
        if not dock:
            dock = QtWidgets.QDockWidget()
            dock.setObjectName("HelpWidget")
            mw.addDockWidget(getDockArea(area),dock)
            dock.setFloating(floating)
            dock.dockLocationChanged.connect(onDockLocationChanged)
        dock.setWidget(view)
        dock.setWindowTitle(title)
        dock.setWindowIcon(QtGui.QIcon(icon))
    else:
        mdi = mw.findChild(QtWidgets.QMdiArea)
        sw = mdi.addSubWindow(view)
        sw.setWindowTitle(title)
        sw.setWindowIcon(QtGui.QIcon(icon))
        sw.show()
        mdi.setActiveSubWindow(sw)

