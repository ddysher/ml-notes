## NATS AuthN/Z

#### Run NATS

```sh
gnatsd -c ./config
```

#### Verify AuthN/Z

Alice is admin, so the following publishes are allowed:

```sh
nats-pub -s "nats://alice:pwdalice@localhost:4222" req.admin "hello world"
nats-pub -s "nats://alice:pwdalice@localhost:4222" req.foo "hello world"
nats-pub -s "nats://alice:pwdalice@localhost:4222" SANDBOX.X "hello world"
```

Bob is a regular user, so publishing to "req.admin" is not allowed:

```sh
$ nats-pub -s "nats://bob:pwdbob@localhost:4222" req.admin "hello world"
nats: permissions violation for publish to "req.admin"

# Allowed
nats-pub -s "nats://alice:pwdalice@localhost:4222" req.foo "hello world"
```

#### bcrypt

Generate a password and bcrypt'ed hash:

```sh
$ go run util/mkpasswd.go -p
Enter Password: pwdderek
Reenter Password: pwdderek
bcrypt hash: $2a$11$9yy6LvHfnurHtjSaNkK3i.ZCQwTBHleP276GKzPklQxZ.MjeLRBFu
```

Now instead of using plain password "pwdderek", we can use bcrypt hash for NATS,
see [config](./config) file.

To connect, use password:

```sh
$ nats-pub -s "nats://derek:pwdderek@localhost:4222" req.admin "hello world"
Published [req.admin] : 'hello world'

$ nats-pub -s "nats://derek:$2a$11$9yy6LvHfnurHtjSaNkK3i.ZCQwTBHleP276GKzPklQxZ.MjeLRBFu@localhost:4222" req.admin "hello world"
nats: authorization violation
```
