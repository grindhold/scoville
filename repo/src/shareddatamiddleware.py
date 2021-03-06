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


from logger import logger
from mimetypes import guess_type


class SharedDataMiddleware(object):
    """
    A WSGI middleware that provides static content.
    """

    def __init__(self, wrap_app, location):
        """
        Initializes this SharedDataMiddleware with a wrapped application and
        the location of the static content (e. g. 'static').
        """
        self._location = location
        self._wrap_app = wrap_app

    def __call__(self, environ, start_response):
        """
        If the wsgi PATH_INFO starts with the static contents location, it will be returned.
        Otherwise the wrapped application will be called.
        """
        if environ['REQUEST_METHOD'] == 'GET' and environ['PATH_INFO'].startswith('/%s/' % self._location):
            logger.info('GET from %s: %s' % (environ.get('REMOTE_ADDR', 'unknown'), environ['PATH_INFO']))
            prefix = "/usr/share/skdrepo/"
            path = prefix + environ['PATH_INFO'][1:]
            try:
                f = open(path, 'r')
                data = f.read()
                f.close()
                (mime, encoding) = guess_type(path)
                status = '200 OK'  
                response_headers = [('Content-Type', mime)]
                response_body = [data]
            except IOError, e:
                logger.warning('failed to open file: %s' % path)
                status = '404 Not Found'
                response_headers = [('Content-Type', 'text/plain')]
                response_body = ['404 Not Found - \'%s\'' % path]

            start_response(status, response_headers)
            logger.debug('response to %s: %s, %s' % (environ['REMOTE_ADDR'], status, str(response_headers)))
            return response_body

        else:
            return self._wrap_app(environ, start_response)

