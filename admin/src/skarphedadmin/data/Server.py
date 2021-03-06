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


import socket
import re
import logging

from Generic import GenericSkarphedObject
from Generic import ObjectStore
from Instance import InstanceType

class InstallationTarget(object):
    def __init__(self):
        self._name = ""
        self._destroyer = None
        self._installer = None
        self._extraParams = {}

    def getName(self):
        return self._name

    def setName(self, name):
        self._name = str(name)

    def getInstaller(self):
        return self._installer

    def setInstaller(self, installer):
        self._installer = installer

    def getDestroyer(self):
        return self._destroyer

    def setDestroyer(self, destroyer):
        self._destroyer = destroyer

    def getExtraParams(self):
        return self._extraParams

    def setExtraParams(self, extraParams):
        self._extraParams = dict(extraParams)

class NoneTarget(InstallationTarget):
    class EmptyInstaller(object):
        def execute_installation(self):
            pass
    class EmptyDestroyer(object):
        def execute_destruction(self):
            pass

    def __init__(self):
        InstallationTarget.__init__(self)
        self._name = "None/None"
        self._destroyer = NoneTarget.EmptyDestroyer()
        self._installer = NoneTarget.EmptyInstaller()

class Server(GenericSkarphedObject):
    URL_PROT_STRIP = re.compile(r".+://")
    URL_TAIL_STRIP = re.compile(r"(:(\d{1}|\d{2}|\d{3}|\d{4}|\d{5}))?/.+")
    URL_2NDL_STRIP = re.compile(r"[^.]+\.[^.]+$")
    STATE_OFFLINE = 0
    STATE_ONLINE = 1
    
    SSH_LOCKED = 0
    SSH_UNLOCKED = 1
    
    LOADED_NONE = 0
    LOADED_PROFILE = 1
    LOADED_SERVERDATA = 2
     
    instanceTypesLoaded=False
     
    INSTALLATION_TARGETS = [NoneTarget()]

    @classmethod
    def addInstallationTarget(cls, target):
        cls.INSTALLATION_TARGETS.append(target)

    @classmethod
    def hasInstallationTarget(cls, targetname):
        return cls.getInstallationTargetByName(targetname) != None

    @classmethod
    def getInstallationTargetByName(cls, targetname):
        for target in cls.INSTALLATION_TARGETS:
            if targetname == target.getName():
                return target
        return None        

    def __init__(self):
        if not Server.instanceTypesLoaded:
            import skarphed
            import skarphed_repo
            import database
            Server.instanceTypesLoaded = True
            
        GenericSkarphedObject.__init__(self)
        self.state = self.STATE_OFFLINE
        self.ssh_loggedin = self.SSH_LOCKED
        self.ssh_ready = False
        self.load = self.LOADED_NONE
        self.data = {}
        
        self.ip = ""
        self.name = ""
        self.ssh_username = ""
        self.ssh_password = ""

        self.target = None
        self.target_usable = False

    def setTarget(self, targetname):
        target = Server.getInstallationTargetByName(targetname)
        if target is None:
            self.target = targetname
            self.target_usable = False
        else:
            self.target = target
            self.target_usable = True

    def getTarget(self):
        return self.target

    def isTargetUsable(self):
        return self.target_usable

    def setName(self,name):
        self.name = name

    def setIp(self,ip):
        self.ip= ip
        self.updated()
    
    def getIp(self):
        return self.ip
        
    def setSSHName(self, name):
        self.ssh_username = name
        
    def setSSHPass(self, password):
        self.ssh_password = password
    
    def getSSHName(self):
        return self.ssh_username

    def getSSHPass(self):
        return self.ssh_password
    
    def setSSHState(self,state):
        self.ssh_loggedin = state

    def connectSSH(self):
        self.getApplication().getSSHConnection(self)
    
    """call From threaded"""
    def getSSH(self):
        try:
            con_stdin, con_stdout, con_stderr = self.ssh_connection.exec_command("uname")
        except socket.error, e:
            self.ssh_ready = False
            self.getServer().connectSSH()
        except AttributeError, e:
            self.ssh_ready = False
            self.getServer().connectSSH()
        while not self.ssh_ready: pass
        return self.ssh_connection

    def establishConnections(self):
        self.connectSSH()
    
    def getName(self):
        if self.ip is not None:
            if self.name is not None:
                return self.ip+" [ "+self.name+" ]"
            return self.ip
        else:
            return "Unknown Server"

    def getRawName(self):
        return self.name;
            
    def loadProfileInfo(self,profileInfo):
        pass
    
    def getSSHState(self):
        return self.ssh_loggedin
    
    def isOnline(self):
        return self.state==self.STATE_ONLINE
    
    def getServer(self):
        return self

    def installNewInstance(self,data,instanceType="skarphed"):
        if instanceType == "skarphed":
            if self.target_usable:
                installer =  self.target.getInstaller()(data,self)
                installer.install()
                return installer
            else:
                print "No installer available for %s"%self.target
        elif instanceType == "skarphed_repo":
            print "Not Implemented yet: %s"%(instanceType,)
        elif instanceType == "skarphed_database":
            print "Not Implemented yet: %s"%(instanceType,)
    
    def setDatabase(self, user="", password=""):
        for child in self.children:
            if child.instanceTypeName == "database":
                child.setUsername(user)
                child.setPassword(password)
                return

        instanceType = InstanceType("database","Database")
        self.createInstance(instanceType, "", user, password)
        self.getApplication().activeProfile.updateProfile()

    def createInstance(self,instanceType, url, username, password):
        instance = None
        if url != "":
            hostname = re.sub(self.URL_TAIL_STRIP,"",re.sub(self.URL_PROT_STRIP,"",url)) # String Protocol identifier , eventually port, path and querystring
            if re.match(r'\b(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b',hostname):
                # Hostname is a valid IP 
                host = hostname 
            else:
                # Hostname is a domain that must be resolved
                hostname = re.search(self.URL_2NDL_STRIP,hostname) # strip subdomains
                if hostname:
                    hostname = hostname.group(0)
                    print hostname
                else:
                    return False
                try:
                    host = socket.gethostbyname(hostname)
                except socket.gaierror:
                    logging.warn("Non-Resolvable URL for instance: %s . This Instance is in Limbo"\
                                    %(url))
                    return False
            if host != self.getIp(): # check wheter the resulting IP belongs to this server
                return False
        exec "from "+instanceType.instanceTypeName+"."+instanceType.instanceTypeName.capitalize()+\
             " import "+instanceType.instanceTypeName.capitalize()
        exec "instance = "+instanceType.instanceTypeName.capitalize()+"(self, url, username, password)"
        self.addChild(instance)
        self.updated()
        instance.establishConnections()
        return instance
        
    def removeInstance(self, instance):
        if instance in self.children:
            self.children.remove(instance)
            instance.destroy()
            self.getApplication().activeProfile.updateProfile()
    
    def getInstances(self):
        return self.children

 
class DNSError(Exception):
    pass

def getServers():
    return ObjectStore().getServers()

def createServer():
    return Server()

def createServerFromInstanceUrl(instanceurl):
    instanceurl = re.sub(r'^[A-Za-z]+:\//','',instanceurl)
    instanceurl = re.sub(r'/.+$|/$','',instanceurl)
    instanceurl = re.sub(r':\d{1,5}$','',instanceurl)
    
    if not re.match(r'\b(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b',instanceurl):
        try:
            ip = socket.gethostbyaddr(instanceurl)
        except socket.gaierror:
            raise DNSError("Couldn't resolve")
    else:
        ip = instanceurl
    for server in getServers():
        if ip == server.getIp():
            return server
    server = Server()
    server.setIp(ip)
    server.setName("Neuer Server")
    return server
