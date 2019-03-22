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


