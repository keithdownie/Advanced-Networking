#!/bin/bash
if [ -z "$1" ]; then
	NAME="R4"
else
	NAME=$1
fi
if [ -z "$2" ]; then
	NET1="net11"
else
	NET1=$2
fi
if [ -z "$3" ]; then
	NET2="net12"
else
	NET2=$3
fi
if [ -z "$4" ]; then
	MULTI="True"
else
	MULTI=$4
fi
python newInstance.py $NAME $NET1 $NET2 $MULTI
