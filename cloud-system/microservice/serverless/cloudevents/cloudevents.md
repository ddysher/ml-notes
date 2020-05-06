<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
- [Specification](#specification)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

*Date: 12/21/2018, v0.2*

[CloudEvents](https://cloudevents.io/), at its core, defines a set of metadata, called attributes,
about the event being transferred between systems, and how those pieces of metadata should appear
in that message. This metadata is meant to be the minimal set of information needed to route the
request to the proper component and to facilitate proper processing of the event by that component.
Data that is not intended for that purpose should instead be placed within the event (the `data`
attribute) itself.

CloudEvents reached v1.0 on 2019 and was promoted as an incubation project in CNCF.

# Specification

The cloudevents specification is effectively a JSON schema. There is also a serverless workflow
specification about how to orchastrate and pass messages (cloudevents) between functions.

The required attributes include:
- id: String
- source: URI-reference
- specversion: String
- type: String

The optional attributes include:
- datacontenttype: String
- dataschema: URI
- subject: String
- time: Timestamp

In addition, cloudevents supports any number of additional context attributes with distinct names,
known as "extension attributes". At last, a `data` field is used for user data payload.

Following is a simple cloudevents example:

```json
{
    "specversion" : "0.2",
    "type" : "com.github.pull.create",
    "source" : "https://github.com/cloudevents/spec/pull/123",
    "id" : "A234-1234-1234",
    "time" : "2018-04-05T17:31:00Z",
    "comexampleextension1" : "value",
    "comexampleextension2" : {
        "othervalue": 5
    },
    "contenttype" : "text/xml",
    "data" : "<much wow=\"xml\"/>"
}
```
