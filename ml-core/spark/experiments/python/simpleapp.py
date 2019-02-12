#!/usr/bin/env python3
#
# simpleapp.py
#
# A simple spark application written in Python.

from pyspark import SparkContext

# Option1: Running locally for testing, use:
#   spark-submit --master "local" simpleapp.py
#
# sc = SparkContext("local", "First Application")

# Option2: Running on a cluster (standalone), use:
#   spark-submit --master "spark://sugarcane:7077" simpleapp.py
#
# sc = SparkContext("spark://sugarcane:7077", "First Application")

# Note just like in Java, we can use session build to build master info.
from pyspark import SparkConf

conf = SparkConf().setAppName("PySpark App")
sc = SparkContext(conf=conf)

logFile = "file:///home/deyuan/code/general.org"
logData = sc.textFile(logFile).cache()

numAs = logData.filter(lambda s: 'a' in s).count()
numBs = logData.filter(lambda s: 'b' in s).count()
print("Lines with a: %i, lines with b: %i" % (numAs, numBs))
