# -*- coding: utf-8 -*-

# ***************************************************************************
# *   Copyright (c) 2023 Yorik van Havre <yorik@uncreated.net>              *
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
Menu utilities module - NOT USED YET
"""


# menu building - not used yet
MENU_LINKS = [
    [translate("Help", "Home"), "https://freecad.org"],
    [translate("Help", "Forum"), "https://forum.freecad.org"],
    [translate("Help", "Wiki"), "https://wiki.freecad.org"],
    [translate("Help", "Issues"), "https://github.com/FreeCAD/FreeCAD/issues"],
    [translate("Help", "Code repository"), "https://github.com/FreeCAD/FreeCAD"],
]
MENU_COMMANDS = [
    [
        "applications-python.svg",
        translate("Help", "Auto Python modules"),
        None,
        "Std_PythonHelp",
    ],
    ["freecad.svg", translate("Help", "About FreeCAD"), None, "Std_About"],
    ["WhatsThis.svg", translate("Help", "What's this?"), "Shift+F1", "Std_WhatsThis"],
]


def generate_index():
    """
    Offline index generator - generates an index file from the documentation
    Structure:
    - Users
    - Workbenches
    - Powerusers
    - Developers
    - Manual
    """

    import os

    this_folder = os.path.dirname(__file__)
    doc_folder = os.join(os.path.dirname(this_folder), "FreeCAD-documentation", "wiki")
    if not os.path.isdir(doc_folder):
        return

    wikifiles = [e for e in os.listdir(dic_folder) if e.endswith(".md")]

    json = ""


def add_menu():
    """adds the Help menu of FreeCAD"""

    import FreeCADGui

    if hasattr(FreeCADGui, "HelpMenu"):
        mb = FreeCADGui.getMainWindow().menuBar()
        mb.addMenu(FreeCADGui.HelpMenu)


def build_menu():
    """creates and populates a help menu. Menu creation takes several
    seconds to fullfill due to the big number of entries."""

    import FreeCADGui
    from PySide2 import QtGui

    menu = QtGui.QMenu(translate("Help", "Help"))
    menu.setObjectName("Help")

    # On the web
    sub = QtGui.QMenu(translate("Help", "On the web"), menu)
    for it in MENU_LINKS:
        act = QtGui.QAction(it[0], sub)
        act.setToolTip(it[1])
        act.triggered.connect(lambda f=show, arg=it[1]: f(arg))
        sub.addAction(act)
    menu.addMenu(sub)

    # Documentation
    cache = os.path.join(FreeCAD.getUserAppDataDir(), "Help", "menu.md")
    if not os.path.exists(cache):
        get_menu_structure()
    if os.path.exists(cache):
        doc = QtGui.QMenu(translate("Help", "Documentation"), menu)
        act = QtGui.QAction("Index", doc)
        act.setShortcut("F1")
        act.setToolTip(
            translate("Help", "Shows the index page of the FreeCAD documentation")
        )
        act.triggered.connect(lambda: show("Main Page"))
        doc.addAction(act)
        with open(cache) as f:
            for line in f:
                name = line[line.index("[") + 1 : line.index("]")]
                link = line[line.index("(") + 1 : line.index(")")]
                if line.startswith("-"):
                    sub = QtGui.QMenu(name, menu)
                    doc.addMenu(sub)
                else:
                    act = QtGui.QAction(name, sub)
                    act.setToolTip(link)
                    act.triggered.connect(lambda f=show, arg=link: f(arg))
                    sub.addAction(act)
        menu.addMenu(doc)

    # Special FreeCAD Help commands
    for it in MENU_COMMANDS:
        if it[0]:
            act = QtGui.QAction(QtGui.QIcon(":/icons/" + it[0]), it[1], menu)
        else:
            act = QtGui.QAction(it[1], menu)
        if it[2]:
            act.setShortcut(it[2])
        act.triggered.connect(lambda f=FreeCADGui.runCommand, arg=it[3]: f(arg))
        menu.addAction(act)

    # store menu to FreeCAD for faster access and possible modification by addons
    FreeCADGui.HelpMenu = menu


def get_menu_structure():
    """fetches menu structure from documentation"""

    location = get_location("Online Help Toc")
    if not location:
        return
    md = get_contents(location)
    d = os.path.join(FreeCAD.getUserAppDataDir(), "Help")
    if not os.path.isdir(d):
        os.makedirs(d)
    cache = os.path.join(d, "menu.md")
    with open(cache, "w") as f:
        f.write(md)
