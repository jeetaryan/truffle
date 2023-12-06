#! /bin/bash
backupdir="/srv/backupagent/backups/$(date +"%Y%m%d")"
tempdir="/tmp/$(date +"%Y%m%d")-software"
appdir="/var/www/login.truffle.one"
apidir="/var/www/api/api/"

mkdir $backupdir
mkdir $tempdir
mkdir $tempdir/login
cp $appdir/main* $tempdir/login
cp $appdir/services $tempdir/login/services -R
cp $appdir/templates $tempdir/login/templates -R
mkdir $tempdir/login/static
cp $appdir/static/css $tempdir/login/static/css -R
cp $appdir/static/js $tempdir/login/static/js -R
cp $appdir/static/datatables $tempdir/login/static/datatables -R
cp $appdir/static/images $tempdir/login/static/images -R

mkdir $tempdir/api
cp $apidir $tempdir/api -R

tar cfz $backupdir/software.tar.gz $tempdir
rm $tempdir -R
