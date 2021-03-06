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

import gobject
from threading import Thread
from time import sleep

INTERVAL = 60

class AutoSaveThread(Thread):
    def __init__(self, application):
        Thread.__init__(self)
        self.app = application

    def run(self):
        count = 0
        while not self.app.quitrequest:
            sleep(0.5)
            count+=1
            if count/2 == INTERVAL:
                count = 0
                if self.app.activeProfile is not None:
                    gobject.idle_add(self.app.activeProfile.updateProfile,True)
