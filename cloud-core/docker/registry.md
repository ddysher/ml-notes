<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
- [Specification](#specification)
  - [Registry API v2](#registry-api-v2)
    - [Content Digest](#content-digest)
    - [Digest Header](#digest-header)
    - [Pulling an image](#pulling-an-image)
    - [Pushing an image](#pushing-an-image)
    - [Canceling an Upload](#canceling-an-upload)
    - [Deleting a Layer](#deleting-a-layer)
    - [Listing Repositories](#listing-repositories)
    - [Listing Image Tags](#listing-image-tags)
    - [Deleting an Image](#deleting-an-image)
    - [Pagination](#pagination)
    - [Headers](#headers)
  - [Registry format](#registry-format)
    - [Registry on-disk format](#registry-on-disk-format)
    - [Registry links and manifests](#registry-links-and-manifests)
  - [Token Authentication](#token-authentication)
- [Misc Notes](#misc-notes)
  - [Upload purging](#upload-purging)
  - [Repository naming](#repository-naming)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

Date: 10/25/2016

The Registry (Distribution) is a stateless, highly scalable server side application that stores and
lets you distribute Docker images. The Distribution project has the further long term goal of providing
a secure tool chain for distributing content.

# Specification

## [Registry API v2](https://docs.docker.com/registry/spec/api/)

The registry v2 API provides a protocol for images distribution, docker engine is a reference
implementation. The specification is lengthy, following is a few summary.

### Content Digest

A digest is a serialized hash result, consisting of a algorithm and hex portion, e.g.
```
sha256:6c3c624b58dbbcd3c0dd82b4c53f04194d1247c6eebdaab7c610cf7d66709b3b
```

### Digest Header

To provide verification of http content, any response may include a `Docker-Content-Digest` header.
This will include the digest of the target entity returned in the response. For blobs, this is the
entire blob content. For manifests, this is the manifest body without the signature content, also
known as the JWS payload.

### Pulling an image

APIs for pulling images:

- `HEAD /v2/<name>/manifests/<reference>`: check image manifest existence
- `GET /v2/<name>/manifests/<reference>`: fetch image manifest
- `GET /v2/<name>/blobs/<digest>`: pull a layer

Here, `name` is image name, e.g. library/ubuntu, `reference` may include a tag or digest.

To pull an image, we first issue GET manifest request, which returns following data (if image exists):

```
{
   "name": <name>,
   "tag": <tag>,
   "fsLayers": [
      {
         "blobSum": <digest>
      },
      ...
    ]
   ],
   "history": <v1 images>,
   "signature": <JWS>
}
```

Then we send GET blob request for individual layers using digest. The endpoint may issue a 307 (302
for <HTTP 1.1) redirect to another service for downloading the layer. There is a `Range` header to
allow incremental downloads.

For example, pulling image `ddysher/buxybox:1.24`.

```
$ docker images busybox:1.24
REPOSITORY          TAG                 IMAGE ID            CREATED             SIZE
busybox             1.24                47bcc53f74dc        2 years ago         1.11MB
```

Logs from registry:

```
GET /v2/ddysher/busybox/manifests/1.24
{
   "schemaVersion": 1,
   "name": "ddysher/busybox",
   "tag": "1.24",
   "architecture": "amd64",
   "fsLayers": [
     {
         "blobSum": "sha256:4f4fb700ef54461cfa02571ae0db9a0dc1e0cdb5577484a6d75e68dc38e8acc1"
      },
      {
         "blobSum": "sha256:ece6a2d58adfea639490d026eb187c772a789041039c25a9e497fd1db7860f55"
      }
   ],
   "history": [...]
   "signatures": [
      {
         "header": {
            "jwk": {
               "crv": "P-256",
               "kid": "44DV:YCQQ:ILCN:RJZC:OO7H:NYFH:DTTD:S3JZ:IKJC:EISQ:YNW6:ZUXK",
               "kty": "EC",
               "x": "eu0shR44dw8Ig72Pufhi5-lozmwSO_a6J491VDukdn4",
               "y": "1X8rvK4x_0PUZuPr8Xg9KqjOFcLAzatRinRYQSlm-iQ"
            },
            "alg": "ES256"
         },
         "signature": "8QcPZt1Y1o90sG0vdl2blK_tik029MPqtBQrQyb2sOGrItALq4uZ0KedGjw51fakWUGGembcGwpODpryrhKsBQ",
         "protected": "eyJmb3JtYXRMZW5ndGgiOjE5MjAsImZvcm1hdFRhaWwiOiJDbjAiLCJ0aW1lIjoiMjAxOC0wOS0yOVQwNDozMjoxMVoifQ"
      }
   ]
}

# Note the first two hashes are layer digest, the last hash is manifest digest (image ID).
GET /v2/ddysher/busybox/blobs/sha256:4f4fb700ef54461cfa02571ae0db9a0dc1e0cdb5577484a6d75e68dc38e8acc1
GET /v2/ddysher/busybox/blobs/sha256:ece6a2d58adfea639490d026eb187c772a789041039c25a9e497fd1db7860f55
GET /v2/ddysher/busybox/blobs/sha256:47bcc53f74dc94b1920f0b34f6036096526296767650f223433fe65c35f149eb
```

### Pushing an image

APIs for pushing image:

- `POST /v2/<name>/blobs/uploads/`: start pushing
- `PUT /v2/<name>/blobs/uploads/<uuid>?digest=<digest>`: monolithic upload, as well as completing upload
- `PATCH /v2/<name>/blobs/uploads/<uuid>`: chunked upload
- `HEAD /v2/<name>/blobs/<digest>`: check layer blob existance

To push an image, we first issue POST request (to upload a layer), if successful, a `202 Accepted`
response will be returned with the upload URL in the `Location` header:

```
202 Accepted
Location: /v2/<name>/blobs/uploads/<uuid>
Range: bytes=0-<offset>
Content-Length: 0
Docker-Upload-UUID: <uuid>
```

Client is responsible to use the URL from `Location` header to upload the layer. The `uuid` parameter
can be an actual UUID, but this is not required (pay attention it's not the layer's digest). Once
client receives the `Location`, it can use:
- Monolithic Upload: A monolithic upload is simply a chunked upload with a single chunk and may be
  favored by clients that would like to avoided the complexity of chunking. It uses endpoint:
  ```
  PUT /v2/<name>/blobs/uploads/<uuid>?digest=<digest>
  ```
- Chunked Upload: To carry out an upload of a chunk, the client can specify a range header and only
  include that part of the layer file:
  ```
  PATCH /v2/<name>/blobs/uploads/<uuid>
  Content-Length: <size of chunk>
  Content-Range: <start of range>-<end of range>
  Content-Type: application/octet-stream

  <Layer Chunk Binary Data>
  ```
  To complete upload, client must send a PUT request with digest parameter:
  ```
  PUT /v2/<name>/blob/uploads/<uuid>?digest=<digest>
  ```
After pusing all layers, client should post image manifest via `/v2/<name>/manifest`.

For example, push image `busybox:1.27`:

```
$ docker images busybox:1.27
REPOSITORY          TAG                 IMAGE ID            CREATED             SIZE
busybox             1.27                6ad733544a63        10 months ago       1.13MB

# Information about busybox:1.27
"fsLayers":
  "sha256:a3ed95caeb02ffe68cdd9fd84406680ae93d633cb16422d00e8a7c22955b46d4"
  "sha256:0ffadd58f2a61468f527cc4f0fc45272ee4a1a428abe014546c89de2aa6a0eb5"
"imageID:"
  "sha256:6ad733544a6317992a6fac4eb19fe1df577d4dec7529efec28a5bd0edad0fd30"
```

Logs from registry:

```
HEAD  /v2/busybox/blobs/sha256:0ffadd58f2a61468f527cc4f0fc45272ee4a1a428abe014546c89de2aa6a0eb5 (404)
POST  /v2/busybox/blobs/uploads/
PATCH /v2/busybox/blobs/uploads/6f36695a-b55e-4445-a16b-c7f869dd6244?_state=X (202)
PUT   /v2/busybox/blobs/uploads/6f36695a-b55e-4445-a16b-c7f869dd6244?_state=XXX&digest=sha256%3A0ffadd58f2a61468f527cc4f0fc45272ee4a1a428abe014546c89de2aa6a0eb5 (201)
HEAD  /v2/busybox/blobs/sha256:0ffadd58f2a61468f527cc4f0fc45272ee4a1a428abe014546c89de2aa6a0eb5 (200)

HEAD  /v2/busybox/blobs/sha256:6ad733544a6317992a6fac4eb19fe1df577d4dec7529efec28a5bd0edad0fd30 (404)
POST  /v2/busybox/blobs/uploads/
PATCH /v2/busybox/blobs/uploads/fa5b1367-75d9-4109-9ae8-c9563e404ff4?_state=X (202)
PUT   /v2/busybox/blobs/uploads/fa5b1367-75d9-4109-9ae8-c9563e404ff4?_state=XXX&digest=sha256%3A6ad733544a6317992a6fac4eb19fe1df577d4dec7529efec28a5bd0edad0fd30 (201)
HEAD  /v2/busybox/blobs/sha256:6ad733544a6317992a6fac4eb19fe1df577d4dec7529efec28a5bd0edad0fd30 (200)

PUT /v2/busybox/manifests/1.27
```

### Canceling an Upload

An upload can be cancelled by issuing a DELETE request to the upload endpoint. The format will be
as follows:

```
DELETE /v2/<name>/blobs/uploads/<uuid>
```

### Deleting a Layer

A layer may be deleted from the registry via its name and digest. A delete may be issued with the
following request format:

```
DELETE /v2/<name>/blobs/<digest>
```

### Listing Repositories

List repositories using the following endpoint. Note that registry implementation might choose to
list only ones that requester can access, and it's not guaranteed a subsequent pull will always
succeed when an image shows up in list result:

```
GET /v2/_catalog
```

### Listing Image Tags

The tags for an image repository can be retrieved with the following request:

```
GET /v2/<name>/tags/list
```

### Deleting an Image

An image may be deleted from the registry via its name and reference. A delete may be issued with
the following request format:

```
DELETE /v2/<name>/manifests/<reference>
```

### Pagination

Bothe listing repositories and listing image tags can use `Pagination`. Paginated catalog results
can be retrieved by adding an `n` parameter to the request URL, declaring that the response should
be limited to n results.

```
GET /v2/_catalog?n=<integer>
```

The response looks like:

```
200 OK
Content-Type: application/json
Link: <<url>?n=<n from the request>&last=<last repository in response>>; rel="next"

{
  "repositories": [
    <name>,
    ...
  ]
}
```

To get the next result set, a client would issue the request as follows, using the URL encoded in
the described `Link` header:

```
GET /v2/_catalog?n=<n from the request>&last=<last repository value from previous response>
```

### Headers

There are quite a few headers used in the API specification:

- Range
- Link
- Location
- Docker-Content-Digest
- Docker-Upload-UUID
- Accept: application/vnd.docker.distribution.manifest.v2+json (note: `vnd` stands for vendor)

## Registry format

### Registry on-disk format

Following is registry on-disk format after pusing two images:
```
$ docker run -d -p 5000:5000 --restart=always --name registry -v /tmp/registry:/var/lib/registry registry:2
757f61cb413a99e134997cb4c29aca81f01cbbb3340393bc4126687be31c7dc9

$ tree /tmp/registry
/tmp/registry
└── docker
    └── registry
        └── v2
            ├── blobs
            │   └── sha256
            │       ├── 0f
            │       │   └── 0ffadd58f2a61468f527cc4f0fc45272ee4a1a428abe014546c89de2aa6a0eb5
            │       │       └── data
            │       ├── 47
            │       │   └── 47bcc53f74dc94b1920f0b34f6036096526296767650f223433fe65c35f149eb
            │       │       └── data
            │       ├── 4f
            │       │   └── 4f4fb700ef54461cfa02571ae0db9a0dc1e0cdb5577484a6d75e68dc38e8acc1
            │       │       └── data
            │       ├── 6a
            │       │   └── 6ad733544a6317992a6fac4eb19fe1df577d4dec7529efec28a5bd0edad0fd30
            │       │       └── data
            │       ├── 7e
            │       │   └── 7e637087346d657e396a6e2e123682780f7eed39ce977058ec1e07de6516fdc7
            │       │       └── data
            │       ├── 91
            │       │   └── 91ef6c1c52b166be02645b8efee30d1ee65362024f7da41c404681561734c465
            │       │       └── data
            │       └── ec
            │           └── ece6a2d58adfea639490d026eb187c772a789041039c25a9e497fd1db7860f55
            │               └── data
            └── repositories
                └── busybox
                    ├── _layers
                    │   └── sha256
                    │       ├── 0ffadd58f2a61468f527cc4f0fc45272ee4a1a428abe014546c89de2aa6a0eb5
                    │       │   └── link
                    │       ├── 47bcc53f74dc94b1920f0b34f6036096526296767650f223433fe65c35f149eb
                    │       │   └── link
                    │       ├── 4f4fb700ef54461cfa02571ae0db9a0dc1e0cdb5577484a6d75e68dc38e8acc1
                    │       │   └── link
                    │       ├── 6ad733544a6317992a6fac4eb19fe1df577d4dec7529efec28a5bd0edad0fd30
                    │       │   └── link
                    │       └── ece6a2d58adfea639490d026eb187c772a789041039c25a9e497fd1db7860f55
                    │           └── link
                    ├── _manifests
                    │   ├── revisions
                    │   │   └── sha256
                    │   │       ├── 7e637087346d657e396a6e2e123682780f7eed39ce977058ec1e07de6516fdc7
                    │   │       │   └── link
                    │   │       └── 91ef6c1c52b166be02645b8efee30d1ee65362024f7da41c404681561734c465
                    │   │           └── link
                    │   └── tags
                    │       ├── 1.24
                    │       │   ├── current
                    │       │   │   └── link
                    │       │   └── index
                    │       │       └── sha256
                    │       │           └── 7e637087346d657e396a6e2e123682780f7eed39ce977058ec1e07de6516fdc7
                    │       │               └── link
                    │       └── 1.27
                    │           ├── current
                    │           │   └── link
                    │           └── index
                    │               └── sha256
                    │                   └── 91ef6c1c52b166be02645b8efee30d1ee65362024f7da41c404681561734c465
                    │                       └── link
                    └── _uploads
                        └── 514c1826-65b3-4207-86d3-9704b6e8bee4
                            └── hashstates
                                └── sha256
                                    └── 0

48 directories, 19 files
```

### Registry links and manifests

Following various sha256 and links:

```
$ cat /tmp/registry/docker/registry/v2/repositories/busybox/_manifests/tags/1.24/current/link
sha256:7e637087346d657e396a6e2e123682780f7eed39ce977058ec1e07de6516fdc7%

$ cat /tmp/registry/docker/registry/v2/repositories/busybox/_manifests/tags/1.24/index/sha256/7e637087346d657e396a6e2e123682780f7eed39ce977058ec1e07de6516fdc7/link
sha256:7e637087346d657e396a6e2e123682780f7eed39ce977058ec1e07de6516fdc7%

$ cat /tmp/registry/docker/registry/v2/blobs/sha256/7e/7e637087346d657e396a6e2e123682780f7eed39ce977058ec1e07de6516fdc7/data
{
   "schemaVersion": 2,
   "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
   "config": {
      "mediaType": "application/vnd.docker.container.image.v1+json",
      "size": 1370,
      "digest": "sha256:47bcc53f74dc94b1920f0b34f6036096526296767650f223433fe65c35f149eb"
   },
   "layers": [
      {
         "mediaType": "application/vnd.docker.image.rootfs.diff.tar.gzip",
         "size": 699930,
         "digest": "sha256:ece6a2d58adfea639490d026eb187c772a789041039c25a9e497fd1db7860f55"
      },
      {
         "mediaType": "application/vnd.docker.image.rootfs.diff.tar.gzip",
         "size": 32,
         "digest": "sha256:4f4fb700ef54461cfa02571ae0db9a0dc1e0cdb5577484a6d75e68dc38e8acc1"
      }
   ]
}

$ docker images busybox:1.24
REPOSITORY          TAG                 IMAGE ID            CREATED             SIZE
busybox             1.24                47bcc53f74dc        2 years ago         1.11MB

$ curl -v localhost:5000/v2/busybox/manifests/1.24
*   Trying ::1...
* TCP_NODELAY set
* Connected to localhost (::1) port 5000 (#0)
> GET /v2/busybox/manifests/1.24 HTTP/1.1
> Host: localhost:5000
> User-Agent: curl/7.61.0
> Accept: */*
>
< HTTP/1.1 200 OK
< Content-Length: 2559
< Content-Type: application/vnd.docker.distribution.manifest.v1+prettyjws
< Docker-Content-Digest: sha256:e50bcc13b5bbbe42aba950ff99a1b6482ddcfe1f94c8880e740dab659e7b46d5
< Docker-Distribution-Api-Version: registry/2.0
< Etag: "sha256:e50bcc13b5bbbe42aba950ff99a1b6482ddcfe1f94c8880e740dab659e7b46d5"
< X-Content-Type-Options: nosniff
< Date: Sat, 29 Sep 2018 06:33:27 GMT
<
{
   "schemaVersion": 1,
   "name": "busybox",
   "tag": "1.24",
   "architecture": "amd64",
   "fsLayers": [
      {
         "blobSum": "sha256:4f4fb700ef54461cfa02571ae0db9a0dc1e0cdb5577484a6d75e68dc38e8acc1"
      },
      {
         "blobSum": "sha256:ece6a2d58adfea639490d026eb187c772a789041039c25a9e497fd1db7860f55"
      }
   ],
   "history": [
      {
         "v1Compatibility": "{\"architecture\":\"amd64\",\"config\":{\"Hostname\":\"156e10b83429\",\"Domainname\":\"\",\"User\":\"\",\"AttachStdin\":false,\"AttachStdout\":false,\"AttachStderr\":false,\"Tty\":false,\"OpenStdin\":false,\"StdinOnce\":false,\"Env\":null,\"Cmd\":[\"sh\"],\"Image\":\"56ed16bd6310cca65920c653a9bb22de6b235990dcaa1742ff839867aed730e5\",\"Volumes\":null,\"WorkingDir\":\"\",\"Entrypoint\":null,\"OnBuild\":null,\"Labels\":{}},\"container\":\"5f8098ec29947b5bea80483cd3275008911ce87438fed628e34ec0c522665510\",\"container_config\":{\"Hostname\":\"156e10b83429\",\"Domainname\":\"\",\"User\":\"\",\"AttachStdin\":false,\"AttachStdout\":false,\"AttachStderr\":false,\"Tty\":false,\"OpenStdin\":false,\"StdinOnce\":false,\"Env\":null,\"Cmd\":[\"/bin/sh\",\"-c\",\"#(nop) CMD [\\\"sh\\\"]\"],\"Image\":\"56ed16bd6310cca65920c653a9bb22de6b235990dcaa1742ff839867aed730e5\",\"Volumes\":null,\"WorkingDir\":\"\",\"Entrypoint\":null,\"OnBuild\":null,\"Labels\":{}},\"created\":\"2016-03-18T18:22:48.810791943Z\",\"docker_version\":\"1.9.1\",\"id\":\"75da91af850ddb8234ef23ed0b8ffe3246cf443777d22114b966611842b2410e\",\"os\":\"linux\",\"parent\":\"26bbc554d89d56f3365c7ad804d54d5f7d0a80cbf1012b567a97b85e5395f3b9\"}"
      },
      {
         "v1Compatibility": "{\"id\":\"26bbc554d89d56f3365c7ad804d54d5f7d0a80cbf1012b567a97b85e5395f3b9\",\"created\":\"2016-03-18T18:22:48.262403239Z\",\"container_config\":{\"Cmd\":[\"/bin/sh -c #(nop) ADD file:47ca6e777c36a4cfffe3f918b64a445c8f32300deeb9dfa5cc47261bd7b75d21 in /\"]}}"
      }
   ],
   "signatures": [
      {
         "header": {
            "jwk": {
               "crv": "P-256",
               "kid": "WRTN:YSMC:ROVS:I4LH:ZDQG:T3TM:GZWH:ACPU:D3TB:Y2CX:QZJB:7VMB",
               "kty": "EC",
               "x": "gvYmHAMgpZhxpKhllW5kjB0VuT8ObXyhxQcyUi5pZ5I",
               "y": "feozhpq2CLKLipuTeMy2_1Bj76KVXIC9LyHK2Mxm5-Y"
            },
            "alg": "ES256"
         },
         "signature": "Or2HLgWd7Qpdu0xGXJcnCQphlB3-lare9MlG8ksmfF0rGLLcZZIeSoBzTo4ZXsEsm0D_oXhEEHV8tg9-Jvel5Q",
         "protected": "eyJmb3JtYXRMZW5ndGgiOjE5MTIsImZvcm1hdFRhaWwiOiJDbjAiLCJ0aW1lIjoiMjAxOC0wOS0yOVQwNjozMzoyN1oifQ"
      }
   ]
}
```

## [Token Authentication](https://docs.docker.com/registry/spec/auth/token/)

N/A

# Misc Notes

## Upload purging

Upload purging is a background process that periodically removes orphaned files from the upload
directories of the registry. Upload purging is enabled by default.

*References*
- https://issues.sonatype.org/browse/NEXUS-9293
- https://docs.docker.com/registry/configuration/#uploadpurging

## Repository naming

Docker looks for either a "." (domain separator) or ":" (port separator) to learn that the first
part of the repository name is a location and not a user name. If you just had `localhost` without
either `.localdomain` or `:5000` (either one would do) then Docker would believe that `localhost`
is a username, as in localhost/ubuntu or samalba/hipache.

*References*
- https://blog.docker.com/2013/07/how-to-use-your-own-registry/
- https://github.com/docker/distribution/blob/master/docs/deploying.md
