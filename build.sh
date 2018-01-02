#!/bin/bash

MISSFIRE_SERVICES="services"
BANK_SERVICES="MicroBank/services"

MISSFIRE_COMMONS="MiSSFire_client_commons"
BANK_COMMONS="$BANK_SERVICES/common_files"

MISSFIRE_CLIENT_DOCKER_IMAGE="docker_image_template/MiSSFire_client"
MISSFIRE_SERVICES_DOCKER_IMAGE="docker_image_template/MiSSFire_services"

DOCKER_YML="docker-compose.yml_"
DOCKER_YML_ORIGINAL="docker-compose.yml_original"

function arg_parse {
	usage="$(basename "$0") [-h] [-c (Copy MiSSFire files into the bank model)] [-d (Delete MiSSFire files from the bank model)] [-i (Build the necessary Docker images)]"

	while getopts 'hcd' option; do
		case "$option" in
			h) echo "$usage"
			   exit
			   ;;
			c) echo "Copy files."
			   copy_commons
			   exit 0
			   ;;
			d) echo "Delete files."
			   delete_commons
			   exit 0
			   ;;
			i) echo "Building Docker images."
			   build_docker_images
			   exit 0
			   ;;
			\?) echo "Invalid option: -$OPTARG" >&2
			   exit 1
			   ;;
		esac
	done
}


function copy_commons {
	echo "Copying MiSSFire services into the bank model."
	if [[(-d $MISSFIRE_SERVICES) && (-d $BANK_SERVICES)]]; then
		cp -R $MISSFIRE_SERVICES/* $BANK_SERVICES
	else
		echo Missing '$MISSFIRE_SERVICES' or '$BANK_SERVICES'.
	fi

	echo "Copying MiSSFire client commons into the bank model commons."
	if [[(-d $MISSFIRE_COMMONS) && (-d $BANK_COMMONS)]]; then
		cp -R $MISSFIRE_COMMONS $BANK_COMMONS
	else
		echo Missing '$MISSFIRE_COMMONS' or '$BANK_COMMONS'.
	fi

	echo "Copying a new docker compose config file."
	if [[(-f $DOCKER_YML) && (-f $BANK_SERVICES/$DOCKER_YML)]]; then
		mv $BANK_SERVICES/$DOCKER_YML $BANK_SERVICES/$DOCKER_YML_ORIGINAL
		cp $DOCKER_YML $BANK_SERVICES
	else
		echo Missing '$DOCKER_YML_ORIGINAL' or '$BANK_SERVICES/$DOCKER_YML_ORIGINAL'.
	fi

	return 0
}


function delete_commons {
	echo "Removing MiSSFire services from the bank model."
	for f in $MISSFIRE_SERVICES/*; do
		bf=$(basename "$f")
		if [[ -d $BANK_SERVICES/$bf ]]; then
			rm -r $BANK_SERVICES/$bf
		fi
	done

	echo "Removing MiSSFire client commons from the bank model commons."
	bf=$(basename "$MISSFIRE_COMMONS")
	if [[ -d $BANK_COMMONS/$bf ]]; then
		rm -r $BANK_COMMONS/$bf
	fi

	echo "Restoring an original docker compose config file."
	if [[ -f $BANK_SERVICES/$DOCKER_YML_ORIGINAL ]]; then
		mv $BANK_SERVICES/$DOCKER_YML_ORIGINAL $BANK_SERVICES/$DOCKER_YML
	else
		echo Missing '$BANK_SERVICES/$DOCKER_YML_ORIGINAL'.
	fi

	echo "Removing trash files."
	find . \( -name "*.pyc" -o -name "*.key" -o -name "*.csr" -o -name "*.crt" -o -name "*.pem" -o -name "*.old" -o -name "*.attr" -o -name "index.txt" -o -name "serial.txt" -o -name "logging.conf" \) -type f -print0 | xargs -0 /bin/rm -f

	return 0
}


function build_docker_images {
	echo "Building Docker image: 'bankmodeldefault'."
	docker build -t bankmodeldefault $MISSFIRE_CLIENT_DOCKER_IMAGE/Dockerfile

	echo "Building Docker image: 'missfire'."
	docker build -t missfire $MISSFIRE_SERVICES_DOCKER_IMAGE/Dockerfile
	
	return 0
}

arg_parse "$@"



