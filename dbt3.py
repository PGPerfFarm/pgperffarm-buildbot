"""
These are DBT-3 specific testing steps.
"""

from buildbot.plugins import steps, util

import general
import postgres

CMD = "%(prop:builddir)s/../test/dbt3.conf | tail -n 1 | cut -d '=' -f 2"

SCALE = f"$(grep -i ^scale_factor {CMD})"

DBT3PROPERTIES = [
        util.IntParameter(
            name="scale",
            label="Scale Factor",
            default=1,
            required=True,
            ),
        ]

DBT3STEPS = general.CLEANUP + \
        [steps.RemoveDirectory(
            name="Remove previous dbgen files",
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
            name="Clone DBT-3",
            repourl='https://github.com/osdldbt/dbt3.git',
            mode='full',
            method='fresh',
            workdir='dbt3',
            branch='main',
            alwaysUseLatest=True,
            haltOnFailure=True,
            )] + \
        [steps.Configure(
            name="Configure DBT-3",
            command=[
                'cmake',
                '-H.',
                '-Bbuilds/release',
                '-DCMAKE_INSTALL_PREFIX=/usr',
                ],
            workdir='dbt3',
            haltOnFailure=True,
            )] + \
        [steps.Compile(
            name="Build DBT-3",
            command=['make', '-f', 'Makefile.cmake', 'release'],
            workdir='dbt3',
            env={
                'PATH': util.Interpolate("%(prop:builddir)s/usr/bin:${PATH}"),
                },
            haltOnFailure=True,
            )] + \
        [steps.Compile(
            name="Install DBT-3",
            command=['make', 'install'],
            workdir='dbt3/builds/release',
            env={'DESTDIR': util.Interpolate("%(prop:builddir)s")},
            haltOnFailure=True,
            )] + \
        postgres.PGINITDB + \
        postgres.PGSTART + \
        [steps.Compile(
            name="Create database",
            command=['createdb', 'dbt3'],
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
                    "dbt3 run "
                    "--dss=%(prop:builddir)s/dss "
                    "--explain "
                    "--relax "
                    f"--scale-factor {SCALE} "
                    "--stats "
                    "--tpchtools=%(prop:builddir)s/../dbgen "
                    "pgsql %(prop:builddir)s/results"
                    )
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
                    "dbt3 run "
                    "--dss=%(prop:builddir)s/dss "
                    "--explain "
                    "--relax "
                    "--scale-factor %(prop:scale)s "
                    "--stats "
                    "--tpchtools=%(prop:builddir)s/../dbgen "
                    "pgsql %(prop:builddir)s/results"
                    )
                ],
            timeout=None,
            env={
                'PATH': util.Interpolate("%(prop:builddir)s/usr/bin:${PATH}"),
                'PGHOST': '/tmp',
                },
            )] + \
        postgres.PGSTOP + \
        [steps.ShellCommand(
            name="DBT-3 Metrics",
            command=[
                'cat',
                util.Interpolate("%(prop:builddir)s/results/score.txt"),
                ],
        )] + \
        [steps.ShellCommand(
            name="DBT-3 Summary",
            command=[
                'cat',
                util.Interpolate("%(prop:builddir)s/results/summary.rst"),
                ],
        )] + \
        general.STATS_SYSTEM + \
        general.STATS_DSS

for i in range(1, 22):
    DBT3STEPS.append(
            steps.ShellCommand(
                name=f"Power Query {i}",
                command=['cat', f"{i}.txt"],
                workdir='results/power/results',
                alwaysRun=True,
                )
            )

for i in [1, 2]:
    DBT3STEPS.append(
            steps.ShellCommand(
                name=f"Power Refresh Stream {i}",
                command=['cat', f"rf{i}.txt"],
                workdir='results/power/results',
                alwaysRun=True,
                )
            )
