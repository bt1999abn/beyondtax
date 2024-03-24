#! /bin/sh
# PSQL Database Backup to AWS S3

echo "Starting PSQL Database Backup..."

# Ensure all required environment variables are present
if [ -z "$POSTGRES_PASSWORD" ] || \
    [ -z "$POSTGRES_USER" ] || \
    [ -z "$POSTGRES_HOST" ] || \
    [ -z "$POSTGRES_DB" ] || \
    [ -z "$AWS_ACCESS_KEY_ID" ] || \
    [ -z "$AWS_SECRET_ACCESS_KEY" ] || \
    [ -z "$AWS_DEFAULT_REGION" ] || \
    [ -z "$S3_BUCKET" ]; then
    >&2 echo 'Required variable unset, database backup failed'
    exit 1
fi


# Set variables
DB_CONTAINER_NAME="bookmythinnai_db_1"
BACKUP_DIR=$(mktemp -d)
DATE=$(date +%d'-'%m'-'%Y'--'%H'-'%M'-'%S)
FILENAME="backup_$DATE.sql"
BACKUP_PATH=$BACKUP_DIR/$FILENAME

# Backup the database
docker exec $DB_CONTAINER_NAME pg_dump -U $POSTGRES_USER $POSTGRES_DB > $BACKUP_PATH

# Compress the backup
gzip $BACKUP_PATH

BACKUP_PATH="$BACKUP_PATH.gz"
# Check backup created
if [ ! -e "$BACKUP_PATH" ]; then
    echo 'Backup file not found'
    exit 1
fi

# Push backup to S3
aws s3 cp "$BACKUP_PATH" "s3://$S3_BUCKET"
status=$?

# Remove tmp backup path
rm -rf "$BACKUP_DIR"

# Indicate if backup was successful
if [ $status -eq 0 ]; then
    echo "PSQL database backup: '$FILENAME' completed to '$S3_BUCKET'"

    # Remove expired backups from S3
    if [ "$ROTATION_PERIOD" != "" ]; then
        aws s3 ls "$S3_BUCKET" --recursive | while read -r line;  do
            stringdate=$(echo "$line" | awk '{print $1" "$2}')
            filedate=$(date -d"$stringdate" +%s)
            olderthan=$(date -d"-$ROTATION_PERIOD days" +%s)
            if [ "$filedate" -lt "$olderthan" ]; then
                filetoremove=$(echo "$line" | awk '{$1=$2=$3=""; print $0}' | sed 's/^[ \t]*//')
                if [ "$filetoremove" != "" ]; then
                    aws s3 rm "s3://$S3_BUCKET/$filetoremove"
                fi
            fi
        done
    fi
else
    echo "PSQL database backup: '$FILENAME' failed"
    exit 1
fi
