#!/bin/bash
#
# Simple build script for a microservices banking project.
#
# Author: Christian Otterstad
#

DOCKER_COMPOSE_FILE="docker-compose.yml"
DOCKER_COMPOSE_FILE_SANITY="docker-compose.yml_"
SOURCE_DIR="common_files"
EXCLUSION_LIST=($SOURCE_DIR lb)
BUILD_FULL=1
DELETE=0
REBUILD=0
RESTART=0

DOCKER_DEL_VOLUMES="docker volume ls | cut -d ' ' -f 16 | xargs docker volume rm"

function arg_parse {
	usage="$(basename "$0") [-h] [-c (only copy common files, no build)] [-d (Delete all docker files prior to building)] [-b (Disables building)]"

	while getopts 'hcdbrvuf' option; do
		case "$option" in
			h) echo "$usage"
			   exit
			   ;;
			c) echo "Only coping common files."
			   BUILD_FULL=0
			   ;;
			d) echo "Deleting Docker images."
			   DELETE=1
			   ;;
			f) echo "File clean up."
			   clean_files
			   exit 0
			   ;;
			v) echo "Deleting Docker volumes."
			   delete_volumes
			   exit 0
			   ;;
			b) echo "Disabled build."
			   BUILD_FULL=0
			   ;;
			r) echo "Rebuild only."
			   REBUILD=1
			   ;;
			u) echo "Restart service only."
			   RESTART=1
			   ;;
			\?) echo "Invalid option: -$OPTARG" >&2
			   exit 1
			   ;;
		esac
	done
}

function copy_commons {
	for i in *
	do
		if [[ -d $i ]]; then
			EX_MATCH=0
			for j in ${EXCLUSION_LIST[*]}
			do
				if [[ $i == $j ]]; then
					EX_MATCH=1
					break
				fi
			done

			if [[ -d $i/$i ]]; then
				if [[ $i != $SOURCE_DIR ]]; then
					cp -R $SOURCE_DIR/MiSSFire/* $i/$i
					cp -R $SOURCE_DIR/general/* $i/$i
				fi
			fi
		fi
	done

	return 0
}

function delete_volumes {
	echo "Removing all volumes and containers."

	docker stop $(docker ps -a -q) > /dev/null 2>&1
	docker rm $(docker ps -a -q) > /dev/null 2>&1

	eval $DOCKER_DEL_VOLUMES

	echo "OK"
}

function delete_docker_files {	
	delete_volumes

	echo "Stopping all docker containers."

	docker stop $(docker ps -a -q) > /dev/null 2>&1

	echo "OK"

	echo "Deleting all containers."

	docker rm $(docker ps -a -q) > /dev/null 2>&1

	echo "OK"

	echo "Deleting all images."

	docker rmi $(docker images -q) > /dev/null 2>&1

	echo "OK"

	echo "Done removing."
}

function clean_files {
	find . \( -name "*.pyc" -o -name "*.key" -o -name "*.csr" -o -name "*.crt" -o -name "*.pem" -o -name "*.old" -o -name "*.attr" -o -name "index.txt" -o -name "serial.txt" \) -type f -print0 | xargs -0 /bin/rm -f
}

function save_compose_file {
	if [ -f $DOCKER_COMPOSE_FILE ]; then
		mv $DOCKER_COMPOSE_FILE $DOCKER_COMPOSE_FILE_SANITY
	fi
}

function restore_compose_file {
	mv $DOCKER_COMPOSE_FILE_SANITY $DOCKER_COMPOSE_FILE
}

save_compose_file

arg_parse "$@"

echo "Copying common files into all services ..."

if [ $RESTART -eq 1 ]; then
	restore_compose_file

	echo "Stopping $2 ..."

	if ! docker-compose stop $2; then
		echo "Error: Error when stopping $2."

		save_compose_file

		exit 1
	fi

	echo "Stopped."

	if ! docker-compose up $2; then
		echo "Error: Error when restarting $2."

		save_compose_file

		exit 1
	fi

	save_compose_file

	exit 0
fi

copy_commons

if [ $REBUILD -eq 1 ]; then
	clean_files
	restore_compose_file

	echo "Stopping $2 ..."

	if ! docker-compose stop $2; then
		echo "Error: Error when stopping $2."

		save_compose_file

		exit 1
	fi

	echo "Stopped."

	if ! docker-compose build $2; then
		echo "Error: Error when building $2."

		save_compose_file

		exit 1
	fi

	echo "Built."

	save_compose_file
fi

if [ $DELETE -eq 1 ]; then
	delete_docker_files	
fi

if [ $BUILD_FULL -eq 1 ]; then
	echo "Now building everything ..."
	clean_files

	restore_compose_file

	docker-compose up

	save_compose_file
fi

echo "Done!"
