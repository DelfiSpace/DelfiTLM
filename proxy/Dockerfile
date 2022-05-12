# this image runs an nginx proxy
FROM nginxinc/nginx-unprivileged:1-alpine

# retrieve the current user ID
RUN UID=`whoami`

# switch to root
USER root

COPY ./http.conf /http.conf
COPY ./https.conf /https.conf
COPY ./uwsgi_params /etc/nginx/uwsgi_params
COPY ./entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# create a folder for the certificates
RUN mkdir /certs

# create a folder to service Django static content
RUN mkdir -p /vol/static
RUN chmod 755 /vol/static

# expose also the HTTPS port
EXPOSE 8443

# switch back to the unprivileged user
USER $UID

# run the entry point script to select the nginx configuration
CMD ["/bin/sh", "-c", "/entrypoint.sh"]
