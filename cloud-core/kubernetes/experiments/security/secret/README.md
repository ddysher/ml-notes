## Kubernetes Secret (v1.0)

#### Create Secret Manually

The following command creates secret manually. It's important to note that the `data` field of
Secret must be base64-encoded.

```
$ kubectl create -f secret1.yaml
```

To use non-base64 data, there's a `stringData` field:

```
$ kubectl create -f secret2.yaml

# verify the data via:
$ echo 'apiUrl: "https://my.api.com/api/v1"
username: {{username}}
password: {{password}}' | base64
...

```

The `stringData` takes precedence over `data`:

```
$ kubectl create -f secret3.yaml
```
