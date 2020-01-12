<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
- [Experiment](#experiment)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

[PMML](http://dmg.org/pmml/v4-4/GeneralStructure.html) is a XML-based standard to represent mining
models. The standard implementation is a Java based library & API & Command line, see [JPMML](https://github.com/jpmml/).

*References*

- https://openscoring.io/

# Experiment

To start PMML scoring server, use [openscoring](https://github.com/openscoring/openscoring) server:

```
java -jar openscoring-server-executable-${version}.jar
```

Once the server starts, adds a model to the server:

```
curl -X PUT --data-binary @DecisionTreeIris.pmml -H "Content-type: text/xml" http://localhost:8080/openscoring/model/DecisionTreeIris
```

Then we'll be able to access the model in http://localhost:8080/openscoring/model/DecisionTreeIris.
