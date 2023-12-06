#! /bin/bash
backupdir="/srv/backupagent/backups/$(date +"%Y%m%d")"
tempdir="/tmp/$(date +"%Y%m%d")-db"


mkdir $backupdir
mkdir $tempdir
mysqldump truffle -utruffle -panothertry > $tempdir/db-full.sql
tar cfz $backupdir/db-full.tar.gz $tempdir/db-full.sql
rm $tempdir -R
