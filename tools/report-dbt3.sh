#!/bin/sh

BUILDBOTURL="http://147.75.56.225:8010"
CSVEXPORT="export-dbt3.csv"
CSVREPORT="report-dbt3.csv"
CSVSORTED="sorted-dbt3.csv"
PGGITDIR="/usr/local/src/postgres"
PLOTSIZE="1600,1000"

psql -X -d perffarm -o "${CSVEXPORT}" << __SQL__
COPY (
    SELECT workers.name AS plant
         , btrim(branch.value, '"') AS branch
         , btrim(revision.value, '"') AS revision
         , scale.value AS scale
         , logs.id AS logs_id
    FROM builders
       , builds
       , workers
       , build_properties AS branch
       , build_properties AS revision
       , build_properties AS scale
       , steps
       , logs
    WHERE builderid = builders.id
      AND workerid = workers.id
      AND steps.buildid = builds.id
      AND stepid = steps.id
      AND branch.buildid = builds.id
      AND revision.buildid = builds.id
      AND scale.buildid = builds.id
      AND builders.name = 'dbt3'
      AND builds.results = 0
      AND branch.name = 'branch'
      AND revision.name = 'revision'
      AND scale.name = 'scale'
      AND steps.name = 'DBT-3 Metrics'
)
TO STDOUT
(FORMAT csv, HEADER TRUE, DELIMITER ' ');
__SQL__

HEADER="$(head -n 1 "${CSVEXPORT}") ctime metric load power throughput"

echo "${HEADER}" > "${CSVREPORT}"
tail -n +2 "${CSVEXPORT}" | while IFS= read -r LINE; do
	COMMIT="$(echo "${LINE}" | cut -d " " -f 3)"
	LOGSID="$(echo "${LINE}" | cut -d " " -f 5)"

	CTIME="$(cd "${PGGITDIR}" && git show -s --format="%ct" "${COMMIT}")"

	METRICS="$(curl --silent \
			"${BUILDBOTURL}/api/v2/logs/${LOGSID}/raw_inline")"

	SCORE="$(echo "${METRICS}" | \
			sed -n \
			's/.*Composite Score:[ ]\+\([0-9]\+\(\.[0-9]\+\)\?\).*/\1/p')"

	LOAD="$(echo "${METRICS}" | \
			sed -n \
			's/.*Load Test Time (hours):[ ]*\([0-9.]\+\).*/\1/p')"

	POWER="$(echo "${METRICS}" | \
			sed -n \
			's/.*Power Test Score:[ ]\+\([0-9]\+\(\.[0-9]\+\)\?\).*/\1/p')"

	THROUGHPUT="$(echo "${METRICS}" | \
			sed -n \
			's/.*Throughput Test Score:[ ]\+\([0-9]\+\(\.[0-9]\+\)\?\).*/\1/p')"

	echo "${LINE} ${CTIME} ${SCORE} ${LOAD} ${POWER} ${THROUGHPUT}" >> \
			"${CSVREPORT}"
done

tail -n +2 "${CSVREPORT}" | sort -t " " -k 6 -n > "${CSVSORTED}"

BRANCHES="$(tail -n +2 "${CSVEXPORT}" | cut -d " " -f 2 | sort -u | xargs)"
PLANTS="$(tail -n +2 "${CSVEXPORT}" | cut -d " " -f 1 | sort -u | xargs)"

for PLANT in ${PLANTS}; do
	COUNT=0
	PLOTLIST=""
	PLOTLISTLOAD=""
	PLOTLISTPOWER=""
	PLOTLISTTHROUGHPUT=""
	TMPFILELIST=""
	for BRANCH in ${BRANCHES}; do
		COUNT=$(( COUNT + 1 ))
		TMPFILE="$(mktemp)"
		TMPFILELIST="${TMPFILELIST} ${TMPFILE}"

		if [ ${COUNT} -gt 1 ]; then
			PLOTLIST="${PLOTLIST},"
			PLOTLISTLOAD="${PLOTLISTLOAD},"
			PLOTLISTPOWER="${PLOTLISTPOWER},"
			PLOTLISTTHROUGHPUT="${PLOTLISTTHROUGHPUT},"
		fi
		PLOTLIST="${PLOTLIST}'${TMPFILE}' using 'ctime':'metric' title '${BRANCH}' noenhanced with linespoints"
		PLOTLISTLOAD="${PLOTLISTLOAD}'${TMPFILE}' using 'ctime':'load' title '${BRANCH}' noenhanced with linespoints"
		PLOTLISTPOWER="${PLOTLISTPOWER}'${TMPFILE}' using 'ctime':'power' title '${BRANCH}' noenhanced with linespoints"
		PLOTLISTTHROUGHPUT="${PLOTLISTTHROUGHPUT}'${TMPFILE}' using 'ctime':'throughput' title '${BRANCH}' noenhanced with linespoints"

		echo "${HEADER}" > "${TMPFILE}"
		awk -F " " "\$2 == \"${BRANCH}\"" "${CSVSORTED}" >> "${TMPFILE}"
	done

	plot()
	{
		NAME="${1}"
		TITLE="${2}"
		LABEL="${3}"
		LINES="${4}"

		gnuplot <<- __PLOT__
			set xdata time
			set timefmt "%s"
			set terminal pngcairo size ${PLOTSIZE}
			set xlabel "Time"
			set xtics rotate
			set xtics format "%Y-%m-%d"
			set grid
			set title "DBT-3 ${TITLE}Results ${PLANT}" noenhanced
			set output 'dbt3-${PLANT}${NAME}.png'
			set ylabel "${LABEL}"
			set yrange [0:*]
			set key below
			plot ${LINES}
		__PLOT__
	}

	plot "" "" "Composite Score" "${PLOTLIST}"
	plot "-load" "Load " "Hours" "${PLOTLISTLOAD}"
	plot "-power" "Power " "Power Score" "${PLOTLISTPOWER}"
	plot "-throughput" "Throughput " "Throughput Score" "${PLOTLISTTHROUGHPUT}"

	rm "${TMPFILELIST}"
done
