"""
These are DBT-7 specific testing steps.
"""

from buildbot.plugins import steps, util

import general
import postgres

CMD = "%(prop:builddir)s/../test/dbt7.conf | tail -n 1 | cut -d '=' -f 2"

SCALE = f"$(grep -i ^scale_factor {CMD})"

DBT7PROPERTIES = [
        util.IntParameter(
            name="scale",
            label="Scale Factor",
            default=1,
            required=True,
            ),
        ] + \
        general.PROPERTIES

DBT7STEPS = general.CLEANUP + \
        [steps.RemoveDirectory(
            name="Remove previous dsgen files",
            dir=util.Interpolate("%(prop:builddir)s/load"),
            )] + \
        postgres.PGINSTALL + \
        [steps.Compile(
            name="Install auto_explain extension",
            command=['make', 'install'],
            workdir='build/contrib/auto_explain',
            haltOnFailure=True,
            )] + \
        [steps.Git(
            name="Clone DBT-7",
            repourl='https://github.com/osdldbt/dbt7.git',
            mode='full',
            method='fresh',
            workdir='dbt7',
            branch='main',
            alwaysUseLatest=True,
            haltOnFailure=True,
            )] + \
        [steps.Configure(
            name="Configure DBT-7",
            command=[
                'cmake',
                '-H.',
                '-Bbuilds/release',
                '-DCMAKE_INSTALL_PREFIX=/usr',
                ],
            workdir='dbt7',
            haltOnFailure=True,
            )] + \
        [steps.Compile(
            name="Build DBT-7",
            command=['make', '-f', 'Makefile.cmake', 'release'],
            workdir='dbt7',
            env={
                'PATH': util.Interpolate("%(prop:builddir)s/usr/bin:${PATH}"),
                },
            haltOnFailure=True,
            )] + \
        [steps.Compile(
            name="Install DBT-7",
            command=['make', 'install'],
            workdir='dbt7/builds/release',
            env={'DESTDIR': util.Interpolate("%(prop:builddir)s")},
            haltOnFailure=True,
            )] + \
        postgres.PGINITDB + \
        postgres.PGSTART + \
        [steps.Compile(
            name="Create database",
            command=['createdb', 'dbt7'],
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
                    "dbt7 run "
                    "-d postgresqlea "
                    "--stats "
                    "--tpcdstools=%(prop:builddir)s/../dsgen "
                    f"-s {SCALE} "
                    "pgsql %(prop:builddir)s/results"
                    ),
                ],
            timeout=None,
            env={
                'PATH': util.Interpolate("%(prop:builddir)s/usr/bin:${PATH}"),
                'PGHOST': '/tmp',
                },
            )] + \
        [steps.ShellCommand(
            name="Performance test (force)",
            doStepIf=general.IsForceScheduler,
            command=[
                '/bin/sh', '-c',
                util.Interpolate(
                    "dbt7 run "
                    "-d postgresqlea "
                    "--stats "
                    "--tpcdstools=%(prop:builddir)s/../dsgen "
                    "-s %(prop:scale)s "
                    "pgsql %(prop:builddir)s/results"
                    ),
                ],
            timeout=None,
            env={
                'PATH': util.Interpolate("%(prop:builddir)s/usr/bin:${PATH}"),
                'PGHOST': '/tmp',
                },
            )] + \
        postgres.PGSTOP + \
        [steps.ShellCommand(
            name="DBT-7 Summary",
            command=[
                'cat',
                util.Interpolate("%(prop:builddir)s/results/summary.rst"),
                ],
            )] + \
        [steps.ShellCommand(
            name="Power Test Results",
            command=['cat', "results_0.txt"],
            workdir='results/power',
            alwaysRun=True,
           )] + \
        general.STATS_SYSTEM + \
        general.STATS_DSS
