FROM lyft/envoy:1.3.0
# FROM dwflynn/envoy-debug:20170501

RUN apt-get update && apt-get -q install -y \
    curl \
    dnsutils

COPY envoy.json /etc/envoy.json
CMD /usr/local/bin/envoy -c /etc/envoy.json
