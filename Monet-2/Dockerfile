FROM gitlab-registry.cern.ch/lhcb/monet/monet-base:alma9-root-dirac
ARG CI_JOB_TOKEN
ARG HISTOYML_USER_TOKEN

RUN touch /usr/local/bin/elog && chmod 755 /usr/local/bin/elog
RUN mkdir /cache

WORKDIR /

RUN git clone https://monet:${HISTOYML_USER_TOKEN}@gitlab.cern.ch/lhcb/histoyml.git
RUN git clone https://gitlab.cern.ch/lhcb-simulation/simdqdata.git simproddb

WORKDIR /app
COPY . .

RUN pip install git+https://gitlab-ci-token:${CI_JOB_TOKEN}@gitlab.cern.ch/lhcb-monitoring/MonitoringHubClient.git
RUN ulimit -n 2048
RUN chmod 755 /app/presenter_entrypoint.sh

ENV MONET_CONFIG=/app/configs/monet.cfg
ENV X509_VOMSES=/app/diracos/etc/grid-security/vomses

VOLUME /hist
EXPOSE 8123
ENTRYPOINT [ "/app/presenter_entrypoint.sh" ]
