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

from ctypes import cdll, c_char_p, c_int, c_void_p, byref

libxenlight = cdll.LoadLibrary("libxenlight.so")

class libxl(object):
    def __enter__(self):
        self.ctx = c_void_p()
        ret = libxenlight.libxl_ctx_alloc(byref(self.ctx), 0, 0, 0)
        if ret != 0:
            raise Exception("Failed to reate libxl ctx: " + ret)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        libxenlight.libxl_ctx_free(self.ctx)

        return False

    def pause(self, domid):
        return libxenlight.libxl_domain_pause(self.ctx, domid)

    def unpause(self, domid):
        return libxenlight.libxl_domain_unpause(self.ctx, domid)

    def shutdown(self, domid):
        return libxenlight.libxl_domain_shutdown(self.ctx, domid)

    def reboot(self, domid):
        return libxenlight.libxl_domain_reboot(self.ctx, domid)

    def destroy(self, domid):
        return libxenlight.libxl_domain_destroy(self.ctx, domid)

    def suspend_trigger(self, domid):
        return libxenlight.libxl_domain_suspend_trigger(self.ctx, domid)

    def suspend_wakeup(self, domid):
        return libxenlight.libxl_domain_wakeup(self.ctx, domid)


