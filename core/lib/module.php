<?php
namespace scv;

include_once "core.php";

class ModuleException extends \Exception{}

interface IModule{
	public function getName();
	
	public function renderHTML($moduleInstanceId);
	
	public function renderJavascript($moduleInstanceId);
	
}

class Module implements IModule {
	private $name = testmodul;
	
	public function __construct($modulename){}
	
	public function renderHTML($moduleInstanceId){
		
	}
	
	public function renderJavascript($moduleInstanceId){
		
	}
	
	public function getName(){
		return $this->name;
	}
}

class ModuleManager extends Singleton {
	/**
	 *  This function builds the tables that are necessary
	 *  to run the Module
	 */
	
	private static $instance = null;
	
	public static function getInstance(){
		if (ModuleManager::$instance==null){
			ModuleManager::$instance = new ModuleManager();
			ModuleManager::$instance->init();
		}
		return ModuleManager::$instance;
	}
	
	protected function init(){}
	
	private function createDatabaseTables($tables,$moduleId){
		$core =  Core::getInstance();
		$core->getDB()->createTableForModule($tables,$moduleId);
	}
	
	private function removeDatabaseTables($tables,$moduleId){
		$core = Core::getInstance();
		$core->getDB()->removeTableForModule($tables,$moduleId);
	}
	
	/**
	 * This function creates Rights that are necessary for
	 * the module
	 */
	
	private function createRights($manifest, $moduleId){
		$rights = $manifest->rights;
		$core = Core::getInstance();
		$rightsManager = $core->getRightsManager();
		foreach($rights as $right){
		  $rightsManager->createRight($right,$manifest->name);	
		}
		return;
	}
	
	private function removeRights($manifest, $moduleId){
		$rights = $manifest->rights;
		$core = Core::getInstance();
		$rightsManager = $core->getRightsManager();
		foreach($rights as $right){
		  $rightsManager->removeRight($right,$manifest->name);	
		}
		return;
	}
		
	
	/**
	 * registerModule registers the Module and yields a unique moduleid
	 */
	public function registerModule($manifest){
		$core =  Core::getInstance();
		$db = $core->getDB();
		$newModuleId = $db->getSeqNext("MOD_GEN");
		$statement = "INSERT INTO MODULES (MOD_ID, MOD_NAME, MOD_DISPLAYNAME, MOD_VERSIONMAJOR, MOD_VERSIONMINOR, MOD_VERSIONREV)
		              VALUES (?,?,?,?,?,?);";
		$db->query($core,$statement,array($newModuleId, $manifest->name, $manifest->hrname, $manifest->version_major,
		                                  $manifest->version_minor, $manifest->revision));
	    return $newModuleId;
	}
	
	public function unregisterModule($manifest){
		$core =  Core::getInstance();
		$db = $core->getDB();
		
		$statement = "DELETE FROM MODULES WHERE MOD_NAME = ?;";
		$db->query($core,$statement,array($manifest->name,));
	    return;
	}
	
	public  function installModule($moduleId){
		$core = Core::getInstance();
		$modulesPath = $core->getConfig()->getEntry("modules.path");
		if (is_dir("../".$modulesPath.$moduleId)){
			throw new ModuleException("InstallationError: This Module is already installed (Directory Exists)");
		}

		system('mkdir ../'.$modulesPath.escapeshellarg($moduleId)." > /dev/null");
		system('tar xfz /tmp/'.escapeshellarg($moduleId).'.tar.gz -C ../'.$modulesPath.escapeshellarg($moduleId).'/ > /dev/null');
		
		$manifestRaw = file_get_contents('../'.$modulesPath.$moduleId.'/manifest.json');
		if ($manifestRaw == false){
			throw new ModuleException("InstallationError: $moduleId is not a valid Scoville Module");
			return;
		}
		
		$manifest = json_decode($manifestRaw);
		
		if ($manifest == null){
			throw new ModuleException("InstallationError: Manifest seems to be broken. Validate!");
			return;
		}
				
		$moduleNumber = ModuleManager::registerModule($manifest);
		ModuleManager::createDatabaseTables($manifest->tables, $moduleNumber);
		ModuleManager::createRights($manifest, $moduleNumber); //TODO: Implementiere createRights
		
		//Cleanup
		system('rm /tmp/'.escapeshellarg($moduleId).".tar.gz > /dev/null");
	}
	
	public function addRepository($ip, $port, $name = null) {
		$repository = new Repository(null, $name, $ip, $port, null);
		return $repository;
	}
	
