#!/usr/bin/python
#-*- coding: utf-8 -*-

###########################################################
# Copyright 2011 Daniel 'grindhold' Brendle and Team
#
# This file is part of Scoville.
#
# Scoville is free software: you can redistribute it and/or 
# modify it under the terms of the GNU General Public License 
# as published by the Free Software Foundation, either 
# version 3 of the License, or (at your option) any later 
# version.
#
# Scoville is distributed in the hope that it will be 
# useful, but WITHOUT ANY WARRANTY; without even the implied 
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR 
# PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public 
# License along with Scoville. 
# If not, see http://www.gnu.org/licenses/.
###########################################################

###########################################################
# Rewrite from PHP status
# 
# class OperationException                    
# class OperationManager                    
# - public dropOperation()  done
# - public retryOperation()  done
# - public cancelOperation()  done
# - public restoreOperation() done
# - public processChildren()  done
# - public processNext() done
# - public getCurrentOperationsForGUI() done
# class Operation done
# - constructor() done
# - public getValue() done
# - public getValues() done
# - public setValue() done
# - public setParent() done
# - public getParent() done
# - public setDBID() done
# - public setId() done
# - public getId() done
# - public abstract doWorkload() done
# class ModuleOperation() done
# - public setValuesFromMeta() done
# - public getMeta() done
# - public getCurrentlyProcessedModules() done
# - public abstract optimizeQueue() done
# class ModuleUninstallOperation done
# - public doWorkload done
# - public optimizeQueue done
# class ModuleInstallOperation done
# - public doWorkload done
# - public optimizeQueue done
# class FailOperation done
# - public doWorkload done
# class TestOperation done
# - public doWorkload done
###########################################################

import os
from daemon import Daemon
from time import sleep
from StringIO import StringIO
from traceback import print_exc

class OperationException(Exception):
    """
    Exceptions for Operation-Module
    """
    ERRORS = {
        0:"""Could not remove Lock!""",
    }

    @classmethod
    def get_msg(cls,nr, info=""):
        return "OP_"+str(nr)+": "+cls.ERRORS[nr]+" "+info

