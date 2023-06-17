import csv
import boto3
from datetime import datetime, timedelta

# Create an RDS client
rds_client = boto3.client('rds')

# Create a CloudWatch client
cloudwatch_client = boto3.client('cloudwatch')

# Retrieve a list of all RDS instances
response = rds_client.describe_db_instances()

# Prepare the list of instances
instances = []

# Iterate through the instances and store the details
for instance in response['DBInstances']:
    instance_id = instance['DBInstanceIdentifier']
    instance_class = instance['DBInstanceClass']
    engine = instance['Engine']
    status = instance['DBInstanceStatus']
    endpoint = instance['Endpoint']['Address']

    # Retrieve the instance name
    tags_response = rds_client.list_tags_for_resource(ResourceName=instance['DBInstanceArn'])
    instance_name = next((tag['Value'] for tag in tags_response['TagList'] if tag['Key'] == 'Name'), 'N/A')

    # Retrieve the instance type
    instance_details = rds_client.describe_db_instances(DBInstanceIdentifier=instance_id)
    instance_type = instance_details['DBInstances'][0]['DBInstanceClass']

    instances.append([instance_id, instance_name, instance_type, instance_class, engine, status, endpoint])

# Specify the output CSV file path
output_file = 'rds_instances.csv'

# Write the instances to the CSV file
with open(output_file, 'w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['Instance ID', 'Instance Name', 'Instance Type', 'Instance Class', 'Engine', 'Status', 'Endpoint'])
    writer.writerows(instances)

# Retrieve the CPU utilization metrics for the past 30 days for each instance
end_time = datetime.utcnow()
start_time = end_time - timedelta(days=30)

# Prepare the list of underutilized instances
underutilized_instances = []

for instance in instances:
    instance_id = instance[0]

    response = cloudwatch_client.get_metric_statistics(
        Namespace='AWS/RDS',
        MetricName='CPUUtilization',
        Dimensions=[
            {
                'Name': 'DBInstanceIdentifier',
                'Value': instance_id
            },
        ],
        StartTime=start_time,
        EndTime=end_time,
        Period=86400,  # One day period (24 hours x 60 minutes x 60 seconds)
        Statistics=['Average'],
    )

    # Calculate the average CPU utilization for the past 30 days
    cpu_utilization = sum(point['Average'] for point in response['Datapoints']) / len(response['Datapoints']) if response['Datapoints'] else 0

    if cpu_utilization < 10:  # Adjust the threshold as needed
        underutilized_instances.append(instance + [cpu_utilization])

# Specify the output CSV file path for underutilized instances
underutilized_output_file = 'underutilized_rds_instances.csv'

# Write the underutilized instances to the CSV file
with open(underutilized_output_file, 'w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['Instance ID', 'Instance Name', 'Instance Type', 'Instance Class', 'Engine', 'Status', 'Endpoint', 'CPU Utilization'])
    writer.writerows(underutilized_instances)

print(f"RDS instances exported to {output_file}")
print(f"Underutilized RDS instances exported to {underutilized_output_file}")
