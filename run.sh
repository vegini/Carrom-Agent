#!/bin/bash

for i in $(seq $1 $2)
do
	python start_experiment.py -rs $i | grep "Cleared Board in *" > out.txt
done
# awk -f "BEGIN{sum = 0; count = 0;} {sum = sum + $3; count++;} END{print(sum/count)}"

awk 'BEGIN{sum = 0; count = 0;} { sum += $4 } END { print sum/NR }' out.txt