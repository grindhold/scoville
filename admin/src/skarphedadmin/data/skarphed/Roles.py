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


from skarphedadmin.data.Generic import GenericSkarphedObject
from skarphedadmin.data.skarphed.Skarphed import rpc

from Role import Role

class Roles(GenericSkarphedObject):
    def __init__(self,parent):
        GenericSkarphedObject.__init__(self)
        self.par = parent
        self.updated()
        self.refresh()
    
    def refreshCallback(self,data):
        roleIds = [r.getId() for r in self.children]
        for role in data:
            if role['id'] not in roleIds:
                self.addChild(Role(self,role))
            else:
                self.getRoleById(role['id']).refresh(role)
                
    @rpc(refreshCallback)
    def getRoles(self):
        pass
    
    def refresh(self):
        self.getRoles()
    
    def getRoleById(self,id):
        for role in self.children:
            if role.getId() == id:
                return role
        return None
    
    def getName(self):
        return "Roles"
    
    def createRoleCallback(self,json):
        self.refresh()
    
    @rpc(createRoleCallback)
    def createRole(self,roledata):
        pass
    
    def createNewRole(self,name):
        self.createRole({'name':name})
    
    def getPar(self):
        return self.par
    
    def getSkarphed(self):
        return self.getPar()
    
    def getServer(self):
        return self.getPar().getServer()
