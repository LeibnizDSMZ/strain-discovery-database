FROM docker.io/mongodb/mongodb-community-server:8.0-ubuntu2204

ARG USER_GID=1001
ARG INIT_MONGO_CONFIG=/etc/mongod.conf
ENV INIT_MONGO_CONFIG=${INIT_MONGO_CONFIG}
USER root

COPY ./bin/db/mongo_init.sh /docker-entrypoint-initdb.d/mongo_db.sh
COPY ./bin/db/mongo_entry.sh /entry.sh
COPY ./configs/db/mongo.conf ${INIT_MONGO_CONFIG}

RUN groupmod --gid ${USER_GID} mongodb
RUN apt-get install -y bash \
    && chown mongodb:mongodb ${INIT_MONGO_CONFIG} \
    && mkdir /socket && chown mongodb:mongodb /socket \
    && mkdir -p /var/log/mongodb && chown mongodb:mongodb /var/log/mongodb

USER mongodb
ENTRYPOINT [ "/bin/bash", "/entry.sh" ]
