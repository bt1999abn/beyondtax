# Deployment Resource
```
https://testdriven.io/blog/dockerizing-django-with-postgres-gunicorn-and-nginx/
```

# In Local
```
docker-compose -f docker-compose.yml up --build
```


# In Production
```
1. Pull the latest project
2. docker-compose -f docker-compose.prod.yml up -d --build
3. docker-compose exec web python manage.py migrate
4. docker-compose exec web python manage.py collectstatic
5. docker-compose exec web python manage.py dumpdata > latest_data.json
5. docker-compose exec web python manage.py loaddata latest_data.json
```

# For Logs
```
docker-compose logs -f web
```

# GIT
```
For creating a tag 
git tag -a v1.4 -m "my version 1.4"
```

# For SSL
```
# Resource
https://medium.com/@akshatgadodia/deploying-a-django-application-with-docker-nginx-and-certbot-eaf576463f19

# To generate SSL using CertBot.

certbot certonly --manual --preferred-challenges dns --email avi@boilerPlate.com --domains live.boilerPlate.com
```

# Increasing the Volume of EC2 instance
```
1. First increase the volume in instance.
2. Chek if the volume is updated in the instance through ssh.
    * lsblk --> list block devices 
    * df -Th --> display the amount of available disk space for file systems on which the invoking user 
    has appropriate read access
3. sudo growpart /dev/xvda 1
    * Example: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/recognize-expanded-volume-linux.html
4. sudo resize2fs /dev/xvda1
5. Recheck if updated: sudo resize2fs /dev/xvda1
    
```

# Date Hierarchy
```
For date Hierarchy: https://hakibenita.medium.com/scaling-django-admin-date-hierarchy-85c8e441dd4c
```

# DB Backup
```
Resource:
https://cpcwood.com/blog/2-one-way-to-backup-a-psql-database-to-aws-s3-using-linux-cron-or-kubernetes-cronjob

# Set the crons in the crontab
sudo crontab -e

# Checking Crontab logs
grep CRON /var/log/syslog

## Save the logs to a file so that you can see the output.

```