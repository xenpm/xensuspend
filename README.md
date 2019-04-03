# xensuspend #

xensuspend is in early development stages.

This is a daemon that is running in Dom0 and controls system-wide suspend and resume.

It is able to suspend all guest domains before suspending Dom0 and
then wakeup everything in reverse order.

It tries to analyze dependencies between domains to suspend
frontends before backends.

It can be run in daemon mode if invoked as `xensuspend daemon`. In this case any domain can write `suspend` to own xenstore entry `control/system-suspend-req` to initiate full system suspend. You can do this with `xenstore-write`: `xenstore-write control/system-suspend-req suspend`.

