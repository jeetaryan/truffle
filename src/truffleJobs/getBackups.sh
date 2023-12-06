#! /bin/bash

# Collect list of files
cd /home/ec2-user/backups
files=`sftp -b - -P 55417 -oIdentityFile=/home/ec2-user/truffle-backupagent backupagent@141.95.104.51 <<EOF
cd /backups
ls
EOF`
files=`echo $files|sed "s/.*sftp> ls//"` 

# Use the list to generate list of commands for the second run
(
  echo cd /backups
  for file in $files; do
    echo get -R -a $file
  done
) | sftp -b - -P 55417 -oIdentityFile=/home/ec2-user/truffle-backupagent backupagent@141.95.104.51
cd /home/ec2-user

#delete old backups
backupdir="/home/ec2-user/backups"
cd $backupdir
if [ $(ls | wc -l) -gt 21 ]
then
  for D in *; do
      [ $(date -d '-90 days' +%Y%m%d) -gt $D ] && rm -rf $D
  done
fi