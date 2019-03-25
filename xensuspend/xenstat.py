# Copyright (C) 2019 EPAM Systems
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

from ctypes import cdll, c_char_p
from ctypes.util import find_library

xenstatlib = cdll.LoadLibrary(find_library("xenstat"))
xenstatlib.xenstat_domain_name.restype = c_char_p

class xenstat(object):
    def __enter__(self):
        self.handle = xenstatlib.xenstat_init()
        if self.handle == 0:
            raise Exception("Failed to initialize xenstat library")

        self.node = xenstatlib.xenstat_get_node(self.handle, 1)
        if self.node == 0:
            xenstatlib.xenstat_uninit(self.handle)
            raise Exception("Failed to get xenstat node")

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        xenstatlib.xenstat_free_node(self.node)
        xenstatlib.xenstat_uninit(self.handle)

        return False


    class xenstat_domain(object):
        def __init__(self, node, domid):
            self.domain = xenstatlib.xenstat_node_domain(node, domid)

        def name(self):
            return xenstatlib.xenstat_domain_name(self.domain).decode()

        def dying(self):
            return bool(xenstatlib.xenstat_domain_dying(self.domain))

        def crashed(self):
            return bool(xenstatlib.xenstat_domain_crashed(self.domain))

        def shutdown(self):
            return bool(xenstatlib.xenstat_domain_shutdown(self.domain))

        def paused(self):
            return bool(xenstatlib.xenstat_domain_paused(self.domain))

        def blocked(self):
            return bool(xenstatlib.xenstat_domain_blocked(self.domain))

        def running(self):
            return bool(xenstatlib.xenstat_domain_running(self.domain))

    def domain(self, domid):
        return self.xenstat_domain(self.node, domid)

