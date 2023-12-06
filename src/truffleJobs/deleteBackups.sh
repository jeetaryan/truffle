#! /bin/bash

backupdir="/srv/backupagent/backups/"
cd $backupdir
if [ $(ls | wc -l) -gt 21 ]
then
  for D in *; do
      [ $(date -d '-90 days' +%Y%m%d) -gt $D ] && rm -rf $D
  done
fi