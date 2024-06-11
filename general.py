"""
These are common steps that any of tests may use.
"""

from buildbot.plugins import steps, util

CLEANUP = [
        steps.RemoveDirectory(
            name="Remove previous load logs",
            dir=util.Interpolate("%(prop:builddir)s/load"),
            ),
        steps.RemoveDirectory(
            name="Remove previous pgdata",
            dir=util.Interpolate("%(prop:builddir)s/pgdata"),
            ),
        steps.RemoveDirectory(
            name="Remove previous results",
            dir=util.Interpolate("%(prop:builddir)s/results"),
            ),
        steps.RemoveDirectory(
            name="Remove previous test installation",
            dir=util.Interpolate("%(prop:builddir)s/usr"),
            ),
        ]

STATS_SYSTEM = [
        steps.ShellCommand(
            name="Operating system kernel parameters",
            command=['sysctl', '-a'],
            env={'PATH': "/sbin:${PATH}"},
            alwaysRun=True,
            ),
        steps.ShellCommand(
            name="PostgreSQL log",
            command=[
                'cat',
                util.Interpolate("%(prop:builddir)s/pgdata/pg.log"),
                ],
            alwaysRun=True,
            ),
        ]

CATPREFIX = "cat %(prop:builddir)s/results/throughput/sysstat"
STATS_DSS = [
        steps.ShellCommand(
            name="pidstat",
            command=['sh', '-c', util.Interpolate(f"{CATPREFIX}/pidstat.txt")],
            alwaysRun=True,
            ),
        steps.ShellCommand(
            name="Bock Device Stats",
            command=[
                'sh', '-c',
                util.Interpolate(f"{CATPREFIX}/sar/sar-blockdev.csv"),
                ],
            alwaysRun=True,
            ),
        steps.ShellCommand(
            name="CPU Stats",
            command=[
                'sh', '-c', util.Interpolate(f"{CATPREFIX}/sar/sar-cpu.csv"),
                ],
            alwaysRun=True,
            ),
        steps.ShellCommand(
            name="Memory Stats",
            command=[
                'sh', '-c', util.Interpolate(f"{CATPREFIX}/sar/sar-mem.csv"),
                ],
            alwaysRun=True,
            ),
        steps.ShellCommand(
            name="Network Stats",
            command=[
                'sh', '-c', util.Interpolate(f"{CATPREFIX}/sar/sar-net.csv"),
                ],
            alwaysRun=True,
            ),
        steps.ShellCommand(
            name="Paging Stats",
            command=[
                'sh', '-c',
                util.Interpolate(f"{CATPREFIX}/sar/sar-paging.csv"),
                ],
            alwaysRun=True,
            ),
        steps.ShellCommand(
            name="Swapping Stats",
            command=[
                'sh', '-c', util.Interpolate(f"{CATPREFIX}/sar/sar-swap.csv"),
                ],
            alwaysRun=True,
            ),
        ]

CATPREFIX = "cat %(prop:builddir)s/results/db/*/sysstat"
STATS_OLTP = [
        steps.ShellCommand(
            name="pidstat",
            command=['sh', '-c', util.Interpolate(f"{CATPREFIX}/pidstat.txt")],
            alwaysRun=True,
            ),
        steps.ShellCommand(
            name="Bock Device Stats",
            command=[
                'sh', '-c',
                util.Interpolate(f"{CATPREFIX}/sar/sar-blockdev.csv"),
                ],
            alwaysRun=True,
            ),
        steps.ShellCommand(
            name="CPU Stats",
            command=[
                'sh', '-c', util.Interpolate(f"{CATPREFIX}/sar/sar-cpu.csv"),
                ],
            alwaysRun=True,
            ),
        steps.ShellCommand(
            name="Memory Stats",
            command=[
                'sh', '-c', util.Interpolate(f"{CATPREFIX}/sar/sar-mem.csv"),
                ],
            alwaysRun=True,
            ),
        steps.ShellCommand(
            name="Network Stats",
            command=[
                'sh', '-c', util.Interpolate(f"{CATPREFIX}/sar/sar-net.csv"),
                ],
            alwaysRun=True,
            ),
        steps.ShellCommand(
            name="Paging Stats",
            command=[
                'sh', '-c',
                util.Interpolate(f"{CATPREFIX}/sar/sar-paging.csv"),
                ],
            alwaysRun=True,
            ),
        steps.ShellCommand(
            name="Swapping Stats",
            command=[
                'sh', '-c', util.Interpolate(f"{CATPREFIX}/sar/sar-swap.csv"),
                ],
            alwaysRun=True,
            ),
        ]
