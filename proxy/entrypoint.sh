#!/bin/sh

# default location for the certificate files
CERTIFICATE=/certs/server.pem
KEY=/certs/server.key

# this is used to resolve the $host strings in the nginx conf file
export DOLLAR='$'

# check if the certificates exist
if [ -f "$CERTIFICATE" ] && [ -f "$KEY" ];
then
    echo "Certificates found... using HTTPS configuration"

    # replace environment variables in the nginx configuration file
    envsubst < /https.conf > /etc/nginx/conf.d/default.conf
else
    echo "Certificates not found... using HTTP configuration"

    # replace environment variables in the nginx configuration file
    envsubst < /http.conf > /etc/nginx/conf.d/default.conf
fi

# start nginx
exec nginx -g 'daemon off;'