class Operation(object):
    """
    Contais everything necessary to Handle Operations
    """

    STATUS_PENDING = 0
    STATUS_ACTIVE = 1
    STATUS_FAILED = 2

    VALID_STORAGE_TYPES = ('int','bool','str','unicode')

    def __init__(self,core, parent_id = None):
        """

        """
        self._core = core
        
        self._id = None
        self._parent = parent_id
        self._values = {}

    @classmethod
    def set_core(cls,core):
        cls._core = core

    @classmethod
    def drop_operation(cls,operation_id):
        """
        Drops an Operation, identified by it's Operation Id and
        it's children recursively
        Drop deletes the Operations from Database
        """
        db = cls._core.get_db()

        stmnt = "SELECT OPE_ID FROM OPERATIONS WHERE OPE_OPE_PARENT = ? AND OPE_STATUS IN (0, 2) ;"
        cur = db.query(cls._core,stmnt,(operation_id,))
        for row in cur.fetchallmap():
            cls.drop_operation(row["OPE_ID"])

        stmnt = "DELETE FROM OPERATIONS WHERE OPE_ID = ? AND OPE_STATUS IN (0, 2) ;"
        db.query(cls._core,stmnt,(operation_id,),commit=True)

    @classmethod
    def retry_operation(cls,operation_id):
        """
        Resets the state of an operation and it's children recursively to 0 (PENDING)
        The operation is identified by a given operationId
        """
        db = cls._core.get_db()

        stmnt = "SELECT OPE_ID FROM OPERATIONS WHERE OPE_OPE_PARENT = ? AND OPE_STATUS = 2 ;"
        cur = db.query(cls._core,stmnt,(operation_id,))
        for row in cur.fetchallmap():
            cls.retry_operation(row["OPE_ID"])

        stmnt = "UPDATE OPERATIONS SET OPE_STATUS = 0 WHERE OPE_ID = ? AND OPE_STATUS = 2 ;"
        db.query(cls._core,stmnt,(operation_id,),commit=True)

    @classmethod
    def cancel_operation(cls,operation_id):
        """
        Cancels an Operation, identified by it's Operation Id and
        it's children recursively
        Cancel Deletes the Operation from Database
        """
        db = cls._core.get_db()

        stmnt = "SELECT OPE_ID FROM OPERATIONS WHERE OPE_OPE_PARENT = ? AND OPE_STATUS = 0 ;"
        cur = db.query(cls._core,stmnt,(operation_id,))
        for row in cur.fetchallmap():
            cls.cancel_operation(row["OPE_ID"])

        stmnt = "DELETE FROM OPERATIONS WHERE OPE_ID = ? AND OPE_STATUS = 0 ;"
        db.query(cls._core,stmnt,(operation_id,),commit=True)

    @classmethod
    def restore_operation(cls, operation_record):
        """
        Restore an Operationobject stored in the database by a Dataset consisting of
        the operation's ID and the operation's TYPE:
        For example:   {"OPE_ID": 100, "OPE_TYPE": "TestOperation"}
        Restores the Operationobject's _values-attribute by the data saved
        in the DB-Table OPERATIONDATA
        """
        classname = operation_record["OPE_TYPE"]
        module = "" #TODO Implement modulename from database if Operation belongs to Module
        is_operation_of_module = False
        exec """
try:
    type(%(class)s)
except NameError,e:
    is_operation_of_module = True"""%{'class':classname}

        if is_operation_of_module:
            exec """
from %(module)s import %(class)s
operation = %(class)s(cls._core)"""%{'class':classname,'module':module}
        else:
            exec """
operation = %(class)s(cls._core)"""%{'class':classname}

        operation.set_id(operation_record['OPE_ID'])
        db = cls._core.get_db()
        stmnt = "SELECT OPD_KEY, OPD_VALUE, OPD_TYPE FROM OPERATIONDATA WHERE OPD_OPE_ID = ? ;"
        cur = db.query(cls._core,stmnt,(operation_record["OPE_ID"],))
        for row in cur.fetchallmap():
            val = row["OPD_VALUE"]
            exec """val = %s(val)"""%row["OPD_TYPE"]
            operation.set_value(row["OPD_KEY"], val)
        return operation

    @classmethod
    def process_children(cls, operation):
        """
        Recursively executes the workloads of Operation's Childoperations
        It hereby catches exceptions in the workloads, sets the OPE_STATUS
        to 2 (FAILED) if a catch occurs, then passes the exception on to the 
        higher layer.
        If an Operation succeeds, it's entry in DB gets deleted
        """
        db = cls._core.get_db()

        stmnt = "SELECT OPE_ID, OPE_TYPE FROM OPERATIONS WHERE OPE_OPE_PARENT = ? ORDER BY OPE_INVOKED ;"
        stmnt_lock = "UPDATE OPERATIONS SET OPE_STATUS = 1 WHERE OPE_ID = ? ;"
        cur = db.query(cls._core,stmnt,(operation.get_id(),))
        for row in cur.fetchallmap():
            child_operation = cls.restore_operation(row)
            db.query(cls._core,stmnt_lock,(child_operation.get_id(),),commit=True)
            try:
                cls.process_children(child_operation)
                child_operation.do_workload()
            except Exception,e:
                stmnt_err = "UPDATE OPERATIONS SET OPE_STATUS = 2 WHERE OPE_ID = ? ;"
                db.query(cls._core,stmnt_err,(int(row["OPE_ID"]),),commit=True)
                #TODO GENERATE ERROR IN LOG
                raise e
            stmnt_delete = "DELETE FROM OPERATIONS WHERE OPE_ID = ?;"
            db.query(cls._core,stmnt_delete,(child_operation.get_id(),),commit=True)

    @classmethod
    def process_next(cls):
        """
        Sets the status of the next toplevel operation to 1 (ACTIVE)
        Fetches the next toplevel-operation from the database, applies a FILESYSTEMLOCK!
        Which is /tmp/scv_operating.lck !!! 
        """
        db = cls._core.get_db()
        configuration = cls._core.get_configuration()
        if os.path.exists(configuration.get_entry("core.webpath")+"/scv_operating.lck"):
            return False
        lockfile = open(configuration.get_entry("core.webpath")+"/scv_operating.lck","w")
        lockfile.close()
        stmnt_lock = "UPDATE OPERATIONS SET OPE_STATUS = 1 \
                            WHERE OPE_ID IN ( \
                              SELECT OPE_ID FROM OPERATIONS \
                              WHERE OPE_OPE_PARENT IS NULL AND OPE_STATUS = 0 \
                              AND OPE_INVOKED = ( \
                                SELECT MIN(OPE_INVOKED) FROM OPERATIONS  \
                                WHERE OPE_OPE_PARENT IS NULL AND OPE_STATUS = 0) \
                            ) ;"
        stmnt = "SELECT OPE_ID, OPE_TYPE FROM OPERATIONS WHERE OPE_OPE_PARENT IS NULL AND OPE_STATUS = 1 ;"
        db.query(cls._core,stmnt_lock,commit=True)
        cur = db.query(cls._core,stmnt)
        res = cur.fetchallmap()
        if len(res) > 0:
            operation = cls.restore_operation(res[0])
            try:
                cls.process_children(operation)
                operation.do_workload()
            except Exception, e:
                stmnt_err = "UPDATE OPERATIONS SET OPE_STATUS = 2 WHERE OPE_ID = ? ;"
                db.query(cls._core,stmnt_err,(operation.get_id(),),commit=True)
                error = StringIO()
                print_exc(None,error)
                cls._core.log(error.getvalue())
            ret = True
        else:
            ret = False
        stmnt_delete = "DELETE FROM OPERATIONS WHERE OPE_STATUS = 1 ;"
        db.query(cls._core,stmnt_delete,commit=True)
        db.commit()
        try:
            os.unlink(configuration.get_entry("core.webpath")+"/scv_operating.lck")
        except OSError,e :
            raise OperationException(OperationException.get_msg(0))
        return ret

    @classmethod
    def get_current_operations_for_gui(cls, operation_types=None):
        """
        Returns all Operations in an associative array.
        The array's indices are the operationIDs
        The Objects contain all information about the operations,
        including the Data
        """
        db = cls._core.get_db()
        #TODO CHECK HOW LISTS ARE HANDLED IN FDB
        if operation_types is not None and type(operation_types) == list:
            stmnt = "SELECT OPE_ID, OPE_OPE_PARENT, OPE_INVOKED, OPE_TYPE, OPE_STATUS FROM OPERATIONS WHERE OPE_TYPE IN (?) ORDER BY OPE_INVOKED ;"
            cur = db.query(cls._core,stmnt,(operation_types))
        else:
            stmnt = "SELECT OPE_ID, OPE_OPE_PARENT, OPE_INVOKED, OPE_TYPE, OPE_STATUS FROM OPERATIONS ORDER BY OPE_INVOKED ;"
            cur = db.query(cls._core,stmnt)
        ret = {}
        for row in cur.fetchallmap():
            operation = cls.restore_operation(row)
            custom_values = operation.get_values()

            ret[row["OPE_ID"]] = {"id":row["OPE_ID"],
                                  "parent":row["OPE_OPE_PARENT"],
                                  "invoked":str(row["OPE_INVOKED"]),
                                  "type":row["OPE_TYPE"],
                                  "status":row["OPE_STATUS"],
                                  "data":custom_values}
        return ret

    def get_values(self):
        """
        trivial
        """
        return self._values

    def get_value(self,key):
        """
        trivial
        """
        return self._values(key)

    def set_value(self,key,value):
        """
        trivial
        """
        self._values[key] = value

    def set_parent(self,parent_id):
        """
        trivial
        """
        self._parent = parent_id

    def get_parent(self):
        """
        trivial
        """
        return self._parent

    def set_db_id(self):
        """
        Get a new Operation Id from the Database and assign it to this
        Operation if this Operation's id is null. Afterwards return the 
        new Id
        """
        if self._id is None:
            db = self._core.get_db()
            self._id = db.get_seq_next('OPE_GEN')
        return self._id

    def set_id(self, nr):
        """
        trivial
        """
        self._id = nr

    def get_id(self):
        """
        trivial
        """
        return self._id

    def store(self):
        """
        Stores this Operation to database.
        Also saves every user defined value in $_values as 
        long as it is a valid type         
        """
        db = self._core.get_db()

        if self._id is None:
            db = self._core.get_db()
            self._id = db.get_seq_next('OPE_GEN')

        stmnt = "UPDATE OR INSERT INTO OPERATIONS (OPE_ID, OPE_OPE_PARENT, OPE_INVOKED, OPE_TYPE) \
                      VALUES (?,?,CURRENT_TIMESTAMP,?) MATCHING (OPE_ID);"
        db.query(self._core,stmnt,(self._id,self._parent,self.__class__.__name__),commit=True)

        stmnt = "UPDATE OR INSERT INTO OPERATIONDATA (OPD_OPE_ID, OPD_KEY, OPD_VALUE, OPD_TYPE) \
                      VALUES ( ?, ?, ?, ?) MATCHING(OPD_OPE_ID,OPD_KEY);"
        for key, value in self._values.items():
            typ = str(type(value)).replace("<type '","",1).replace("'>","",1)
            if typ not in Operation.VALID_STORAGE_TYPES:
                continue
            db.query(self._core,stmnt,(self._id,key,value,typ),commit=True)

    def do_workload(self):
        """
        This method must be overridden by inheriting classes.
        The code inside this method will be executed when the
        Operation is processed by OperationManager::processNext or 
        OperationManager::processChild 
        """
        pass

