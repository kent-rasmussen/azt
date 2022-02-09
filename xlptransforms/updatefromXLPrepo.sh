#!/bin/bash
#This script checks that the hardlinks between this directory and the source on my computer (from the XLP git repo, with my modifications) are intact.
#If they are not, it removes the file here, and links it again, to keep this up to date with the XLP repo.
#In case I've forgotten, that repo is kept up to date by 
#	cd /home/kentr/.xxe7/addon/XLingPap/
#	git checkout XXE7.3
#	git pull
#	git checkout XXE7.3_KARmods
#	git rebase XXE7.3

thisfolder="${HOME}/IT/azt/repo_stable/xlptransforms"
repo="${HOME}/.xxe7/addon/XLingPap"
#These are subdirectories of the above XLP repo; we don't need everything
xlptransforms="${repo}/transforms"
xlpdtds="${repo}/dtds"
xlpbatchfiles="${repo}/batchfiles"
xlpjava="${repo}/javasrc/XLingPapExtensions/src/xlingpaper/xxe/"

cd ${repo}
echo "Fetching XLP remote repository (takes internet time/bandwidth)"
git fetch
#git diff --exit-code XXE7.3 remotes/origin/XXE7.3
#ech $bob
#echo $?
if ! `git diff --exit-code XXE7.3 remotes/origin/XXE7.3` ;then
echo "If you see XXE7.3 in the above, there are updates to the remote XLP repo; incorporate those first!"
exit
fi
cd - &>/dev/null

cd ${thisfolder}
echo "I'm going to need your sudo password here, to avoid a lot of extra permissions output on find."
for file in * 
do 
locations=`sudo find ${HOME} -samefile ${file}` #gimme each location of the *same* file.
if grep -q "${xlptransforms}\|${xlpdtds}\|${xlpbatchfiles}\|${xlpjava}" <<< ${locations}
then echo "${file} OK!"
else #echo "local copy (of ${file}) not found in repo!"
	case ${file} in
		*'.xsl') rm ${file}; ln ${xlptransforms}/${file};;
		*'.dtd') rm ${file}; ln ${xlpdtds}/${file};;
		*'.java') rm ${file}; ln ${xlpjava}/${file};;
		*'PDF'{,.bat}) echo ${file};;# ln ${xlptransforms}/${file};;
		*) echo "${file} not a a repo file; not being updated";;
	esac
fi

done
cd - &>/dev/null

