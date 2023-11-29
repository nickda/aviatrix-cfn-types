# Custom Cloudformation Resource Types for Aviatrix

<!-- TOC start  -->
- [1. Deploy the execution environment](#1-deploy-the-execution-environment)
- [2. Install the prerequisites](#2-install-the-prerequisites)
- [3. Pull and run the Lambda Python image in Docker](#3-pull-and-run-the-lambda-python-image-in-docker)
- [4. Generate the Aviatrix resources and provider documentation](#4-generate-the-aviatrix-resources-and-provider-documentation)
- [5. Submit the resources to AWS Cloudformation](#5-submit-the-resources-to-cloudformation)
- [6. Configuring Aviatrix Controller IP address and credentials](#6-configuring-aviatrix-controller-ip-address-and-credentials)
- [7. Deploy resources by creating a Cloudformation template](#7-deploy-resources-by-creating-a-cloudformation-template)

<!-- TOC end -->

<!-- TOC --><a name="1-deploy-the-execution-environment"></a>

## 1. Deploy the execution environment

Start by deploying the execution environment from [template.yml](https://github.com/nickda/aviatrix-cfn-types/blob/main/template.yml) to Cloudformation.
>[!IMPORTANT] 
> Ensure you select the correct region in the AWS Console or AWS CLI.

![CleanShot 2023-11-28 at 17 17 09](https://github.com/nickda/aviatrix-cfn-types/assets/10653195/41ccf740-d5d1-41e9-a251-2a80e5cd6bfd)

### Architecture Components

**Terraform State S3 Bucket:** An Amazon S3 bucket stores the Terraform state files. This state bucket is crucial for Terraform to track the state of resources and for ensuring idempotency in infrastructure provisioning.

**Executor Lambda Function:** The core of the setup is the Executor Lambda Function, which is triggered by the creation, modification, or deletion of CloudFormation resources. The Lambda function executes Terraform code against the Aviatrix Controller API. This automation enables the management of the Aviatrix Platform's resources via Terraform while using CloudFormation as the orchestration tool.

**ExecutorLambdaServiceRole:** This IAM role authorizes the Executor Lambda Function to interact with other AWS services. It has policies granting permissions to manage Terraform state in the S3 bucket and access secrets from the AWS Secrets Manager.

**CloudWatch Logs:** Utilized for logging and troubleshooting, CloudWatch Logs store the output of the Executor Lambda Function, providing insights into the execution process and facilitating error analysis. The log group is configured with a retention policy of 14 days, ensuring logs are stored for an adequate period for review and compliance.

**AWS Secrets Manager:** AWS Secrets Manager is employed to manage sensitive information such as the Aviatrix Controller credentials. It securely stores and retrieves database credentials, API keys, and other secrets the Lambda function needs.

### Security and Compliance

Security is a paramount aspect of this architecture. The Terraform state bucket is encrypted using AES-256 encryption, and public access is blocked to protect state files. CloudWatch Logs are secured by IAM roles, allowing only authorized entities to access log data. The AWS Secrets Manager secures sensitive data, ensuring that the Lambda function can securely access necessary credentials without exposing them in the code or logs.

### Operational Flow

The operational flow begins with a change in the CloudFormation stack, which triggers the Executor Lambda Function. The Lambda function runs Terraform commands to create, update, or delete resources in the Aviatrix Platform as the Terraform code specifies. The function also interacts with the S3 bucket to retrieve and update the Terraform state. Logs generated during this process are sent to CloudWatch for monitoring and troubleshooting.

<!-- TOC --><a name="2-install-the-prerequisites"></a>

## 2. Install the prerequisites

The following prerequisites are required to generate Cloudformation resource types from Aviatrix Terraform provider:

- Python 3
- Git
- Docker
- Terraform 1.0+
- CloudFormation CLI with Python Plugin

### Example of installation on the Amazon Linux

```sh
## Clone this repository to a local directory
git clone git@github.com:nickda/aviatrix-cfn-types.git
cd ./aviatrix-cfn-types

## Install the prerequisites
sudo yum update
sudo yum install python3
sudo yum install git
sudo yum install docker
sudo service docker start
sudo usermod -a -G docker ec2-user
sudo yum install unzip
sudo yum-config-manager --add-repo https://rpm.releases.hashicorp.com/AmazonLinux/hashicorp.repo
sudo yum -y install terraform
sudo yum install python3-pip
pip3 install virtualenv

## Create the virtual environment and install and Cloudformation CLI and Python plugin into it
virtualenv venv
source venv/bin/activate
pip3 install cloudformation-cli
cfn --version
pip3 install cloudformation-cli cloudformation-cli-python-plugin

## Update AWS CLI to the latest version
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

## Configure AWS credentials and the region to which the Cloudformation resources will be registered
aws configure
```

<!-- TOC --><a name="3-pull-and-run-the-lambda-python-image-in-docker"></a>

## 3. Pull and Run the Lambda Python Image in Docker

```sh
docker pull public.ecr.aws/lambda/python:3.9
docker run -d -p 9000:8080 public.ecr.aws/lambda/python:3.9 app
```

<!-- TOC --><a name="4-generate-the-aviatrix-resources-and-provider-documentation"></a>

## 4. Generate the Aviatrix resources and documentation

To generate resources based on the latest version of Terraform provider:

```sh
python3 generate.py
```

<!-- TOC --><a name="5-submit-the-resources-to-cloudformation"></a>

## 5. Submit the resources to AWS Cloudformation

> [!CAUTION]
> By default, AWS imposes a limit of 50 custom resources per account per region. You can open a support case with AWS to increase the limit.

To submit resources one at a time:

```sh
python3 submit <resource-name>
```

e.g.,

```sh
python3 submit TF::Aviatrix::Account
```

To submit all generated resource types (in the `resources` folder) in bulk:

```sh
python3 submit-all.py
```

> [!NOTE]
> If you'd like to submit only a subset of resource types, delete the directories with the types you won't need from the `resources` directory before running the `submit-all.py` script.

<!-- TOC --><a name="6-configuring-aviatrix-controller-ip-address-and-credentials"></a>

## 6. Configuring Aviatrix Controller IP address and credentials

To configure this resource, you must create an AWS Secrets Manager secret named `aviatrix_secret`.

The following arguments must be included as the key/value or JSON properties in the secret:

| Argument | Description |
| --- | --- |
| `controller_ip` | The IP address of the Aviatrix controller |
| `password` | The password of the `admin` user |

<!-- TOC --><a name="7-deploy-resources-by-creating-a-cloudformation-template"></a>

## 7. Deploy resources by creating a Cloudformation template

You can find an example of Controller configuration and network infrastructure deployment template in the [cfn_template_examples](https://github.com/nickda/aviatrix-cfn-types/tree/main/cfn_template_examples) directory.


## 8. (Optional) De-registering the resource types from AWS Cloudformation
If you require to deregister the resource types submitted to AWS Cloudformation you can run the following command:

```sh
python3 deregister-all.py
```

This will remove all custom Cloudformation resources submitted in step 5.