class OperationManager(object):
    """
    Permission Manger wraps Operation's classmethods
    """
    def __init__(self,core):
        """
        Initialize OperationManager
        """
        self._core = core
        Operation.set_core(core)

        self.drop_operation = Operation.drop_operation
        self.retry_operation = Operation.retry_operation
        self.cancel_operation = Operation.cancel_operation
        self.restore_operation = Operation.restore_operation
        self.process_children = Operation.process_children
        self.process_next = Operation.process_next
        self.get_current_operations_for_gui = Operation.get_current_operations_for_gui

    def get_operation_daemon(self):
        return OperationDaemon

    def get_parent(self):
        """
        returns PermissionManager's coreobject
        """
        return self._core

    def get_core(self):
        """
        returns PermissionManager's coreobject
        """
        return self._core

#MODULEINVOLVED
class ModuleOperation(Operation):
    """
    Abstracts Operations that have to do with modules
    """
    def __init__(self,core):
        """
        trivial
        """
        Operation.__init__(self,core)

    def set_values(self,module):
        """
        Sets this operations values from module metadata
        """
        if type(module) == dict:
            self.set_value("name",module["name"])
            self.set_value("hrname",module["hrname"])
            self.set_value("version_major",module["version_major"])
            self.set_value("version_minor",module["version_minor"])
            self.set_value("revision",module["revision"])
            self.set_value("signature",module["signature"])
        elif module.__class__.__name__ == "Module":
            pass #TODO IMPLEMENT / DISCUSS AFTER IMPLEMENTING MODULE-SUBSYSTEM

    def get_meta(self):
        """
        trivial
        """
        return self._values
    
    @classmethod
    def get_currently_processed_modules(cls):
        """
        Returns an Array of ModuleOperation-Objects that are
        currently listedin the queue 
        """
        db = cls._core.get_db()
        stmnt = "SELECT OPE_ID, OPE_OPE_PARENT, OPE_TYPE FROM OPERATIONS \
                   WHERE OPE_TYPE = 'ModuleInstallOperation' \
                   or OPE_TYPE = 'ModuleUninstallOperation' ;"
        cur = db.query(cls._core,stmnt);
        ret = []
        for row in cur.fetchallmap():
            ret.append(Operation.restore_operation(row).get_meta())
        return ret

    def optimize_queue(self):
        """
        abtract
        """
        pass

