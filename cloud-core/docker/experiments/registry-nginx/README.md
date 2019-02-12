#### Running an unsecure registry behind nginx on localhost (ubuntu)
* Clone [easyrsa](https://github.com/OpenVPN/easy-rsa) to generate certificates
```
  git clone https://github.com/OpenVPN/easy-rsa.git
```
* In easyrsa3 folder, run
```
  ./easyrsa init-pki
```
* Generate CA. The output will be pki/ca.crt and pki/private/ca.key. Put whatever Common Name you like for CA - it doesn't matter since it won't be trusted anyway :)
```
  ./easyrsa build-ca nopass
```
* Then generate certificates. The output will be pki/issued/127.0.0.1.crt and pki/private/127.0.0.1.key
```
  ./easyrsa build-server-full 127.0.0.1 nopass
```
* Copy generated ca under `./certs`, and server certs under `./certs/127.0.0.1/`
* In nginx.conf, 'ssl_certificates' and 'ssl_certificates_key' sections need to point to the right ones
```
  ssl_certificate /etc/nginx/ssl/127.0.0.1.crt;
  ssl_certificate_key /etc/nginx/ssl/127.0.0.1.key;
```
* Use htpasswd to create a password file (admin:admin)
```
  htpasswd -c docker-registry.htpasswd admin
```
* Create $(pwd)/data and run an insecure registry
```
  docker run -v $(pwd)/data:/tmp/registry-dev --name raw-registry registry:2.0
```
* Run nginx reverse proxy
```
  docker run -p 4433:443 -v $(pwd)/certs/127.0.0.1:/etc/nginx/ssl -v $(pwd)/docker-registry.htpasswd:/etc/nginx/conf.d/docker-registry.htpasswd -v $(pwd)/nginx.conf:/etc/nginx/conf.d/docker-registry.conf --link raw-registry:raw-registry nginx
```
Or
```
  docker build -t ddysher/registry-nginx .
  docker run -p 4433:443 --link raw-registry:raw-registry ddysher/registry-nginx
```
* Then login
```
  docker login localhost:433
```
* Now we can do normal push/pull, e.g:
```
  docker push localhost:433/hello-world
```

#### Running an unsecure registry behind nginx on remote server (ubuntu)
* Generate certificates for remote server, using the same CA as above. Here, we use deyuan.me as domain and its ip address 104.131.232.95
```
  ./easyrsa --subject-alt-name=IP:104.131.232.95 build-server-full deyuan.me nopass
```
* Copy generated server certs under `./certs/deyuan.me/`
* In nginx.conf, 'ssl_certificates' and 'ssl_certificates_key' sections need to point to the right ones
```
  ssl_certificate /etc/nginx/ssl/deyuan.me.crt;
  ssl_certificate_key /etc/nginx/ssl/deyuan.me.key;
```
* Create $(pwd)/data and run an insecure registry
```
  docker run -v $(pwd)/data:/tmp/registry-dev --name raw-registry registry:2.0
```
* Run nginx reverse proxy on remote server
```
  docker run -p 4433:443 -v $(pwd)/certs/deyuan.me:/etc/nginx/ssl -v $(pwd)/docker-registry.htpasswd:/etc/nginx/conf.d/docker-registry.htpasswd -v $(pwd)/nginx.conf:/etc/nginx/conf.d/docker-registry.conf --link raw-registry:raw-registry nginx
```
* Note that adding `ca.crt` to `/etc/docker/certs.d/deyuan.me:4433` doesn't work, we must add the certificate to system. Also note that restart docker daemon is required.
```
  sudo cp ./certs/ca.crt /usr/local/share/ca-certificates/deyuan.me.crt
  sudo update-ca-certificates
  sudo service docker restart
```
* Optional: remove the certificate
```
  sudo rm /usr/local/share/ca-certificates/deyuan.me.crt
  sudo update-ca-certificates --fresh
  sudo service docker restart
```
