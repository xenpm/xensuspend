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
    deps = build_deps()
    print("Domain dependencies: " + str(deps))
    print("Suspend order: "+ str(get_suspend_order(deps)))

    if len (sys.argv) != 2:
        print("Use {} suspend to suspend system".format(sys.argv[0]))
        return

    if sys.argv[1] == "suspend":
        for d in get_suspend_order(deps):
            suspend_domain(d)
        for d in reversed(get_suspend_order(deps)):
            resume_domain(d)
    elif sys.argv[1] == "resume":
        for d in reversed(get_suspend_order(deps)):
            resume_domain(d)
    else:
        print("Unknown command")

    return 0

def suspend_domain(domid, timeout=60):
    if domid == 0:
        return suspend_dom0()

    print("Suspending domain {}".format(domid))
    with libxl() as xl:
        xl.suspend_trigger(domid)

    with xenstat() as xs:
        dom = xs.domain(domid)
        name = dom.name()
        while timeout > 0:
            print("Waiting {} to suspend, {} seconds left".format(name, timeout))
            if dom.paused():
                break
            time.sleep(1)
            timeout -= 1
            break
        if dom.running():
            raise Exception("Failed to suspend domain {} ({})".format(name, domid))

def resume_domain(domid, timeout=60):
    if domid == 0:
        return
    print("Resuming domain {}".format(domid))
    with libxl() as xl:
        xl.wake_up(domid)

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

