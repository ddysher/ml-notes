FROM nginx:1.9.1

ADD certs/127.0.0.1 /etc/nginx/ssl
ADD nginx.conf /etc/nginx/conf.d/docker-registry.conf
ADD docker-registry.htpasswd /etc/nginx/conf.d/docker-registry.htpasswd
