from pyspark import SparkContext, SparkConf # pyspark==3.2.0

def main():
    conf = SparkConf()
    sc = SparkContext(conf=conf)
    distFile = sc.textFile("hdfs://localhost:9000/user/azureuser/input/")
    count = distFile.flatMap(lambda line: line.split(" ")).map(lambda word: (word, 1)).reduceByKey(lambda a, b: a + b).sortByKey()
    count.saveAsTextFile("hdfs://localhost:9000/user/azureuser/output")

if __name__ == "__main__":
    main()
