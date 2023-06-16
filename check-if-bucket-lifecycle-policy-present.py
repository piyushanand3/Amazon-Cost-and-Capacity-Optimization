import boto3
import botocore
# Get the list of all S3 buckets
buckets = boto3.client('s3').list_buckets()['Buckets']

# Create a list to store the buckets with lifecycle policies
lifecycle_buckets = []

# Create a list to store the buckets without lifecycle policies
no_lifecycle_buckets = []

# Iterate through the list of buckets
for bucket in buckets:

    # Try to get the lifecycle configuration for the bucket
    try:
        lifecycle_config = boto3.client('s3').get_bucket_lifecycle(Bucket=bucket['Name'])

        # If the bucket has a lifecycle configuration
        if lifecycle_config['Rules']:

            # Add the bucket to the list of buckets with lifecycle policies
            lifecycle_buckets.append(bucket['Name'])

        # Otherwise, the bucket does not have a lifecycle configuration
        else:

            # Add the bucket to the list of buckets without lifecycle policies
            no_lifecycle_buckets.append(bucket['Name'])

    # If an error occurs when trying to get the lifecycle configuration
    except botocore.exceptions.ClientError as e:

        # If the error is that the bucket does not have a lifecycle configuration
        if e.response['Error']['Code'] == 'NoSuchLifecycleConfiguration':

            # Add the bucket to the list of buckets without lifecycle policies
            no_lifecycle_buckets.append(bucket['Name'])

# Print the list of buckets with lifecycle policies
print('Buckets with lifecycle policies:')
for bucket in lifecycle_buckets:
    print(bucket)

# Print the list of buckets without lifecycle policies
print('Buckets without lifecycle policies:')
for bucket in no_lifecycle_buckets:
    print(bucket)