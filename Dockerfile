FROM  ubuntu:24.04
FROM  python:3.12

ENV PATH="/scripts:${PATH}"

# Always flush output directly
ENV PYTHONBUFFERED=1

# Install Java
RUN echo "deb https://deb.debian.org/debian/ bullseye main" >> /etc/apt/sources.list && \
    apt-get update && \
    apt install -y --no-install-recommends openjdk-11-jre-headless && \
    apt-get clean;

# install dependencies
COPY ./requirements.txt /requirements.txt

RUN pip3 install -r /requirements.txt

# add the code to the docker image
RUN mkdir /app
COPY ./src /app
WORKDIR /app
COPY ./scripts /scripts

# add executable permission to the scripts folder
# scripts will run a uwsgi service that will host the app
RUN chmod +x /scripts/*

# add directories for static
RUN mkdir -p /vol/web/media
RUN mkdir -p /vol/web/static

# create a new user in the docker image to run the server, not as root
RUN adduser user
RUN chown -R user:user /vol
RUN chmod -R 755 /vol/web

RUN mkdir /var/log/django
RUN chown -R user:user /app
RUN chmod -R 755 /var/log/django
RUN chown -R user:user /var/log/django

RUN chown -R user:user /app/home/temp
RUN chmod -R 755 /app/home/temp

# download the solar system latest ephemeris from JPL SSD  ftp server
ADD https://ssd.jpl.nasa.gov/ftp/eph/planets/bsp/de421.bsp /app/de421.bsp
RUN chown user:user /app/de421.bsp
RUN chmod -R 744 /app/de421.bsp

# switch to unprivileged user
USER user

# run the startup script
CMD ["entrypoint.sh"]
