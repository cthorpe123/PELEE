#!/bin/bash

# Script for hadding together ntuple files based on a sam definition
# Author: C Thorpe (U of Manchester)
#
# Prestages files so best run inside nohup (or screen):
# Usage: nohup ./hadd_ntuple.sh <samdef> >& hadd_<samdef>.log &

cleanup=false
skip_prestage=true
drop_weights=true
prestage_fraction=0.98

########################################################################
# Function to make a list of locations of staged files
make_list_staged_files(){

def=$1
samweb list-files defname:$def > files_${def}.list

# remove the old list of file locations
rm file_locations_${def}.log

while read -r line; do

    loc=$(samweb locate-file $line)

    if [[ "$(echo "$loc" | grep "dcache")" == "dcache:"* ]]; then
        #echo "File on dcache"
        loc=$(echo "$loc" | grep "dcache" | sed 's/dcache://g')
    elif [[ "$(echo "$loc" | grep "enstore")" == "enstore:"* ]]; then
        #echo "File on enstore"
        loc=$(echo "$loc" | grep "enstore" | sed 's/enstore://g')
    fi

    loc=$(echo "${loc}" | sed 's/([^()]*)//g') 
    loc=${loc}/
    status=$(cat ${loc}".(get)(${line})(locality)")

    if [[ "$status" == *"ONLINE"* ]]; then 
        #echo "Found a file"
        echo ${loc}${line} >> file_locations_${def}.log
    fi

done < files_${def}.list

}

########################################################################

def=$1
echo "Hadding files for sam def ${def}"

########################################################################
# Prestage the input def first

samweb list-files defname:$def > files_${def}.list

if [ $skip_prestage == false ]; then

    nohup samweb prestage-dataset --defname=${def} --parallel=4 >& prestage_${def}.log &

    files=$(samweb count-files defname:${def}) 
    files_to_stage=$(bc -l <<< "${files}*${prestage_fraction}")

    files_staged=0
    while (( $(echo "${files_staged} < ${files_to_stage}" | bc -l) )); do
        echo "Staged ${files_staged} of ${files}, target is ${files_to_stage}"
        sleep 60m
        make_list_staged_files $def
        files_staged=$(wc -l file_locations_${def}.log | awk '{ print $1}')
    done

    sam_project=$(cat prestage_${def}.log | grep 'Started project' | awk '{ print $3}') 
    samweb stop-project $sam_project

    echo "Prestaged ${files_staged} of ${files}"
    echo "Finished prestaging definition"

fi

########################################################################
# Make a fullpath list of the files


#samweb list-file-locations --defname=${def} > file_locations_${def}.log
#sed -i 's/\.root.*/\.root/g' file_locations_${def}.log
#sed -i 's/enstore://g' file_locations_${def}.log
#sed -i 's/\s\+/\//g' file_locations_${def}.log
#exit
#grep -v '^dcache' file_locations_${def}.log > tmp_file_locations_${def}.log
#mv tmp_file_locations_${def}.log file_locations_${def}.log
#sed -i 's/^dcache/d' file_locations_${def}.og

if [ $skip_prestage == true ]; then
    make_list_staged_files $def
fi

echo "Done making list of file locations"

########################################################################
# Convert the file list to xrootd format

while IFS= read -r line; do
  output=$(pnfsToXRootD "$line")
  echo "$output" >> "xrootd_locations_${def}.log"
done < "file_locations_${def}.log"

echo "Converted file locations to xrootd"

########################################################################
# Hadd together the xrood files


files=$(wc -l xrootd_locations_${def}.log | awk '{ print $1 }')

if [ 5000 -gt $files ]; then
  onelinefilelist=$(cat xrootd_locations_${def}.log | tr \\n ' ')
  hadd -f ${def}.root ${onelinefilelist}
  if [ $drop_weights == true ]; then
root -b -l <<EOF
.L drop_weights.C
drop_weights("${def}.root");
EOF
    mv noweights/${def}.root ${def}.root  
  fi 
else 
  # Alternative method for hadding ntuples for large definitions Split the 
  # file list into groups of files, hadd each group, then merge the results together 
  i=1
  ctr=0
  pieces=""
  group=1000
  while [ $files -gt $i ]; do
    onelinefilelist=$(sed -n $i,$((i+group-1))p xrootd_locations_${def}.log | tr \\n ' ')
    hadd -f ${def}_pt${ctr}.root ${onelinefilelist} 
    if [ $drop_weights == true ]; then
root -b -l <<EOF
.L drop_weights.C
drop_weights("${def}_pt${ctr}.root");
EOF
        mv noweights/${def}_pt${ctr}.root ${def}_pt${ctr}.root  
    fi 
    pieces=$(echo $pieces ${def}_pt${ctr}.root)
    i=$((i+group))
    ctr=$((ctr+1))
  done

  hadd -f ${def}.root $pieces
  #rm ${def}_pt*.root

fi

########################################################################
# Remove temp files/logs

if [ $cleanup == true ]; then
    rm file_locations_${def}.log
    rm xrootd_locations_${def}.log
    rm prestage_${def}.log 
    rm files_${def}.list
    rm ${def}_pt*.root
    rm 
fi

########################################################################
# Check how many events are in the sam def versus how many are in the 
# hadded root file

echo
root -b ${def}.root <<EOF
nuselection->cd()
NeutrinoSelectionFilter->GetEntries()
EOF

samweb list-files --summary defname:${def}
echo

########################################################################

echo "Finished!"


