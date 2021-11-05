
FROM  python:3.9

ENV PATH="/scripts:${PATH}"

COPY ./requirements.txt /requirements.txt
RUN pip3 install -r /requirements.txt


RUN mkdir /app
COPY ./src /app
WORKDIR /app
COPY ./scripts /scripts

RUN chmod +x /scripts/*

RUN mkdir -p /vol/web/media
RUN mkdir -p /vol/web/

RUN adduser user
RUN chown -R user:user /vol
RUN chmod -R 755 /vol/web
USER user

CMD ["entrypoint.sh"]
