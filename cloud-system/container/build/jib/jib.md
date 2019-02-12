<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

Jib builds Docker and OCI images for Java applications without a Docker daemon, and without writing
any Dockerfile. It is available as plugins for Maven and Gradle and as a Java library. For example,
to use jib with maven, add the following plugin to `pom.xml`:

```
  <build>
    <plugins>
      <plugin>
        <groupId>com.google.cloud.tools</groupId>
        <artifactId>jib-maven-plugin</artifactId>
        <version>1.3.0</version>
        <configuration>
          <to>
            <image>imagename</image>
          </to>
        </configuration>
      </plugin>
    </plugins>
  </build>
```

then simply execute `maven compile jib:build`, Jib will build a docker image and push it to remote
repository.
