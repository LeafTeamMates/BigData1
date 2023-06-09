#!/usr/bin/env python3
"""sortedAppreciate.py"""

import argparse
from pyspark.sql import SparkSession
import time
import re

# Parse the arguments
parser = argparse.ArgumentParser()
parser.add_argument("--input", help="the input path")
parser.add_argument("--output", help="the output path")

args = parser.parse_args()
input_path, output_path = args.input, args.output

# Create the SparkSession
spark = SparkSession.builder.appName("sortedAppreciate").getOrCreate()

def split(line):
    # Replace commas inside quotes with semicolons
    line = re.sub(r',(?=[^"]*"[^"]*(?:"[^"]*"[^"]*)*$)', lambda m: m.group().replace(',', ';'), line)
    # Split the line using commas as a delimiter
    fields = line.split(',')
    # Replace semicolons back to commas
    fields = [field.replace(';', ',') for field in fields]
    return fields[2], fields[4], fields[5]

def valid(line):
    """Checks if the line is valid"""
    try:
        helpfulness_numerator = int(line[1])
        helpfulnes_denominator = int(line[2])
    except ValueError:
        return False

    return helpfulness_numerator >= 0 and helpfulnes_denominator > 0 and helpfulness_numerator <= helpfulnes_denominator

# calculate time elapsed
start_time = time.time()
# ================================
# Read the input file with spark core
input_rdd = spark.sparkContext.textFile(input_path)

# PRE PROCESSING
# eseguo lo split in parole
input_rdd = input_rdd.map(split)
# filtro i record validi 
validated_rdd = input_rdd.filter(valid)
# Ogni record sarà = (userId, helpfulnessNumerator/helpfulnessDenominator)
userid_rating_rdd = validated_rdd.map(lambda x: (x[0], int(x[1]) / int(x[2])))

# Compute the average rating for each user
userid_avg_rating_rdd = userid_rating_rdd.aggregateByKey((0, 0), lambda a,b: (a[0] + b, a[1] + 1), lambda a,b: (a[0] + b[0], a[1] + b[1]))
userid_avg_rating_rdd = userid_avg_rating_rdd.mapValues(lambda v: v[0] / v[1])

# Sort the users by average rating
sorted_userid_avg_rating_rdd = userid_avg_rating_rdd.sortBy(lambda x: x[1], ascending=False)
# ================================
# end time 
end_time = time.time()

print("Time elapsed: \n\n", end_time - start_time)

# Print in the console the first ten users
for user in sorted_userid_avg_rating_rdd.take(10):
    print(user)

sorted_userid_avg_rating_rdd.saveAsTextFile(output_path)