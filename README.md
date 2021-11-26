#### Help module for FreeCAD

This is a work-in-progress module aimed at replacing the entire FreeCAD Help system. Its primary use is to display a documentation page. It can do so in several ways:

* In a new tab in the FreeCAD UI
* In a standalone, dockable dialog
* In the system's default browser

It can also fetch documentation from different sources and in different formats:

* From a locally installed collectipn of markdown files
* From an online repository of markdown files
* From an online website, such as a wiki

It also included a FreeCAD preferences page to allow users to set their preferred source and format from the above options.

This also turns the FreeCAD help system usable by addons, that can have the help system open custom URLs.

Later on, it could also be extended to do more powerful things such as populating a Help menu or inserting content (images, etc) into tooltips.
