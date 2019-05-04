#!/usr/bin/env python3
#
# rdd_basics.py
#
# Experiment with basic RDD operations.

from pyspark import SparkContext, SparkConf

conf = SparkConf().setAppName("Count App")
sc = SparkContext(conf=conf)
sc.setLogLevel("ERROR")

# 'words' is a RDD in Spark (<class 'pyspark.rdd.RDD'>)
words = sc.parallelize(
  ["scala",
   "java",
   "hadoop",
   "spark",
   "akka",
   "spark vs hadoop",
   "pyspark",
   "pyspark and spark"]
)

#
# count
#
# Number of elements in the RDD is returned.
counts = words.count()
print("Number of elements in RDD -> %i" % (counts))

#
# collect
#
# All the elements in the RDD are returned, as list.
coll = words.collect()
print("Elements in RDD -> %s" % (coll))

#
# foreach
#
# Run a function func on each element of the dataset.
fore = words.foreach(lambda e : print(e))

#
# filter
#
# A new RDD is returned containing the elements, which satisfies the
# function inside the filter.
words_filter = words.filter(lambda x: 'spark' in x)
filtered = words_filter.collect()
print("Fitered RDD -> %s" % (filtered))

#
# map
#
# A new RDD is returned by applying a function to each element in the RDD.
words_map = words.map(lambda x: (x, 1))
mapping = words_map.collect()
print("Key value pair -> %s" % (mapping))

#
# flatmap
#
# map returns a new RDD by applying given function to each element of the RDD.
#   Function in map returns only one item.
# flatMap: Similar to map, it returns a new RDD by applying a function to each
#  element of the RDD, but output is flattened.
split_map = words.map(lambda x: x.split(" "))
print("map split result -> %s" % (split_map.collect()))
split_flatmap = words.flatMap(lambda x: x.split(" "))
print("flatmap split result -> %s" % (split_flatmap.collect()))

#
# reduce
#
# Common reduce operation.
from operator import add
nums = sc.parallelize([1, 2, 3, 4, 5])
adding = nums.reduce(add)
print("Adding all the elements -> %i" % (adding))

#
# join
#
# join returns RDD with a pair of elements with the matching keys and all
# the values for that particular key.
x = sc.parallelize([("spark", 1), ("hadoop", 4), ("storm", 3)])
y = sc.parallelize([("spark", 2), ("hadoop", 5)])
joined = x.join(y)
final = joined.collect()
print("Join RDD -> %s" % (final)) # Join RDD -> [('spark', (1, 2)), ('hadoop', (4, 5))]

#
# cache, persist
#
# Persist this RDD with the default storage level (MEMORY_ONLY). Spark has a
# persist() method for users to use different storage level. The cache()
# method is a shorthand for using the default storage level.
# https://spark.apache.org/docs/latest/rdd-programming-guide.html#rdd-persistence
words.cache()
caching = words.persist().is_cached
print("Words got chached > %s" % (caching))
