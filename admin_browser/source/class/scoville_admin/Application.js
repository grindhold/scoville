/* ************************************************************************

   Copyright:

   License:

   Authors:

************************************************************************ */

/* ************************************************************************

#asset(scoville_admin/*)

************************************************************************ */

/**
 * This is the main application class of your custom application "scoville_admin"
 */
qx.Class.define("scoville_admin.Application",
{
  extend : qx.application.Standalone,



  /*
  *****************************************************************************
     MEMBERS
  *****************************************************************************
  */

  members :
  {
    /**
     * This method contains the initial application code and gets called 
     * during startup of the application
     * 
     * @lint ignoreDeprecated(alert)
     */
    
    createRPCObject : function(ip){
    	var srv = document.getElementById('srvip');
    	var rpc = new qx.io.remote.Rpc("http://"+srv.value+"/rpc/","scoville_admin.scvRpc");
        return rpc;
    },
    
    addUser : function(users){
    	if (this.newUserPage == null){
    		this.newUserPage = new scoville_admin.NewUserPage(this,users);
    		this.tabview.setSelection([this.newUserPage]);
    	}else{
    	    this.tabview.setSelection([this.newUserPage]);
    	}
    },
    
    addRole : function(roles){
    	if (this.newRolePage == null){
    		this.newRolePage = new scoville_admin.NewRolePage(this,roles);
    		this.tabview.setSelection([this.newRolePage]);
    	}else{
    		this.tabview.setSelection([this.newRolePage]);
    	}
    },
    
    loadServer : function(ip,me,username,password){
    	//TODO: code Fuer Ajax-Request
    	var servers = this.tree.getRoot().getChildren();
    	for (var i = 0; i < servers.length; i++){
    		if (ip == servers[i].ip){
    			return 0;
    		}
    	}
    	try {
    		var servernode = new scoville_admin.Server(this,ip,username,password);
    		this.tree.getRoot().add(servernode);
    	}
    	catch(e){}
    	return 1;
    },
    
    storeServerlistCookie : function (){
    	var servers = this.tree.getRoot().getChildren();
    	var serverlist = [];
    	for (var i = 0; i < servers.length; i++){
    		if (servers[i].classname == "scoville_admin.Server"){
    			serverlist.push (servers[i].getIp());
    		}
    	}
    	qx.bom.Cookie.set("scv_admin", qx.lang.Json.stringify(serverlist));
    },
    
    tabviewHandler : function(me){
    	return function(page){
    		me.tool.updateForPage(me.tabview.getSelection()[0]);
    	}
    },
    
    dragStartHandler : function(me){
    	return function(evt){
    		if (me.tree.getSelection()[0].classname == "scoville_admin.Widget"){
    			evt.addType("widget");
	    		evt.addAction("copy");
				evt.addAction("move");
				evt.addAction("alias");
    		}
    	}
    },
    
    dropRequest : function(me){
		return function(evt){
			if (evt.getCurrentType("widget")){
				evt.addData("widget", me.tree.getSelection()[0]);
			}
			return null;
		} 
	},
    
    main : function()
    {
      // Call super class
      this.base(arguments);

      // Enable logging in debug variant
      if (qx.core.Environment.get("qx.debug"))
      {
        // support native logging capabilities, e.g. Firebug for Firefox
        qx.log.appender.Native;
        // support additional cross-browser console. Press F7 to toggle visibility
        qx.log.appender.Console;
      }

      /*
      -------------------------------------------------------------------------
        Below is your actual application code...
      -------------------------------------------------------------------------
      */

      // Create a button
      this.mainpane = new qx.ui.splitpane.Pane();
      this.vbox = new qx.ui.layout.VBox();
      this.vcontainer = new qx.ui.container.Composite(this.vbox);
      this.tabview = new qx.ui.tabview.TabView();
      this.tabview.addListener("changeSelection", this.tabviewHandler(this));
      this.menu = new qx.ui.menubar.MenuBar();  
      this.tool = new scoville_admin.Toolbar();    
      this.button1 = new qx.ui.form.Button("First Button", "scoville_admin/test.png");
      this.button2 = new qx.ui.form.Button("LOL BUTTON" );
      this.testimg = new qx.ui.basic.Image("scoville_admin/config_header.png");
      
      this.tree = new qx.ui.tree.Tree();
      this.tree.addListener("dragstart", this.dragStartHandler(this));
      this.tree.addListener("droprequest", this.dropRequest(this));
      this.tree.setDraggable(true);
      
      
      // Document is the application root
      var doc = this.getRoot();
      
      //var testseite1 = new qx.ui.tabview.Page('aha.llllo','');
      //var testseite2 = new qx.ui.tabview.Page('gnihihihilllo','');
      
      var treeroot = new qx.ui.tree.TreeFolder('Scoville Infrastructure');
      treeroot.setIcon('scoville_admin/scoville.png');
      
      
      this.treecontextmenu = new scoville_admin.TreeContextMenu(this);
      this.tree.setContextMenu(this.treecontextmenu);
      this.tree.setRoot(treeroot);
      //this.tree.hideRoot=true;
      
      //Menu
      this.men_server = new qx.ui.menu.Menu();
      this.but_server = new qx.ui.menubar.Button('Server',null,this.men_server);

      
      this.menu.add(this.but_server);
      
      
      
      this.mainpane.add(this.tree, 1);
      this.mainpane.add(this.tabview, 4);
      this.vcontainer.add(this.testimg);
      this.vcontainer.add(this.menu);
      this.vcontainer.add(this.tool);
      this.vcontainer.add(this.mainpane,{flex:1});
      doc.add(this.vcontainer, {width:'100%',height:'100%'});
	
	  var srv = document.getElementById('srvip');
      this.loadServer(srv.value,'','');
      
	  treeroot.setOpen(true);    
    }

    
  }
});
