"""
These are DBT-2 specific testing steps.
"""

from buildbot.plugins import steps, util

import general
import postgres

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
            command=[
                'dbt2', 'build',
                '-w', '1',
                'pgsql',
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
            command=[
                'dbt2', 'run',
                '--stats',
                '-w', '1',
                '-d', '60',
                'pgsql',
                util.Interpolate("%(prop:builddir)s/results"),
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
