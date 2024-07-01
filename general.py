"""
These are common steps that any of tests may use.
"""

from buildbot.plugins import steps, util

PROPERTIES = [
        util.FileParameter(
            name="custom_postgresql.conf",
            label="Upload postgresql.conf overrides",
            default=""
            ),
        util.FileParameter(
            name="postgresql.patch",
            label="Upload PostgreSQL patch (must be base64 encoded)",
            default=""
            ),
        util.FileParameter(
            name="dbt.patch",
            label="Upload DBT kit patch (must be base64 encoded)",
            default=""
            ),
        ]

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

PATCHDBT = [
        steps.ShellCommand(
            name="Apply DBT kit patch",
            doStepIf=lambda step: step.build.getProperties(). \
                    hasProperty("dbt.patch") and \
                    step.build.getProperty("dbt.patch"),
            command=[
                'sh', '-c',
                util.Interpolate(
                    "echo \"%(prop:dbt.patch)s\" > ../dbt.patch && "
                    "base64 -d ../dbt.patch | patch -p1"
                    ),
                ],
            haltOnFailure=True,
            workdir=util.Interpolate("%(prop:buildername)s"),
            )
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

def IsForceScheduler(step):
    '''Check if the force scheduler was used, which uses a naming convention
    that starts with run-'''
    if step.getProperty("scheduler").startswith("run-"):
        return True
    return False

def IsNotForceScheduler(step):
    '''Check if the force scheduler was not used, which uses a naming
    convention that starts with run-'''
    if IsForceScheduler(step):
        return False
    return True
