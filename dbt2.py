"""
These are DBT-2 specific testing steps.
"""

from buildbot.plugins import steps, util

import general
import postgres

CMD = "%(prop:builddir)s/../test/dbt2.conf | tail -n 1 | cut -d '=' -f 2"

CONN_PER_PROC = f"$(( ($(grep -i ^connections {CMD}) - 1) / $(nproc) + 1 ))"
CONNECTIONS = f"$(grep -i ^connections {CMD})"
DURATION = f"$(grep -i ^duration {CMD})"
RAMPUP = f"$(( ($(grep -i ^rampup {CMD}) / {CONNECTIONS} + 1) * 1000 ))"
WAREHOUSES = f"$(grep -i ^warehouses {CMD})"

DBT2PROPERTIES = [
        util.IntParameter(
            name="warehouses",
            label="Warehouses",
            default=1,
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
            label="Seconds between opening database connections",
            default=1,
            required=True,
            ),
        util.IntParameter(
            name="connections_per_processor",
            label="Connections opened per processor",
            default=1,
            required=True,
            ),
        util.IntParameter(
            name="terminal_limit",
            label="Maximum number of database connections to open",
            default=1000,
            required=True,
            ),
        ]

DBT2STEPS = general.CLEANUP + \
        postgres.PGINSTALL + \
        [steps.Git(
            name="Clone DBT-2",
            repourl='https://github.com/osdldbt/dbt2.git',
            mode='full',
            method='fresh',
            workdir='dbt2',
            haltOnFailure=True,
            branch='main',
            alwaysUseLatest=True,
            )] + \
        [steps.Configure(
            name="Configure DBT-2",
            command=[
                'cmake',
                '-H.',
                '-Bbuilds/release',
                '-DCMAKE_INSTALL_PREFIX=/usr',
                ],
            workdir='dbt2',
            haltOnFailure=True,
            )] + \
        [steps.Compile(
            name="Build DBT-2",
            command=['make', '-f', 'Makefile.cmake', 'release'],
            workdir='dbt2',
            env={
                'PATH': util.Interpolate("%(prop:builddir)s/usr/bin:${PATH}"),
                'PGUSER': 'postgres',
                },
            haltOnFailure=True,
            )] + \
        [steps.Compile(
            name="Install DBT-2",
            command=['make', 'install'],
            workdir='dbt2/builds/release',
            env={'DESTDIR': util.Interpolate("%(prop:builddir)s")},
            haltOnFailure=True,
            )] + \
        [steps.Compile(
            name="(hack) Install DBT-2 pl/pgsql functions",
            command=[
                'sh', '-c',
                'cp -p dbt2/storedproc/pgsql/pgsql/*.sql usr/share/postgresql/',
                ],
            workdir=util.Interpolate("%(prop:builddir)s"),
            haltOnFailure=True,
            )] + \
        postgres.PGINITDB + \
        postgres.PGSTART + \
        [steps.Compile(
            name="Create database",
            command=['createdb', 'dbt2'],
            env={
                'PATH': util.Interpolate("%(prop:builddir)s/usr/bin:${PATH}"),
                },
            haltOnFailure=True,
            )] + \
        [steps.ShellCommand(
            name="Build database",
            doStepIf=general.IsNotForceScheduler,
            command=[
                '/bin/sh', '-c',
                util.Interpolate(f"dbt2 build -w {WAREHOUSES} pgsql"),
                ],
            env={
                'APPDIR': util.Interpolate("%(prop:builddir)s"),
                'PATH': util.Interpolate("%(prop:builddir)s/usr/bin:${PATH}"),
                'PGDATABASE': 'postgres',
                },
            timeout=None,
            haltOnFailure=True,
            )] + \
        [steps.ShellCommand(
            name="Build database (force)",
            doStepIf=general.IsForceScheduler,
            command=[
                '/bin/sh', '-c',
                util.Interpolate("dbt2 build -w %(prop:warehouses)s pgsql"),
                ],
            env={
                'APPDIR': util.Interpolate("%(prop:builddir)s"),
                'PATH': util.Interpolate("%(prop:builddir)s/usr/bin:${PATH}"),
                'PGDATABASE': 'postgres',
                },
            timeout=None,
            haltOnFailure=True,
            )] + \
        [steps.ShellCommand(
            name="Performance test",
            doStepIf=general.IsNotForceScheduler,
            command=[
                '/bin/sh', '-c',
                util.Interpolate(
                    f"dbt2 run --stats "
                    f"--connection-delay {RAMPUP} "
                    f"--connections-per-processor {CONN_PER_PROC} "
                    f"--duration {DURATION} "
                    f"--terminal-limit {CONNECTIONS} "
                    f"--warehouses {WAREHOUSES} "
                    "pgsql %(prop:builddir)s/results"
                    ),
                ],
            env={
                'PATH': util.Interpolate("%(prop:builddir)s/usr/bin:${PATH}"),
                'PGHOST': '/tmp',
                },
            timeout=None,
            haltOnFailure=True,
            )] + \
        [steps.ShellCommand(
            name="Performance test (force)",
            doStepIf=general.IsForceScheduler,
            command=[
                '/bin/sh', '-c',
                util.Interpolate(
                    "dbt2 run --stats "
                    "--connection-delay %(prop:connection_delay)s "
                    "--connections-per-processor %(prop:connections_per_processor)s "
                    "--duration %(prop:duration)s "
                    "--terminal-limit %(prop:terminal_limit)s "
                    "--warehouses %(prop:warehouses)s "
                    "pgsql %(prop:builddir)s/results"
                    ),
                ],
            env={
                'PATH': util.Interpolate("%(prop:builddir)s/usr/bin:${PATH}"),
                'PGHOST': '/tmp',
                },
            timeout=None,
            haltOnFailure=True,
            )] + \
        postgres.PGSTOP + \
        [steps.ShellCommand(
            name="DBT-2 Summary",
            command=[
                'cat',
                util.Interpolate("%(prop:builddir)s/results/summary.rst"),
                ],
        )] + \
        general.STATS_SYSTEM + \
        general.STATS_OLTP
