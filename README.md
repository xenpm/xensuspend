# xensuspend #

xensuspend is in early development stages.

This should be a daemon that is running in Dom0 and controls system-wide suspend and resume.

It is able to suspend all guest domains before suspending Dom0 and
then wakeup everything in reverse order.

It tries to analyze dependencies between domains to suspend
frontends before backends.

Right now it is implemented as one-shot script, not as a daemon.
