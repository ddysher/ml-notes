#!/usr/bin/env python3
#
# rdd_transformation.py
#
# Experiment with RDD transformations.

# Run interactive shell with
#   https://www.supergloo.com/fieldnotes/apache-spark-transformations-python-examples
#
# - map(func)
# - flatmap(func)
# - filter(func)
# - mapPartitions(func, preservespartitioning=false): similar to map but applies to a partition of RDD
# - mapPartitionsWithIndex(func): similar to mapPartition, except a partition index is passed to handler function
# - sample(withreplacement, fraction, seed)
# - union(rdd)
# - intersect(rdd)
# - distinct([numtasks])
# - groupByKey([numtasks])
# - reduceByKey(func, [numtasks])
# - aggregateByKey(zerovalue)(seqop, combop, [numtasks])
# - sortByKey(ascending=true, numpartitions=none, keyfunc=<function <lambda>>)
# - join(otherdataset, [numtasks])
#
# The group of transformation functions (groupByKey, reduceByKey, aggregateByKey, sortByKey, join) all act on key,value pair RDDs.

from pyspark import SparkContext, SparkConf

conf = SparkConf().setAppName("Transformation App")
sc = SparkContext(conf=conf)
sc.setLogLevel("ERROR")

#
# mapPartitions, where each partition is passed to handler f() as
# an iterator respectively.
#
# The method map converts each element of the source RDD into a single element
# of the result RDD by applying a function. mapPartitions converts each partition
# of the source RDD into multiple elements of the result (possibly none).
#
one_through_9 = range(1,10)

# If we use mapPartitions, each paritition of the original RDD is passed to
# handler. Pay attention the the handler f(), which uses yield result.
def f(iterator): yield sum(iterator)
parallel = sc.parallelize(one_through_9, 3)
parallel.mapPartitions(f).collect() # [6, 15, 24]

# If we use map, each element of the original RDD is passed to handler.
parallel.map(lambda x: x*2).collect() # [2, 4, 6, 8, 10, 12, 14, 16, 18]

# default parallelism is depends system cpu resource
#   [1, 2, 3, 4, 5, 6, 7, 17]  # 8 core
# or
#   [3, 7, 11, 24] # 4 core
parallel = sc.parallelize(one_through_9)
parallel.mapPartitions(f).collect()

#
# mapParitionsWithIndex
#
parallel = sc.parallelize(range(1,10),4)
def show(index, iterator): yield 'index: '+str(index)+" values: "+ str(list(iterator))
parallel.mapPartitionsWithIndex(show).collect()
# ['index: 0 values: [1, 2]', 'index: 1 values: [3, 4]', 'index: 2 values: [5, 6]', 'index: 3 values: [7, 8, 9]']

#
# groupByKey
#
# Group baby names via name.
baby_names = sc.textFile("./baby_names.csv")
rows = baby_names.map(lambda line: line.split(","))

# Now we have a RDD where each row is a list. The map below further extracts only
# the second and third columns, and group the RDD based on second column (the key).
# The last map is used for printing.
namesToCounties = rows.map(lambda n: (str(n[1]), str(n[2]))).groupByKey()
print(namesToCounties.map(lambda x: {x[0]: list(x[1])}).collect())

#
# reduceByKey
#
# Compute total count of names.
from operator import add
filtered_rows = baby_names.filter(lambda line: 'Count' not in line).map(lambda line: line.split(","))
print(filtered_rows.map(lambda n: (str(n[1]), int(n[4]))).reduceByKey(add).collect())

#
# sortByKey
#
print(filtered_rows.map(lambda n: (str(n[1]), int(n[4]))).sortByKey().collect())

#
# join
#
names1 = sc.parallelize(("abe", "abby", "apple")).map(lambda a: (a, 1))
names2 = sc.parallelize(("apple", "beatty", "beatrice")).map(lambda a: (a, 1))
names1.join(names2).collect()   # [('apple', (1, 1))]
