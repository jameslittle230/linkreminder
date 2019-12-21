import boto3


def uploadFile(localPath, remotePath, bucket):
    s3 = boto3.resource('s3')

    s3.Bucket(bucket).upload_file(localPath, remotePath, ExtraArgs={
        'ContentType': 'text/html',
    })
