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

import FreeCAD
from PySide import QtGui

reply = QtGui.QMessageBox.question(None, "Keep addon settings?", 
        "Do you wish to keep the preferences settings for this addon? If yes, when reinstalled, the current settings will still be present.",
        QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, QtGui.QMessageBox.Yes)
if reply == QtGui.QMessageBox.Yes:
    pass
if reply == QtGui.QMessageBox.No:
    p = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod")
    p.RemGroup("Help")

