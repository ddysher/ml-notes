#!/usr/bin/env python3
#
# rdd_parition.py
#
# Experiment with paritions.

from pyspark import SparkConf, SparkContext

conf = SparkConf().setAppName("Count Appx")
sc = SparkContext(conf=conf)
sc.setLogLevel("ERROR")

nums = range(0, 10)
print(nums)

# The default is defined via sc.defaultParallelism. In a case of using parallelize()
# without partitioner data is evenly distributed between partitions using their
# indices (no partitioning scheme is used).
rdd = sc.parallelize(nums)
print("Number of partitions: {}".format(rdd.getNumPartitions()))
print("Partitioner: {}".format(rdd.partitioner))
print("Partitions structure: {}".format(rdd.glom().collect()))

# Use parallelism of 2, the output would be:
#   Partitions structure: [[0, 1, 2, 3, 4], [5, 6, 7, 8, 9]]
rdd = sc.parallelize(nums, 2)
print("Default parallelism: {}".format(sc.defaultParallelism))
print("Number of partitions: {}".format(rdd.getNumPartitions()))
print("Partitioner: {}".format(rdd.partitioner))
print("Partitions structure: {}".format(rdd.glom().collect()))

# Use parallelism of 15, the output would be:
#   Partitions structure: [[], [0], [1], [], [2], [3], [], [4], [5], [], [6], [7], [], [8], [9]]
#
# This is bad because the time needed to prepare a new thread for processing
# data (one element) is significantly greater than processing time itself.
rdd = sc.parallelize(nums, 15)
print("Default parallelism: {}".format(sc.defaultParallelism))
print("Number of partitions: {}".format(rdd.getNumPartitions()))
print("Partitioner: {}".format(rdd.partitioner))
print("Partitions structure: {}".format(rdd.glom().collect()))

# Use a custom partitioner to partition data based on country so analysis can
# be performed country-wise. The output would be:
# [
#   [('Poland', {'name': 'Marek', 'amount': 51, 'country': 'Poland'}),
#    ('Poland', {'name': 'Paul', 'amount': 75, 'country': 'Poland' })],
#   [('United Kingdom', {'name': 'Bob', 'amount': 100, 'country': 'United Kingdom'}),
#    ('United Kingdom', {'name': 'James', 'amount': 15, 'coutry': 'United Kingdom'}),
#    ('Germany', {'name': 'Johannes', 'amount': 200, 'country': 'Germany' })],
#   [],
#   []
# ]
#
# Note the hash() function put 'United Kingdom' and 'Germany' into the same bucket.
transactions = [
  {'name': 'Bob', 'amount': 100, 'country': 'United Kingdom'},
  {'name': 'James', 'amount': 15, 'country': 'United Kingdom'},
  {'name': 'Marek', 'amount': 51, 'country': 'Poland'},
  {'name': 'Johannes', 'amount': 200, 'country': 'Germany'},
  {'name': 'Paul', 'amount': 75, 'country': 'Poland'},
]

def country_partitioner(country):
  return hash(country)

rdd = sc.parallelize(transactions) \
  .map(lambda el: (el['country'], el)) \
  .partitionBy(4, country_partitioner)

print("Number of partitions: {}".format(rdd.getNumPartitions()))
print("Partitioner: {}".format(rdd.partitioner))
print("Partitions structure: {}".format(rdd.glom().collect()))

# Use mapPartitions to map through each partition; the input to mapPartition
# handler is an iterator which can be used to iterate elements of a partition.
def sum_sales(iterator):
  yield sum(transaction[1]['amount'] for transaction in iterator)

by_country = sc.parallelize(transactions) \
  .map(lambda el: (el['country'], el)) \
  .partitionBy(3, country_partitioner)

print("Partitions structure: {}".format(by_country.glom().collect()))

# Sum sales in each partition
sum_amounts = by_country \
  .mapPartitions(sum_sales) \
  .collect()

print("Total sales for each partition: {}".format(sum_amounts))

# Classical word count; each task will do the map on its own partition, and
# reduce will result in data shuffle.
logFile = "file:///home/deyuan/code/projects/overview.org"
logData = sc.textFile(logFile)

counts = logData.flatMap(lambda line: line.split(" ")) \
  .map(lambda word: (word, 1)).partitionBy(4)

# Values of the same key will be passed to 'reduceByKey'. We'll see
# four parition files in "/tmp/hash".
counts.reduceByKey(lambda x, y: x + y).saveAsTextFile("/tmp/hash")

sc.close()
