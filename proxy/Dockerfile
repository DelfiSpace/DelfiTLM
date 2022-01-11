# this image runs an nginx proxy
FROM nginxinc/nginx-unprivileged:1-alpine

# retrieve the current user ID
RUN UID=`whoami`

# switch to root
USER root

COPY ./http.conf /http.conf
COPY ./https.conf.template /default.conf.template
COPY ./uwsgi_params /etc/nginx/uwsgi_params
COPY ./entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# create a folder for the certificates
RUN mkdir /certs

# expose also the HTTPS port
EXPOSE 8443

# switch back to the unprivileged user
USER $UID

# run the entry point script to select the nginx configuration
CMD ["/bin/sh", "-c", "/entrypoint.sh"]