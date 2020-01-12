Right now, we have the components running (excluding modeldb):

- dlk-manager
- vizier-core
- vizier-db
- vizier-suggestion-[algorithm]

These are the binaries I've found after briefly scanning the code structure:

```
.
├── cli
│   ├── Dockerfile
│   └── main.go
├── dlk
│   └── dlkmanager
│       └── dlkmanager.go
├── manager
│   └── main.go
├── suggestion
│   ├── grid
│   |   └── main.go
│   └── random
│       └── main.go
└── earlystopping
    └── medianstopping
        └── main.go
```

Personally, I think there are two issues we can fix to improve the code base:
- component naming and source code naming is inconsistent
- structure can be improved to make it consistent with go projects in the wild :)

Here is the structure off my head:

```
├── cmd
│   ├── cli
│   │   └── cli.go
│   └── dlkctl
│   │   └── dlkcli.go
│   └── dlkmanager
│   │   └── dlkmanager.go
│   └── viziercore
│   |   └── viziercore.go
│   └── earlystopping
│       └── medianstopping.go
├── pkg
│   └── apis
|       └── v1alpha1
|           └── api.proto
│   └── db
│   └── dlk
│   └── mocks
├── manifests
│   └── conf
│   └── dlk
│   └── modeldb
│   └── vizier
├── hack
│   └── build.sh
│   └── deploy.sh
├── test
├── vendor
```

Note that since we mostly want to write suggestion service in python, it should have its own root directory.  If we want to write earlystopping service in other languages as well, then we can also move it out to top-level root.
