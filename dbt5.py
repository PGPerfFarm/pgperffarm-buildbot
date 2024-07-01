"""
These are DBT-5 specific testing steps.
"""

from buildbot.plugins import steps, util

import general
import postgres

CMD = "%(prop:builddir)s/../test/dbt5.conf | tail -n 1 | cut -d '=' -f 2"

CUSTOMERS = f"$(grep -i ^customers {CMD})"
DURATION = f"$(grep -i ^duration {CMD})"
USERS = f"$(grep -i ^users {CMD})"
RAMPUP = f"$(( ($(grep -i ^rampup {CMD})  * 1000) / {USERS} ))"

DBT5PROPERTIES = [
        util.IntParameter(
            name="customers",
            label="Customers",
            default=1000,
            required=True,
            ),
        util.IntParameter(
            name="duration",
            label="Steady state duration in seconds",
            default=120,
            required=True,
            ),
        util.IntParameter(
            name="connection_delay",
            label="Seconds between starting users",
            default=1,
            required=True,
            ),
        util.IntParameter(
            name="users",
            label="Users",
            default=1,
            required=True,
            ),
        ]

DBT5STEPS = general.CLEANUP + \
        postgres.PGINSTALL + \
        [steps.Git(
            name="Clone DBT-5",
            repourl='https://github.com/osdldbt/dbt5.git',
            mode='full',
            method='fresh',
            workdir='dbt5',
            branch='main',
            alwaysUseLatest=True,
            haltOnFailure=True,
            )] + \
        [steps.Configure(
            name="Configure DBT-5",
            command=[
                'cmake',
                '-H.',
                '-Bbuilds/release',
                '-DCMAKE_INSTALL_PREFIX=/usr',
                ],
            workdir='dbt5',
            haltOnFailure=True,
            )] + \
        [steps.Compile(
            name="Build DBT-5",
            command=['make', '-f', 'Makefile.cmake', 'release'],
            workdir='dbt5',
            env={'PATH': util.Interpolate(
                "%(prop:builddir)s/usr/bin:${PATH}")},
            haltOnFailure=True,
            )] + \
        [steps.Compile(
            name="Install DBT-5",
            command=['make', 'install'],
            workdir='dbt5/builds/release',
            env={'DESTDIR': util.Interpolate(
                "%(prop:builddir)s")},
            haltOnFailure=True,
            )] + \
        [steps.Compile(
            name="Build & Install DBT-5 C stored functions",
            command=['make', 'install'],
            workdir='dbt5/storedproc/pgsql/c',
            env={'PATH': util.Interpolate(
                "%(prop:builddir)s/usr/bin:${PATH}")},
            haltOnFailure=True,
            )] + \
        postgres.PGINITDB + \
        postgres.PGSTART + \
        [steps.ShellCommand(
            name="Build database",
            command=[
                '/bin/sh', '-c',
                util.Interpolate(
                    "dbt5 build "
                    "-l CUSTOM "
                    f"-c {CUSTOMERS} "
                    f"-t {CUSTOMERS} "
                    "--tpcetools=%(prop:builddir)s/../egen "
                    "pgsql"
                    ),
                ],
            env={
                'APPDIR': util.Interpolate("%(prop:builddir)s"),
                'PATH': util.Interpolate("%(prop:builddir)s/usr/bin:${PATH}"),
                },
            workdir='load',
            timeout=None,
            haltOnFailure=True,
            )] + \
        [steps.ShellCommand(
            name="(hack) drop pl/pgsql functions",
            command=[
                'psql',
                '-X',
                '-d', 'dbt5',
                '-f', util.Interpolate(
                    "%(prop:builddir)s/dbt5/storedproc/pgsql/pgsql/drop_all_functions.sql"),
                ],
            env={
                'PATH': util.Interpolate("%(prop:builddir)s/usr/bin:${PATH}"),
                },
            haltOnFailure=True,
            )] + \
        [steps.ShellCommand(
            name="(hack) load pl/c functions",
            command=[
                'dbt5', 'pgsql-load-stored-procs',
                '-t', 'c',
                '-d', 'dbt5',
                '-i', '../usr/share/postgresql',
                ],
            env={
                'PATH': util.Interpolate("%(prop:builddir)s/usr/bin:${PATH}"),
                },
            haltOnFailure=True,
            )] + \
        [steps.ShellCommand(
            name="Performance test",
            doStepIf=general.IsNotForceScheduler,
            command=[
                '/bin/sh', '-c',
                util.Interpolate(
                    "dbt5 run "
                    "--stats "
                    "--tpcetools=%(prop:builddir)s/../egen "
                    f"-c {CUSTOMERS} "
                    f"-d {DURATION} "
                    f"-s {RAMPUP} "
                    f"-t {CUSTOMERS} "
                    f"-u {USERS} "
                    "pgsql %(prop:builddir)s/results"
                    ),
                ],
            timeout=None,
            env={
                'PATH': util.Interpolate("%(prop:builddir)s/usr/bin:${PATH}"),
                'PGHOST': '/tmp',
                 },
            haltOnFailure=True,
            )] + \
        [steps.ShellCommand(
            name="Performance test (force)",
            doStepIf=general.IsForceScheduler,
            command=[
                '/bin/sh', '-c',
                util.Interpolate(
                    "dbt5 run "
                    "--stats "
                    "--tpcetools=%(prop:builddir)s/../egen "
                    "-c %(prop:customers)s "
                    "-d %(prop:duration)s "
                    "-s %(prop:connection_delay)s "
                    "-t %(prop:customers)s "
                    "-u %(prop:users)s "
                    "pgsql %(prop:builddir)s/results"
                    ),
                ],
            timeout=None,
            env={
                'PATH': util.Interpolate("%(prop:builddir)s/usr/bin:${PATH}"),
                'PGHOST': '/tmp',
                 },
            haltOnFailure=True,
            )] + \
        postgres.PGSTOP + \
        [steps.ShellCommand(
            name="DBT-5 Summary",
            command=[
                'cat',
                util.Interpolate("%(prop:builddir)s/results/summary.rst"),
                ],
        )] + \
        general.STATS_SYSTEM + \
        general.STATS_OLTP
