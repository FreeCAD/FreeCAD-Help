#### Help module for FreeCAD

This is the FreeCAD Help system. Its primary use is to display a documentation page. 
It can do so in several ways:

* In a new tab in the FreeCAD UI
* In a dockable dialog
* In the system's default browser

It can also fetch documentation from different sources and in different formats:

* From a locally installed collection of markdown files
* From an online repository of markdown files
* From an online website, such as a wiki

It also included a FreeCAD preferences page under *General* tab to allow users 
to set their preferred source and format from the above options.

This also turns the FreeCAD help system usable by addons, that can have the 
help system open custom URLs.

Later on, it could also be extended to do more powerful things such as populating a 
Help menu or inserting content (images, etc) into tooltips.

### Python usage

The main usage is using the "show" function. It can retrieve an URL, a local file 
(markdown or html), or find a page automatically from the settings set under 
Preferences->General->Help.

It doesn't matter what you give, the system will recognize if the contents are HTML 
or Markdown and render it appropriately.

Basic usage:

```
import Help
Help.show("Draft Line")
Help.show("Draft_Line") # works with spaces or underscores
Help.show("https://wiki.freecadweb.org/Draft_Line")
Help.show("https://gitlab.com/freecad/FreeCAD-documentation/-/raw/main/wiki/Draft_Line.md")
Help.show("/home/User/.FreeCAD/Documentation/Draft_Line.md")
Help.show("http://myserver.com/myfolder/Draft_Line.html")
```

Preferences keys (in "User parameter:BaseApp/Preferences/Mod/Help"):

```
optionBrowser/optionTab/optionDialog (bool): Where to open the help dialog
optionOnline/optionOffline (bool): where to fetch the documentation from
URL (string): online location
Location (string): offline location
Suffix (string): a suffix to add to the URL, ex: /fr
StyleSheet (string): optional CSS stylesheet to style the output
```
