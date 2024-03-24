import os

from beyondTax.settings.base import BASE_DIR, env


USE_S3 = env.bool('USE_S3', False)

if USE_S3:
    # aws settings
    AWS_ACCESS_KEY_ID = env('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = env('AWS_STORAGE_BUCKET_NAME')
    AWS_DEFAULT_ACL = 'public-read'
    AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
    AWS_S3_OBJECT_PARAMETERS = {'CacheControl': 'max-age=86400'}

    # s3 static settings
    AWS_STATIC_LOCATION = 'static'
    AWS_LOCATION = 'static'
    STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/{AWS_LOCATION}/'
    STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

    # Media
    AWS_MEDIA_FILES_LOCATION = 'media'
    AWS_PUBLIC_MEDIA_LOCATION = env('AWS_PUBLIC_MEDIA_LOCATION')
    AWS_PRIVATE_MEDIA_LOCATION = env('AWS_PRIVATE_MEDIA_LOCATION')

    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/{AWS_MEDIA_FILES_LOCATION}/'
    DEFAULT_FILE_STORAGE = 'beyondTax.storage.backends.PublicMediaStorage'
    PRIVATE_FILE_STORAGE = 'beyondTax.storage.backends.PrivateMediaStorage'

    # DB BACKUP
    DBBACKUP_STORAGE = STATICFILES_STORAGE
    DBBACKUP_STORAGE_OPTIONS = {
        'access_key': AWS_ACCESS_KEY_ID,
        'secret_key': AWS_SECRET_ACCESS_KEY,
        'bucket_name': AWS_STORAGE_BUCKET_NAME,
        'default_acl': 'private',
        'location': 'db_backup/'
    }
    DBBACKUP_ADMINS = ["omkar.thouta0231@gmail.com"]

else:
    STATIC_URL = '/static/'
    STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
    MEDIA_URL = '/media/'
