## Spark with Java

#### Run example

Build the project:

```
mvn package
```

Then add spark-submit to PATH, and run

```
# local
$ spark-submit --class "SimpleApp" --master "local[4]" target/simple-project-1.0.jar

# standalone cluster
$ spark-submit --class "SimpleApp" --master "spark://mangosteen:7077" target/simple-project-1.0.jar
```