	public function removeRepository($id) {
		
	}
	
	public function getRepository($id) {
		$core = Core::getInstance();
		$db = $core->getDB();
		$result = $db->query($core,"select rep_id, rep_name, rep_ip, rep_port, rep_lastupdate from repository where rep_id = ?;", array($id));
		$row = $db->fetchArray($result);
		$repository = new Repository($row['REP_ID'],$row['REP_NAME'],$row['REP_IP'],$row['REP_PORT'],$row['REP_LASTUPDATE']);
		return $repository;
	}
	
	public function installModuleFromRepository($repository, $moduleId){
		//TODO: Implement
	}
	
	public function uninstallModule($moduleId){
		$core = Core::getInstance();
		$modulesPath = $core->getConfig()->getEntry("modules.path");
		if (!is_dir("../".$modulesPath.$moduleId)){
			throw new ModuleException("InstallationError: This Module is not installed (Directory Exists)");
		}
		
		//TODO: Ueberpruefen, ob modul noch irgendwo verwendet wird.
		
		$db = $core->getDB();
		
		$result = $db->query($core,"SELECT MOD_ID FROM MODULES WHERE MOD_NAME = ?;", array($moduleId));
		$row = $db->fetchArray($result);
		$moduleNumber = $row['MOD_ID'];
		 
		
		$manifestRaw = file_get_contents('../'.$modulesPath.$moduleId.'/manifest.json');
		if ($manifestRaw == false){
			throw new ModuleException("InstallationError: $moduleId is not a valid Scoville Module");
			return;
		}
		
		$manifest = json_decode($manifestRaw);
		
		if ($manifest == null){
			throw new ModuleException("InstallationError: Manifest seems to be broken. Validate!");
			return;
		}
				
		ModuleManager::removeDatabaseTables($manifest->tables, $moduleNumber);
		ModuleManager::removeRights($manifest, $moduleNumber); //TODO: Implementiere createRights
		$moduleNumber = ModuleManager::unregisterModule($manifest);
		
		//Delete module on file system
		system('rm -r ../'.$modulesPath.escapeshellarg($moduleId)." > /dev/null");
	}
	
	public function loadModule($moduleName){
		$core = Core::getInstance();
		try{
			include_once $moduleName."/module.php";
			$moduleClass = str_replace(".","_", $moduleName);
			//eval("\$module = new $moduleClass(\$core);");
			$module = new $moduleClass($core);
			return $module;
		}catch(ModuleException $e){}
	}
	
	public function loadModuleById($moduleId){
		$core = Core::getInstance();
		$db = $core->getDB();
		$stmnt = "SELECT MOD_NAME FROM MODULES WHERE MOD_ID = ? ;";
		$res = $db->query($core,$stmnt,array($moduleId));
		if ($set = $db->fetchArray($res)){
			$moduleName = $set['MOD_NAME'];
		}else{
			throw new ModuleException("Load Module: Module with id $moduleId does not exist!");
		}
		try{
			include_once $moduleName."/module.php";
			$moduleClass = str_replace(".","_", $moduleName);
			//eval("\$module = new $moduleClass(\$core);");
			$module = new $moduleClass($core);
			return $module;
		}catch(ModuleException $e){}
	}
	
}

class Repository {
	private $id = null;
	private $name = null;
	private $ip = null;
	private $port = null;
	private $lastupdate = null;
	
	public function __construct($id, $name, $ip, $port, $lastupdate) {
		$this->id = $id;
		$this->name = $name;
		$this->ip = $ip;
		$this->port = $port;
		$this->lastupdate = $lastupdate;
	}
	
	private function getHost() {
		if($port == 80) {
			$host = "http://{$this->ip}/";
		} else {
			$host = "http://{$this->ip}:{$this->port}/";
		}		
		return $host;
	}
	
	public function getAllModules() {
		$list = json_decode(file_get_contents($this->getHost()."proto.php?j=".json_encode(array("c"=>1))));
		return $list;
	}
	
	public function getAllVersions($moduleid) {
		$list = json_decode(file_get_contents($this->getHost()."proto.php?j=".json_encode(array("c"=>2,"m"=>$moduleid))));
		return $list;
	}
	
	public function getDependencies($moduleid) {
		
	}
	
	public function getDescDependencies($moduleid) {
		
	}
	
	public function getModule($moduleid) {
		
	}
	
	public function store() {
		
	}
}

?>
