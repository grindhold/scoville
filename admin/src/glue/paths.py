#!/usr/bin/python
#-*- coding: utf-8 -*-

###########################################################
# © 2011 Daniel 'grindhold' Brendle and Team
#
# This file is part of Skarphed.
#
# Skarphed is free software: you can redistribute it and/or 
# modify it under the terms of the GNU Affero General Public License 
# as published by the Free Software Foundation, either 
# version 3 of the License, or (at your option) any later 
# version.
#
# Skarphed is distributed in the hope that it will be 
# useful, but WITHOUT ANY WARRANTY; without even the implied 
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR 
# PURPOSE. See the GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public 
# License along with Skarphed. 
# If not, see http://www.gnu.org/licenses/.
###########################################################

from sys import platform, path
from os.path import join

P = path[0]

# Handle different filepaths for most common OS (others may follow)

if platform == 'linux2':
    DATA = join(P,"..","data")
    ICON = join(DATA,"icon")
    INSTALLER = join(P,"..","installer")
elif platform == 'win32':
    DATA = join(P,"..","data")
    ICON = join(DATA,"icon")
    INSTALLER = join(P,"..","installer")
elif platform == 'darwin':
    DATA = join(P,"..","data")
    ICON = join(DATA,"icon")
    INSTALLER = join(P,"..","installer")