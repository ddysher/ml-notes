<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Overview](#overview)
- [Scheduler](#scheduler)
- [Experiments](#experiments)
- [References](#references)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

Luigi is a Python module that helps you build complex pipelines of batch jobs. It handles dependency
resolution, workflow management, visualization etc. It also comes with Hadoop support built in. Luigi
has experimental support for tracking task history; it stores information in a relational database,
whose connection information is specified from configuration file.

# Scheduler

luigi.scheduler module. The system for scheduling tasks and executing them in order. Deals with
dependencies, priorities, resources, etc. The Worker pulls tasks from the scheduler (usually over
the REST interface) and executes them. See Using the Central Scheduler for more info.

**Kubernetes**

Kubernetes module is a contrib module which simply executes a job and waits for it to complete.

# Experiments

To run official example, we need to set 'PYTHONPATH', i.e.

```
$ PYTHONPATH='.' luigi --module top_artists AggregateArtists --local-scheduler --date-interval 2012-06
$ PYTHONPATH='.' luigi --module top_artists Top10Artists --local-scheduler --date-interval 2012-06
```

The DataIntervalParameter will output the following data:

```
[datetime.date(2012, 6, 1), datetime.date(2012, 6, 2), datetime.date(2012, 6, 3), datetime.date(2012, 6, 4), datetime.date(2012, 6, 5), datetime.date(2012, 6, 6), datetime.date(2012, 6, 7), datetime.date(2012, 6, 8), datetime.date(2012, 6, 9), datetime.date(2012, 6, 10), datetime.date(2012, 6, 11), datetime.date(2012, 6, 12), datetime.date(2012, 6, 13), datetime.date(2012, 6, 14), datetime.date(2012, 6, 15), datetime.date(2012, 6, 16), datetime.date(2012, 6, 17), datetime.date(2012, 6, 18), datetime.date(2012, 6, 19), datetime.date(2012, 6, 20),datetime.date(2012, 6, 21), datetime.date(2012, 6, 22), datetime.date(2012, 6, 23), datetime.date(2012, 6, 24), datetime.date(2012, 6, 25), datetime.date(2012, 6, 26), datetime.date(2012, 6, 27), datetime.date(2012, 6, 28), datetime.date(2012, 6, 29), datetime.date(2012, 6, 30)]
```

Step by step tutorial: http://luigi.readthedocs.io/en/stable/example_top_artists.html

# References

- https://github.com/spotify/luigi/
- http://bionics.it/posts/luigi-tutorial
- http://drincruz.github.io/slides/intro-data-pipelines-luigi/index.html

*Related projects*

- https://github.com/pinterest/pinball
- https://github.com/apache/incubator-airflow
