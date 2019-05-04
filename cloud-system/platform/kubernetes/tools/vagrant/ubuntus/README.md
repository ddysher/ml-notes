## README

vagrant ssh master
curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -
echo "deb http://apt.kubernetes.io/ kubernetes-xenial main" | sudo tee /etc/apt/sources.list.d/kubernetes.list
sudo apt-get update && sudo apt-get install -y docker-engine kubelet kubeadm kubectl kubernetes-cni


sudo kubeadm init --apiserver-advertise-address 192.168.66.10 --pod-network-cidr 10.244.0.0/16 --token 8c2350.f55343444a6ffc46

sudo cp /etc/kubernetes/admin.conf /home/ubuntu/.kube/
sudo chown $(id -u):$(id -g) /home/ubuntu/.kube/admin.conf
mv /home/ubuntu/.kube/admin.conf /home/ubuntu/.kube/config
