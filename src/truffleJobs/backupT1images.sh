#! /bin/bash
backupdir="/srv/backupagent/backups/$(date +"%Y%m%d")"
appdir="/var/www/login.truffle.one"

mkdir $backupdir
tar cfz $backupdir/images.tar.gz $appdir/static/*
