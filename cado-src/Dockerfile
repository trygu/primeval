FROM registry.gitlab.inria.fr/cado-nfs/cado-nfs/factoring-full:latest

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

VOLUME ["/work"]

ENTRYPOINT ["/bin/bash", "/entrypoint.sh"]
