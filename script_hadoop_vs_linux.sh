#!/bin/bash
time cat $1 | tr ' ' '\n' | sort | uniq -c 
time hadoop jar hadoop-mapreduce-examples-3.3.1.jar wordcount /input/4vxdw3pa out4vxdw3pa
hdfs dfs -rm -r -skipTrash -f outweh83uyn
