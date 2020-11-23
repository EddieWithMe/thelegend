# This file is part of krakenex.
#
# krakenex is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# krakenex is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser
# General Public LICENSE along with krakenex. If not, see
# <http://www.gnu.org/licenses/gpl-3.0.txt>.


import httplib
import urllib


class Connection:
    """Kraken.com connection handler.

    Public methods:
    close
    """

    def __init__(self, uri='api.kraken.com', timeout=30):
        """ Create an object for reusable connections.

        Arguments:
        uri     -- URI to connect to (default: 'https://api.kraken.com')
        timeout -- bl