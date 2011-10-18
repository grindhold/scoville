qx.Class.define("scoville_admin.ServerPage",{
	extend: qx.ui.tabview.Page,
	
	construct : function(app, server){
		this.app=app;
		this.base(arguments);
		this.server = server;
		this.setLabel(server.name);
		this.setIcon('scoville_admin/server.png');
		
		this.tabs = app.tabview;
		if (server.loggedin){
			this.buildGui();
		}else{
			this.buildLogin();
		}
		this.setShowCloseButton(true);
		this.tabs.add(this);
		
	},
	
	members: {
		buttonEnter:null,
		buttonCancel:null,
		label:null,
		ipentry:null,
		server:null,
		infobox:null,
		infolabel:null,
		heading:null,
		
		buildLogin : function (){
			this.heading = new qx.ui.basic.Label().set({value:"<span style='font-size:18px; font-weight:bold;'>Authentication</span>",rich:true});
			
			this.infobox = new qx.ui.groupbox.GroupBox("Credentials", "scoville_admin/server.png");
			this.infobox.setLayout(new qx.ui.layout.Basic());
			this.infolabel = new qx.ui.basic.Label("Please enter your credentials for a Scoville server here!");
			this.setLayout(new qx.ui.layout.VBox());
			this.buttonEnter = new qx.ui.form.Button("Login");
			this.buttonCancel = new qx.ui.form.Button("Cancel");
			this.userlabel = new qx.ui.basic.Label("Username:");
			this.userentry = new qx.ui.form.TextField();
			this.passwordlabel = new qx.ui.basic.Label("Password:");
			this.passwordentry = new qx.ui.form.PasswordField();
			
			this.buttonEnter.addListener("execute", this.enterNewServerCallback(this));
			this.buttonCancel.addListener("execute", this.cancelCallback(this));
			
			this.infobox.add(this.infolabel,{top:10, left:100});
			this.infobox.add(this.userlabel,{top:50,left:100});
			this.infobox.add(this.userentry,{top:50,left:250});
			this.infobox.add(this.passwordlabel,{top:75,left:100});
			this.infobox.add(this.passwordentry,{top:75,left:250});
			this.infobox.add(this.buttonCancel,{top:100,left:100});
			this.infobox.add(this.buttonEnter,{top:100, left:250});
			this.add(this.heading);
			this.add(this.infobox);
		},
		
		buildGui : function(){
			
		},
		
		
		cancelCallback: function(me){
			return function(){}
			/*return function(){
				me.tabs.remove(me);
			}*/
		},
		
		enterNewServerCallback : function(me){
			return function(){
		  		var username = me.userentry.getValue();
			    var password = me.passwordentry.getValue();
				
 				me.tabs.remove(me);
				
				me.app.createRPCObject(me.server.ip).callAsync(me.server.createAuthenticationHandler(me.server),"authenticateUser",username,password);
			};
			
			
		}
		
		
	}
});
