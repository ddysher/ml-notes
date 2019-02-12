/*
 * SimpleApp.java
 *
 * A simple spark application written in Java.
 */
import org.apache.spark.sql.SparkSession;
import org.apache.spark.sql.Dataset;

public class SimpleApp {

  public static void main(String[] args) {
    // Option1: Running locally for testing, use:
    //   spark-submit --class "SimpleApp" --master "local" target/simple-project-1.0.jar
    //
    // Option2: Running in a cluster, use:
    //   spark-submit --class "SimpleApp" --master "spark://sugercane:7077" target/simple-project-1.0.jar
    //
    // Note Builder has a master() method to define master URL, it will use the
    // link passed from spark-submit.
    SparkSession spark = SparkSession.builder().
      appName("Simple Application").getOrCreate();

    String logFile = "/home/deyuan/code/general.org"; // Should be some file on your system
    Dataset<String> logData = spark.read().textFile(logFile).cache();

    long numAs = logData.filter(s -> s.contains("a")).count();
    long numBs = logData.filter(s -> s.contains("b")).count();
    System.out.println("Lines with a: " + numAs + ", lines with b: " + numBs);

    spark.stop();
  }

  // compute simulates a bit of computation (~10s), used for execution inspection.
  public static void compute() {
    int x = 0;
    for (int i = 0; i < 200000; i++) {
      for (int j = 0; j < 200000; j++) {
        for (int k = 0; k < 200000; k++) {
          x = i + j + k;
        }
      }
    }
    System.out.println(x);
  }
}