#MODULEINVOLVED
class ModuleInstallOperation(ModuleOperation):
    """
    Manages the process to install a module to this server
    """
    def __init__(self,core):
        """
        trivial
        """
        ModuleOperation.__init__(self,core)

    def do_workload(self):
        """
        tell the module manager to install a specific module.
        """
        module_manager = self._core.get_module_manager()
        module_manager.install_module(self.get_meta())

    def optimize_queue(self):
        """
        optimizes the queue. 
        """
        pass    #TODO Implement

#MODULEINVOLVED
class ModuleUninstallOperation(ModuleOperation):
    """
    Manages the process to uninstall a module to this server
    """
    def __init__(self,core):
        """
        trivial
        """
        ModuleOperation.__init__(self,core)

    def do_workload(self):
        """
        tell the module manager to install a specific module.
        """
        module_manager = self._core.get_module_manager()
        module = module_manager.get_module_by_name(self._values["name"])
        module_manager.uninstall_module(module)

    def optimize_queue(self):
        """
        optimizes the queue. 
        """
        pass    #TODO Implement

#MODULEINVOLVED
class ModuleUpdateOperation(ModuleOperation):
    """
    Manages the process to uninstall a module to this server
    """
    def __init__(self,core):
        """
        trivial
        """
        ModuleOperation.__init__(self,core)

    def do_workload(self):
        """
        tell the module manager to install a specific module.
        """
        module_manager = self._core.get_module_manager()
        module = module_manager.get_module_by_name(self._values["name"])
        module_manager.update_module(module)
        
    def optimize_queue(self):
        """
        optimizes the queue. 
        """
        pass    #TODO Implement

class FailOperation(Operation):
    """
    For unittest purposes: An Operation that always fails
    """
    def __init__(self,core):
        """
        trivial
        """
        Operation.__init__(self,core)

    def do_workload(self):
        """
        simply fail
        """
        raise Exception("Failoperation failed")

class TestOperation(Operation):
    """
    For unittest purposes: An Operation that always succeds
    """
    def __init__(self,core):
        """
        trivial
        """
        Operation.__init__(self,core)

    def do_workload(self):
        """
        simply succeed
        """
        pass

class OperationDaemon(Daemon):
    """
    This is the deamon that runs to actually execute the scheduled operations
    """
    def __init__(self, core, pidfile):
        """
        Initialize the deamon
        """
        Daemon.__init__(self,pidfile)
        self._core = core

    def stop(self):
        configuration = self._core.get_configuration()
        if os.path.exists(configuration.get_entry("core.webpath")+"/scv_operating.lck"):
            os.remove(configuration.get_entry("core.webpath")+"/scv_operating.lck") 
        Daemon.stop(self)

    def run(self):
        """
        Do work if there is work to do, otherwise check every two seconds for new work.
        """
        operation_manager = self._core.get_operation_manager()
        while True:
            while operation_manager.process_next():
                pass
            sleep(2)

