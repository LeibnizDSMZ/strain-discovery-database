# SPDX-FileCopyrightText: 2026 Leibniz Institute DSMZ-German Collection of Microorganisms and Cell Cultures GmbH
#
# SPDX-License-Identifier: MIT

FROM docker.io/almalinux:10 AS appbuilder

ARG BIN_DEPLOY_PREP
ARG BIN_DEPLOY_REQ
ARG CONTAINER="container"
ARG NODE_VERSION

COPY . /tmp/app

WORKDIR /tmp/app

RUN dnf clean all && dnf install -y bash
RUN bash "./${BIN_DEPLOY_PREP}" && bash "./${BIN_DEPLOY_REQ}"
RUN make build

RUN --mount=type=secret,id=env_file,target=/run/secrets/env_file \
    bash -c "\
        while IFS='=' read -r key value; do \
            if [[ ! \${key} =~ ^# && -n \${key} ]]; then \
                export \${key}=\${value}; \
            fi; \
        done < /run/secrets/env_file && make runBuild \
    "

FROM docker.io/almalinux:10 AS main

ARG USERNAME=runner
ARG USER_UID=1001
ARG USER_GID=1001
ARG HOME_MAIN="/home/runner"
ARG BIN_DEPLOY_ENTRY_PROD
ARG BIN_DEPLOY_HEALTH
ARG BIN_EVALUATE_LOG
ARG NODE_VERSION

RUN dnf clean all && dnf install -y bash

ARG BIN_DEPLOY_PREP
ARG BIN_DEPLOY_REQ
ARG BIN_DEPLOY_USER

COPY ./${BIN_DEPLOY_PREP} /prep.sh
COPY ./${BIN_DEPLOY_REQ} /req.sh
COPY ./${BIN_DEPLOY_USER} /user.sh

COPY --from=appbuilder /tmp/app/dist /tmp/build
COPY ./${BIN_DEPLOY_ENTRY_PROD} /entry.sh
COPY ./${BIN_DEPLOY_HEALTH} /health.sh
COPY ./${BIN_EVALUATE_LOG} /evaluate_log.sh

WORKDIR /tmp/build
RUN bash /prep.sh && rm /prep.sh
RUN bash /req.sh && rm /req.sh
RUN bash /user.sh && rm /user.sh

RUN mkdir -p /data/cache && mkdir -p /data/output && \
    chown ${USERNAME}:${USERNAME} -R /data/

HEALTHCHECK --interval=5m --timeout=3s CMD /health.sh

RUN chown ${USERNAME}:${USERNAME} -R /tmp/build

USER ${USERNAME}

RUN pip install --no-cache-dir *.whl

WORKDIR ${HOME_MAIN}

RUN rm -rf  /tmp/build

ENV PATH="${HOME_MAIN}/.local/bin:${PATH}"

ENTRYPOINT ["/bin/sh", "/entry.sh"]
