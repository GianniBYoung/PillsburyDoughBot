#!/bin/bash

# recursively creates a list of all files within a directory
function Delve
{
	#stores list of every file in the directory
	files=($(ls --format=single-column --literal))
	for file in ${files[@]}; do
	workingDirectory=$(pwd)

		# checks if the file is a directory and if so recurses
		if [ -d $file ]; then
			cd $workingDirectory/$file
			Delve
			cd ../
		else
		 echo "$workingDirectory/$file" >> /tmp/images.txt
		fi
	done
}


startingDirectory=($(pwd))
#if a directory is given as an argument, switch to it.
[[ $1 ]] && cd $1

listOfDirectory=($(ls --literal --format=single-column))

#clears images.txt 
if [ -a /tmp/images.txt ];then
	echo "">/tmp/images.txt
fi

for directory in ${listOfDirectory[@]}; do
	workingDirectory=$(pwd)
	if [ -d $directory ];then
		cd $workingDirectory/$directory
		Delve
		cd ../
	fi
done

#removes markdown and other extraneous files
grep --ignore-case --extended-regexp "\.(png|gif|jpg|pdf)$" /tmp/images.txt >/tmp/media.txt
cd $startingDirectory
# updates the masterMedia.txt file if it has already been created otherwise it creates it
if [ -a ./masterMedia.txt ];then
	diff /tmp/media.txt ./masterMedia.txt | grep "<" | tr --delete "<" >> ./masterMedia.txt
	echo "masterMedia.txt is now up to date."
else
	echo "$(</tmp/media.txt)" > ./masterMedia.txt
	echo "masterMedia.txt has been created in the project root folder."
fi
