#!/bin/bash
touch noCrossPost.txt masterMedia.txt imageLog.txt refrainlist.txt;
echo 0 > imageLog.txt
if [ "$#" -eq 0 ]; then
    echo "Please provide path to folder containing images, or provide path as an argument"
    read path
else 
path=$1
fi
sh $(pwd)/directorylist.sh $path
