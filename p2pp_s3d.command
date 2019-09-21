#!/bin/sh
DIRECTORY=`dirname $0`

chmod 755 $DIRECTORY/p2pp_s3d.py

if [ $# -eq -0 ]
then
     $DIRECTORY/p2pp_s3d.py
else
     $DIRECTORY/p2pp_s3d.py "$1"
fi