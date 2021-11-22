# this image runs an nginx proxy
FROM nginxinc/nginx-unprivileged:1-alpine

COPY ./default.conf /etc/nginx/conf.d/default.conf
COPY ./uwsgi_params /etc/nginx/uwsgi_params

# change user to root to add static files directory
USER root

RUN mkdir -p /vol/static
RUN chmod 755 /vol/static

# switch back to unprivileged user
USER nginx
