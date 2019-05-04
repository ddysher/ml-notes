## kubernetes persistent volume with nfs

Follow `learning/storage/nfs` to setup a nfs server; then export required directories.

```
sudo mkdir -p /var/export1 && sudo chown nobody:nogroup /var/export1
sudo mkdir -p /var/export2 && sudo chown nobody:nogroup /var/export2
sudo bash -c "echo '/var/export1 192.168.0.0/16(rw,sync,no_subtree_check) 10.0.0.0/8(rw,sync,no_subtree_check) 172.16.0.0/12(rw,sync,no_subtree_check) 127.0.0.0/8(rw,sync,no_subtree_check)' >> /etc/exports"
sudo bash -c "echo '/var/export2 192.168.0.0/16(rw,sync,no_subtree_check) 10.0.0.0/8(rw,sync,no_subtree_check) 172.16.0.0/12(rw,sync,no_subtree_check) 127.0.0.0/8(rw,sync,no_subtree_check)' >> /etc/exports"
sudo exportfs -a
```

Now create the pod. Make sure server IP address is correct.
