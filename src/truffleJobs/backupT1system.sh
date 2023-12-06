#! /bin/bash
backupdir="/srv/backupagent/backups/$(date +"%Y%m%d")"
tempdir="/tmp/$(date +"%Y%m%d")-system"

mkdir $backupdir
mkdir $tempdir
mkdir $tempdir/etc

sudo cp /etc/apache2 $tempdir/etc/apache2 -R
sudo cp /etc/mysql $tempdir/etc/mysql -R

sudo pip list > $tempdir/pip-list.out
crontab -l > $tempdir/crontab-l.out

sudo tar cfz $backupdir/system.tar.gz $tempdir
sudo rm $tempdir -R
