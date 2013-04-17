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

import os
from StringIO import StringIO

from module import AbstractModule

class ModuleException(Exception): 
    ERRORS = {
        0:"""This instance does not have a WidgetId. Therefore, Widget-bound methods cannot be used"""
    }

    @classmethod
    def get_msg(cls,nr, info=""):
        return "DB_"+str(nr)+": "+cls.ERRORS[nr]+" "+info

class Module(AbstractModule):
    HORIZONTALLY = 0
    VERTICALLY = 1
    def __init__(self, core):
        AbstractModule.__init__(self,core)

        path = os.path.realpath(__file__)
        path = path.replace("__init__.pyc","")
        self._path = path.replace("__init__.py","")

        self._load_manifest()

    """
    BEGIN IMPLEMENTING YOUR MODULE HERE
    """

    def render_pure_html(self,widget_id,args={}):
        content = self.get_content(widget_id)
        menu_id = content['menuId']
        action_manager = self._core.get_action_manager()
        menu = action_manager.get_menu_by_id(menu_id)
        menu_items = menu.get_menu_items()

        render = StringIO()
        for menu_item in menu_items:
            link = menu_item.get_action_list().render_link()
            name = menu_item.get_name()
            render.write('&nbsp;<a href="%s">%s</a>'%(link, name))
            if content['orientation'] == Module.VERTICALLY:
                render.write('<br>')

        return render.getvalue()

    def render_html(self,widget_id,args={}):
        return self.render_pure_html()

    def render_javascript(self,widget_id,args={}):
        return ""

    def set_content(self, widget_id, page_id, menu_id, orientation):
        page_id = int(page_id)
        menu_id = int(menu_id)
        orientation = int(bool(orientation))
        
        db = self._core.get_db()
        stmnt = "UPDATE OR INSERT INTO ${flatmenu} (MOD_INSTANCE_ID, FMN_SIT_ID, FMN_MNU_ID, FMN_ORIENTATION) \
                   VALUES (?,?,?,?) MATCHING (MOD_INSTANCE_ID) ;"
        db.query(self, stmnt, (widget_id, page_id, menu_id, orientation), commit=True)


    def get_content(self, widget_id):
        db = self._core.get_db()
        stmnt = "SELECT FMN_SIT_ID, FMN_MNU_ID, FMN_ORIENTATION FROM ${flatmenu} WHERE MOD_INSTANCE_ID = ? ;"
        cur = db.query(self, stmnt, (widget_id,))
        row = cur.fetchonemap()
        if row is not None:
            return {'pageId':row["FMN_SIT_ID"],
                    'menuId':row["FMN_MNU_ID"],
                    'orientation':row["FMN_ORIENTATION"]}
        else:
            return {"pageId":None,
                    "menuId":None,
                    "orientation":Module.HORIZONTALLY}

