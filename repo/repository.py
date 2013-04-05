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

import base64
import cStringIO
import hashlib
import json
import random
import tarfile

from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5

from database import DatabaseConnection

from session import Session

class Repository(object):
    def __init__(self, environ):
        self.environ = environ
        self.config = self.read_config('/etc/scvrepo/config.json')
        self.connection = DatabaseConnection(
                self.config['db.ip'],
                self.config['db.name'],
                self.config['db.user'],
                self.config['db.password']
            )
        self.connection.connect()

    
    def __del__(self):
        if self.connection:
            self.connection.disconnect()

    def get_db(self):
        return self.connection

    def read_config(self, path):
        f = open(path, 'r')
        config = json.loads(f.read())
        f.close()
        return config


    def verify_admin(self):
        try:
            if not self.environ['beaker.session']['privileged']:
                raise Exception('You are no admin')
        except Exception, e:
            raise Exception('You are no admin')


    def generate_salt(self):
        salt = ""
        length = random.randint(128, 255)
        for i in range(0, length):
            salt += chr(random.randint(0, 255))
        return salt


    def get_all_modules(self):
        result = self.connection.query('SELECT mod_displayname, mod_md5, mod_signature, mod_name,' +
                'mod_versionmajor, mod_versionminor, mod_versionrev ' +
                'FROM modules JOIN (SELECT mod_name vername ' +
                ',MAX(mod_versionmajor*10000000 ' +
                '+mod_versionminor*100000 ' +
                '+mod_versionrev) ver ' +
                'FROM modules ' +
                'GROUP BY mod_name) ' + 
                'ON vername = mod_name ' + 
                'AND ver = mod_versionmajor*10000000 ' + 
                '+mod_versionminor*100000 ' +
                '+mod_versionrev;')
        result = result.fetchallmap()
        modules = [{'name' : m['mod_name'],
                    'hrname' : m['mod_displayname'],
                    'version_major' : m['mod_versionmajor'],
                    'version_minor' : m['mod_versionminor'],
                    'revision' : m['mod_versionrev'],
                    'signature' : m['mod_signature']} for m in result]
        return modules


    def get_versions_of_module(self, module):
        result = self.connection.query('SELECT mod_name, mod_displayname, mod_signature, mod_id, ' +
                'mod_versionmajor, mod_versionminor, mod_versionrev ' +
                'FROM modules ' +
                'WHERE mod_name = ?;', module['name'])
        result = result.fetchallmap()
        modules = [{'name' : m['mod_name'],
                    'hrname' : m['mod_displayname'],
                    'version_major' : m['mod_versionmajor'],
                    'version_minor' : m['mod_versionminor'],
                    'revision' : m['mod_versionrev'],
                    'signature' : m['mod_signature']} for m in result]
        return modules


    def resolve_dependencies_downwards(self, module):
        result = self.connection.query('SELECT mod_id FROM modules WHERE mod_name = ? ' +
                'AND mod_versionmajor = ? AND mod_versionminor = ? AND mod_versionrev = ? ' +
                'AND mod_signature = ?;',
                (module['name'], module['version_major'], module['version_minor'],
                module['revision'], module['signature']))
        result = result.fetchallmap()
        if result:
            mod_id = result[0]['mod_id']
            result = self.connection.query('SELECT DISTINCT dep_mod_dependson ' +
                    'FROM dependencies ' +
                    'WHERE dep_mod_id = ?;', mod_id)
            result = result.fetchallmap()
            mod_ids = [mod_id]

            while result:
                for mod in result:
                    mod_ids.append(mod['dep_mod_dependson'])
                mod_ids_str = ','.join(map(str, mod_ids))
                result = self.connection.query('SELECT dep_mod_dependson ' +
                        'FROM dependencies ' +
                        'WHERE dep_mod_id IN ? AND dep_mod_dependson NOT IN ?;', 
                        (mod_ids_str, mod_ids_str));
                result = result.fetchallmap()
            result = self.connection.query('SELECT mod_name, mod_displayname, mod_signature, mod_id, ' +
                    'mod_versionmajor, mod_versionminor, mod_versionrev ' +
                    'FROM modules WHERE mod_id IN (?) AND mod_id != ?;', 
                    (','.join(map(str, mod_ids)), mod_id));
            result = result.fetchallmap()
            modules = [{'name' : m['mod_name'],
                        'hrname' : m['mod_displayname'],
                        'version_major' : m['mod_versionmajor'],
                        'version_minor' : m['mod_versionminor'],
                        'revision' : m['mod_versionrev'],
                        'signature' : m['mod_signature']} for m in result]
            return modules

        else:
            raise Exception('Module does not exist: %s' % module['name'])


    def resolve_dependencies_upwards(self, module):
        result = self.connection.query('SELECT mod_id ' +
                'FROM modules ' +
                'WHERE mod_name = ? AND mod_versionmajor = ? AND mod_versionminor = ? ' +
                'AND mod_versionrev = ? AND mod_signature = ?;',
                (module['name'], module['version_major'], module['version_minor'],
                module['revision'], module['signature']))
        result = result.fetchallmap()
        if result:
            mod_id = result[0]['mod_id']
            result = self.connection.query('SELECT DISTINCT dep_mod_id ' +
                    'FROM dependencies ' +
                    'WHERE dep_mod_dependson = ?;', mod_id);
            result = result.fetchallmap()
            mod_ids = [mod_id]
            while result:
                for mod in result:
                    mod_ids.append(mod['dep_mod_id'])
                mod_ids_str = ','.join(map(str, mod_ids))
                result = self.connection.query('SELECT dep_mod_id ' +
                        'FROM dependencies ' +
                        'WHERE dep_mod_dependson IN ? AND dep_mod_id NOT IN ?;',
                        (mod_ids_str, mod_ids_str))
                result = result.fetchallmap()

            result = self.connection.query('SELECT mod_name, mod_displayname, mod_signature, mod_id, ' +
                    'mod_versionmajor, mod_versionminor, mod_versionrev ' +
                    'FROM modules ' +
                    'WHERE mod_id IN (?) and mod_id != ?;',
                    (','.join(map(str, mod_ids)), mod_id))
            result = result.fetchallmap()
            modules = [{'name' : m['mod_name'],
                        'hrname' : m['mod_displayname'],
                        'version_major' : m['mod_versionmajor'],
                        'version_minor' : m['mod_versionminor'],
                        'revision' : m['mod_versionrev'],
                        'signature' : m['mod_signature']} for m in result]
            return modules
        else:
            raise Exception('Module does not exist: %s' % module['name'])


    def download_module(self, module):
        result = self.connection.query('SELECT mod_name, mod_displayname, mod_id, mod_versionmajor, ' +
                'mod_versionminor, mod_versionrev, mod_data, mod_signature ' +
                'FROM modules ' +
                'WHERE mod_name = ? AND mod_versionmajor = ? AND mod_versionminor = ? ' +
                'AND mod_versionrev = ? AND mod_signature = ?;',
                (module['name'], module['version_major'], module['version_minor'],
                module['revision'], module['signature']))
        result = result.fetchallmap()
        if result:
            mod = result[0]
            # TODO fix reading from blob mod_data
            result_mod = {'name' : mod['mod_name'],
                        'hrname' : mod['mod_displayname'],
                        'version_major' : mod['mod_versionmajor'],
                        'version_minor' : mod['mod_versionminor'],
                        'revision' : mod['mod_versionrev'],
                        'signature' : mod['mod_signature']}
            return (result_mod, mod['mod_data'])
        else:
            raise Exception('Module does not exist: %s' % module['name'])


    def get_latest_version(self, module):
        result = self.connection.query('SELECT mod_displayname, mod_signature, mod_name, ' +
                'mod_versionmajor, mod_versionminor, mod_versionrev ' +
                'FROM modules JOIN (SELECT mod_name vername, ' +
                'max(mod_versionmajor*10000000+mod_versionminor*100000+mod_versionrev) ver ' + 
                'FROM modules' + 
                'GROUP BY mod_name) ' +  
                'ON vername = mod_name ' + 
                'AND ver = mod_versionmajor*10000000+mod_versionminor*100000+mod_versionrev ' +
                'WHERE mod_name = ?;', module['name']);
        result = result.fetchallmap()
        if result:
            mod = result[0]
            result_mod = {'name' : mod['mod_name'],
                        'hrname' : mod['mod_displayname'],
                        'version_major' : mod['mod_versionmajor'],
                        'version_minor' : mod['mod_versionminor'],
                        'revision' : mod['mod_versionrev'],
                        'signature' : mod['mod_signature']}
            return result_mod
        else:
            raise Exception('Module does not exist: %s' % module['name'])


    def login(self, password, response_header):
        result = self.connection.query("SELECT VAL FROM CONFIG \
                WHERE PARAM = 'password' OR PARAM = 'salt' ORDER BY PARAM ASC;")
        result = result.fetchallmap()

        db_hash = result[0]['VAL']
        salt = base64.b64decode(result[1]['VAL'])
        hashvalue = hashlib.sha512(password.encode('utf-8')  + salt).hexdigest()
        is_valid = hashvalue == db_hash
        
        session = Session.create_session(self, response_header)
        session.set_admin(is_valid)
        session.store()
        return is_valid


    def logout(self):
        try:
            self.environ['beaker.session'].delete()
        except KeyError, e:
            pass


    def change_password(self, password):
        self.verify_admin()
        
        salt = self.generate_salt()
        hashvalue = hashlib.sha512(password + salt).hexdigest()
        salt = base64.b64encode(salt)
        self.connection.query('UPDATE config SET val = ? WHERE param = \'password\';', hashvalue,commit=True)
        self.connection.query('UPDATE config SET val = ? WHERE param = \'salt\';', salt,commit=True)
    

    def register_developer(self, name, fullname, publickey):
        self.verify_admin()

        dev_id = self.connection.get_seq_next('DEV_GEN')
        self.connection.query('INSERT INTO developer (dev_id, dev_name, dev_fullname, dev_publickey) ' +
                'VALUES (?, ?, ?, ?);', (dev_id, name, fullname, publickey),commit=True)


    def unregister_developer(self, dev_id):
        self.verify_admin()

        self.connection.query('UPDATE developer SET dev_publickey = \'\' ' +
                'WHERE dev_id = ?;', dev_id,commit=True)


    def upload_module(self, data, signature):
        result = self.connection.query('SELECT dev_id, dev_name, dev_publickey ' +
                'FROM developer;')
        valid = False
        hashobj = SHA256.new(data)
        for dev in result:
            key = RSA.importKey(dev['dev_publickey'])
            verifier = PKCS1_v1_5.new(key)
            valid = verifier.verify(hashobj, signature)
            if valid:
                dev_id = dev['dev_id']
                break;
        if not valid:
            raise Exception('Signature verification failed')
        
        print ("DEVID: " + str(dev_id)) #TODO debug output

        datafile = cStringIO.StringIO(data)
        tar = tarfile.open(fileobj = datafile, mode = 'r:gz') 
        try:
            manifestdata = tar.extractfile('manifest.json').read()
        except Exception, e:
            raise Exception('Error while reading manifest')
        manifest = json.loads(manifestdata)

        result = self.connection.query('SELECT MAX(mod_versionrev) AS maxrevision ' +
                'FROM modules ' +
                'WHERE mod_name = ?;', manifest['name'])
        result = result.fetchallmap()
        if result:
            revision = result['maxrevision'] + 1
        else:
            revision = 0
        mod_id = self.connection.get_seq_next('MOD_GEN')
        md5 = hashlib.md5(data).hexdigest()

        key = RSA.importKey(self.get_private_key())
        hashobj = SHA256.new(data)
        signer = PKCS1_v1_5.new(key)
        repo_signature = base64.b64_encode(signer.sign(hashobj))
        
        # TODO blob working?
        self.connection.query('INSERT INTO mdoules (mod_id, mod_name, mod_displayname, ' +
                'mod_versionmajor, mod_versionminor, mod_versionrev, mod_md5, mod_signature, ' +
                'mod_data VALUE (?,?,?,?,?,?,?,?,?);',
                (mod_id, manifest['name'], manifest['hrname'], manifest['version_major'],
                manifest['version_minor'], revision, md5, repo_signature, cStringIO.StringIO(data)),commit=True)


    def delete_module(self, identifier, major=None, minor=None, revision=None):
        self.verify_admin()

        if major:
            if minor:
                if revision:
                    self.connection.query('DELETE FROM modules ' +
                            'WHERE mod_name = ? AND mod_versionmajor = ? AND ' +
                            'mod_versionminor = ? AND mod_versionrev = ?;',
                            (identifier, major, minor, revision),commit=True)
                else:
                    self.connection.query('DELETE FROM modules ' +
                            'WHERE mod_name = ? AND mod_versionmajor = ? AND ' +
                            'mod_versionminor = ?;',
                            (identifier, major, minor),commit=True)    
            else:
                self.connection.query('DELETE FROM modules ' +
                        'WHERE mod_name = ? AND mod_versionmajor = ?;',
                        (identifier, major),commit=True)    
        else:
            self.connection.query('DELETE FROM modules ' +
                    'WHERE mod_name = ?;',
                    identifier,commit=True)    


    def get_developers(self):
        self.verify_admin()

        result = self.connection.query('SELECT dev_id, dev_name, dev_fullname ' +
                'FROM developer;')
        result = result.fetchallmap()
        developers = [{'devId' : d['dev_id'],
                        'name' : d['dev_name'],
                        'fullName' : d['dev_fullname']} for d in result]
        return developers


    def get_public_key(self):
        result = self.connection.query('SELECT val ' +
                'FROM config ' +
                'WHERE param = \'publickey\'')
        result = result.fetchallmap()
        if result:
            return result[0]['val']
        return None


    def get_private_key(self):
        result = self.connection.query('SELECT val ' +
                'FROM config ' +
                'WHERE param = \'privatekey\'')
        result = result.fetchallmap()
        if result:
            return result[0]['val']
        return None
