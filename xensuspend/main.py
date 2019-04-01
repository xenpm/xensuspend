#!/usr/bin/env python3

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

import argparse
import daemon
import daemon.pidfile
import pyxs
import sys
import time

from .xenstat import xenstat
from .libxl import libxl

def get_domain_ids():
    'Scan xenstore to get list of available domains'
    with pyxs.Client() as c:
        return [int(x) for x in c.list(b"/local/domain")]

def get_backends(domid):
    'Get list of backends for a given domain id'
    ret = set()
    with pyxs.Client() as c:
        path = "/libxl/{}".format(domid).encode()
        if not c.exists(path):
            return set()
        path = path + b"/device"
        dev_types = c.list(path)
        for dt in dev_types:
            devices = c.list(path + b"/" + dt)
            for device in devices:
                dev_path = path + b"/" + dt + b"/" + device
                frontend_path = c[dev_path + b"/frontend"]
                ret.add(int(c[frontend_path + b"/backend-id"]))
    return ret

def build_deps():
    '''
    Get dict where key is a domid and value is the list of domains
    that provide backends for that domain
    '''

    domains = get_domain_ids()
    dependencies = {}
    for domid in domains:
        backends = get_backends(domid)
        dependencies[domid] = backends

    return dependencies

def get_suspend_order(deps):
    ret = []
    deps = dict(deps)
    while deps:
        for k, v in deps.items():
            if not v:
                ret.append(k)
                del deps[k]
                for _, v1 in deps.items():
                    if k in v1:
                        v1.remove(k)
                break

        else:
            raise Exception("Loop in domain deps found: " + str(deps))

    ret.reverse()
    return ret

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices = ["suspend", "daemon"], help = "Action to perform. Use 'daemon' to run as a daemon")
    parser.add_argument("-f", "--foreground", action = 'store_true', help = "Run daemon in foreground (do not fork)")
    parser.add_argument("-v", "--verbose", action = 'store_true', help = "Print logs to stdout and errors to stderr")
    parser.add_argument("--pidfile", action = 'store', help = "Path to PID file", default = "/var/run/xensuspend.pid")
    args = parser.parse_args()

    if args.command == "suspend":
        system_suspend()
    elif args.command == "daemon":
        detach = None
        if args.foreground:
            detach = False

        stdout = sys.stdout if args.verbose else None
        stderr = sys.stderr if args.verbose else None
        pidfile = daemon.pidfile.PIDLockFile(args.pidfile)

        with daemon.DaemonContext(pidfile = pidfile, stdout = stdout, stderr = stderr, detach_process = detach):
            serve()

    return 0

def suspend():
    deps = build_deps()
    for d in get_suspend_order(deps):
        suspend_domain(d)

def resume():
    deps = build_deps()
    for d in reversed(get_suspend_order(deps)):
        resume_domain(d)
        time.sleep(3)

def format_control_node_path(domain):
    return "/local/domain/{}/control/system-suspend-req".format(domain).encode()

def setup_control_node(client, domain):
    path = format_control_node_path(domain)
    client.mkdir(path)
    client.set_perms(path, ["w{}".format(domain).encode()])

def serve():
    domains = []
    with pyxs.Client() as c:
        m = c.monitor()
        m.watch(b"@introduceDomain", "domain".encode())
        m.watch(b"@releaseDomain", "domain".encode())
        while True:
            path, token = next(m.wait())
            print("Event: ", path, token)
            if token.decode() == "domain":
                domains = on_domains_changed(domains, c, m)
            else:
                print("Signal from domain", token)
                data = (c[path])
                if data.decode() == "suspend":
                    system_suspend()

def on_domains_changed(old_domains, client, monitor):
    domains = get_domain_ids()
    added = set(domains) - set(old_domains)
    removed = set(old_domains) - set(domains)
    print("Old domains:", old_domains)
    print("New domains:", domains)
    print("Added:", added)
    print("Removed", removed)

    for d in added:
        setup_control_node(client, d)
        monitor.watch(format_control_node_path(d), str(d).encode())

    for d in removed:
        monitor.unwatch(format_control_node_path(d), str(d).encode())
    return domains

def system_suspend():
    suspend()
    resume()

def suspend_domain(domid, timeout=60):
    if domid == 0:
        return suspend_dom0()

    print("Suspending domain {}".format(domid))
    with libxl() as xl:
        xl.suspend_trigger(domid)

    while timeout > 0:
        with xenstat() as xs:
            dom = xs.domain(domid)
            print("Waiting {} to suspend, {} seconds left".format(dom.name(), timeout))
            if dom.shutdown():
                break
            time.sleep(1)
            timeout -= 1

    if timeout == 0:
        raise Exception("Failed to suspend domain {}".format(domid))

def resume_domain(domid, timeout=60):
    if domid == 0:
        return
    print("Resuming domain {}".format(domid))
    with libxl() as xl:
        xl.suspend_wakeup(domid)

def suspend_dom0():
    print("echo mem > /sys/power/state")
    with open("/sys/power/state", "wt") as f:
        f.write("mem")
    pass

def test_suspend_order():
    deps = {
        0: [],
        1: [0],
        2: [1, 0],
        3: [0, 1],
        4: [1, 0, 3],
        5: [1, 0, 3, 2, 6],
        6: [0, 4],
        }
    print(get_suspend_order(deps))

if __name__ == "__main__":
    main()

