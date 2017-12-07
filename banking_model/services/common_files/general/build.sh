#!/bin/bash

echo "Applying security configurations."
#export MTLS="True"
if [ "$MTLS" == "True" ]; then
   python MiSSFire.py
fi

echo "Starting Gunicorn."
gunicorn -c gunicorn_config.py api:app

echo "Done!"
