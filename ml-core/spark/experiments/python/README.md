## PySpark

For more examples, see: https://github.com/mahmoudparsian/pyspark-tutorial

Official guides:
- https://spark.apache.org/docs/latest/rdd-programming-guide.html
- https://spark.apache.org/docs/latest/sql-programming-guide.html

#### Run example

Add spark-submit to PATH, then run

```
# local
$ spark-submit xxx.py

# standalone cluster
$ spark-submit --master "spark://mangosteen:7077" xxx.py
```

Or copy/paste code into a pyspark shell to experiment.
