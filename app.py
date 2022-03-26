from botocore.exceptions import ClientError
import base64
from flask import Flask, request, render_template
import boto3
import json
import pymysql

app = Flask(__name__)

aws_access_key_id = 'ASIAQOVBD7GJVCD6PEVL'
aws_secret_access_key = 'u7Psk5mGCajlPSMAkfnIK37QTXSzzq737RbseQID'
aws_session_token = 'FwoGZXIvYXdzEB8aDMzFE2YHWyagZyYd1yLAAYrgN0wAy9+Fo9uSOHzNhupLwVmyvacVlRixzJzv6ZoCYXVbZ4NODSJiq/mDYiCoGo4fDffejB9ZGom3xJub1oA/lWbOOYRhLuIx4L6ifzXAmqsYRBHhbALgGO3Puj7uwT5YTbWHnSJIKkNHT4wAwxhQPnmcpsgXqWMBJxsd84jYHIRWUgspoUGAvfA3hGLIUk5XdWuyXAbcAyN/EremX68wmi0MBbvZsGmEs87GSGduiscKDSd/jEQLXMRNXTo9YSiomv6RBjItfpVUzQ6h8sJylDs6NRqRGbFReF+CmhwkYa6BUZeEKnQvKCNh4gI8RVSYe2nH'

# Modified sample code from AWS Secrets Manager


def get_rds_secret():
    secret_name = "arn:aws:secretsmanager:us-east-1:031476414867:secret:ProductionDB-PSWOfg"
    region_name = "us-east-1"

    # Create a Secrets Manager client
    session = boto3.session.Session(aws_access_key_id=aws_access_key_id,
                                    aws_secret_access_key=aws_secret_access_key, aws_session_token=aws_session_token)
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        if e.response['Error']['Code'] == 'DecryptionFailureException':
            raise e
        elif e.response['Error']['Code'] == 'InternalServiceErrorException':
            raise e
        elif e.response['Error']['Code'] == 'InvalidParameterException':
            raise e
        elif e.response['Error']['Code'] == 'InvalidRequestException':
            raise e
        elif e.response['Error']['Code'] == 'ResourceNotFoundException':
            raise e
    else:
        if 'SecretString' in get_secret_value_response:
            secret = get_secret_value_response['SecretString']
            return secret
        else:
            decoded_binary_secret = base64.b64decode(
                get_secret_value_response['SecretBinary'])
            return decoded_binary_secret

# Connect to RDS MySQL Database and return database cursor


def get_db_instance():
    # Get RDS Secrets in from above method and loading json in dictionary
    secrets_dict = json.loads(get_rds_secret())
    mydb = pymysql.connect(
        host=secrets_dict['host'], user=secrets_dict['username'], password=secrets_dict['password'], database=secrets_dict['dbname'])
    return mydb, mydb.cursor()

# EC2 Endpoint to store students' data in RDS


@app.route('/storestudents', methods=['POST'])
def storestudents():
    # Getting a data from post request
    students = request.json.get('students')
    updated_row = 0
    for student in students:
        first_name = student['first_name']
        last_name = student['last_name']
        banner = student['banner']
        sql_query = "INSERT INTO students (first_name, last_name, banner) VALUES (%s, %s, %s)"
        values = (first_name, last_name, banner)
        mydb, mycursor = get_db_instance()
        mycursor.execute(sql_query, values)
        mydb.commit()
        if mycursor.rowcount > 0:
            updated_row += 1
    if updated_row > 0:
        return " rows are entered into RDS Database", 200
    else:
        return "Data is not inserted into RDS Database", 400

# EC2 Endpoint to show students' data on HTML


@app.route('/liststudents', methods=['GET'])
def liststudents():
    sql_query = "SELECT * FROM students"
    mydb, mycursor = get_db_instance()
    mycursor.execute(sql_query)
    students = mycursor.fetchall()
    students_dict_list = []
    for student in students:
        # Set to list
        student = list(student)
        first_name = student[0]
        last_name = student[1]
        banner = student[2]
        student_dict = {"first_name": first_name,
                        "last_name": last_name, "banner": banner}
        students_dict_list.append(student_dict)
    return render_template('liststudents.html', students=students_dict_list)


if __name__ == "__main__":
    app.run(debug=True)
