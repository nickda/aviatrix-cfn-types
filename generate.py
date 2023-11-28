"""
This script contains various utility functions for generating CloudFormation templates from Terraform code.
It includes functions for converting Terraform types to CloudFormation types, executing shell commands, and generating JSON schemas for CloudFormation resources.
"""
import requests
import subprocess
import os
import pprint
import json
import re
import tempfile
import time
import sys, traceback
import multiprocessing
from pathlib import Path


PROVIDERS_MAP = {
    'random': ['Random','Random'],
    'digitalocean': ['DigitalOcean','DigitalOcean'],
    'oci': ['OCI','Oracle Cloud Infrastructure'],
    'aws': ['AWS','AWS'],
    'opsgenie': ['OpsGenie','OpsGenie'],
    'dnsimple': ['DNSimple','DNSimple'],
    'vsphere': ['VSphere','VMware vSphere'],
    'consul': ['Consul','Consul'],
    'cloudstack': ['CloudStack','CloudStack'],
    'tls': ['TLS','TLS'],
    'azurerm': ['AzureRM','Azure'],
    'nomad': ['Nomad','Nomad'],
    'ovh': ['OVH','OVH'],
    'scaleway': ['Scaleway','Scaleway'],
    'bitbucket': ['Bitbucket','Bitbucket'],
    'logentries': ['Logentries','Logentries'],
    'datadog': ['Datadog','Datadog'],
    'pagerduty': ['PagerDuty','PagerDuty'],
    'ultradns': ['UltraDNS','UltraDNS'],
    'profitbricks': ['ProfitBricks','ProfitBricks'],
    'postgresql': ['PostgreSQL','PostgreSQL'],
    'google': ['Google','Google Cloud'],
    'dme': ['DME','DNSMadeEasy'],
    'triton': ['Triton','Triton'],
    'circonus': ['Circonus','Circonus'],
    'dyn': ['Dyn','Dyn'],
    'mailgun': ['Mailgun','Mailgun'],
    'influxdb': ['InfluxDB','InfluxDB'],
    'alicloud': ['Alicloud','Alicloud'],
    'grafana': ['Grafana','Grafana'],
    'rabbitmq': ['RabbitMQ','RabbitMQ'],
    'arukas': ['Arukas','Arukas'],
    'vcd': ['VCD','VMware vCloud Director'],
    'powerdns': ['PowerDNS','PowerDNS'],
    'atlas': ['Atlas','Atlas'],
    'dns': ['DNS','DNS'],
    'newrelic': ['NewRelic','NewRelic'],
    'github': ['GitHub','GitHub'],
    'librato': ['Librato','Librato'],
    'openstack': ['OpenStack','OpenStack'],
    'heroku': ['Heroku','Heroku'],
    'packet': ['Packet','Packet'],
    'clc': ['CLC','CenturyLinkCloud'],
    'template': ['Template','Template'],
    'icinga2': ['Icinga2','Icinga2'],
    'softlayer': ['SoftLayer','SoftLayer'],
    'spotinst': ['Spotinst','Spotinst'],
    'cloudflare': ['Cloudflare','Cloudflare'],
    'kubernetes': ['Kubernetes','Kubernetes'],
    'opc': ['OPC','Oracle Public Cloud'],
    'vault': ['Vault','Vault'],
    'gitlab': ['Gitlab','Gitlab'],
    'statuscake': ['StatusCake','StatusCake'],
    'local': ['Local','Local'],
    'ns1': ['NS1','NS1'],
    'fastly': ['Fastly','Fastly'],
    'docker': ['Docker','Docker'],
    'rancher': ['Rancher','Rancher'],
    'logicmonitor': ['LogicMonitor','LogicMonitor'],
    'cloudscale': ['CloudScale','CloudScale'],
    'netlify': ['Netlify','Netlify'],
    'opentelekomcloud': ['OpenTelekomCloud','OpenTelekomCloud'],
    'panos': ['Panos','Palo Alto Networks'],
    'oraclepaas': ['OraclePaaS','Oracle Cloud Platform'],
    'nsxt': ['NSXT','VMware NSX-T'],
    'runscope': ['RunScope','RunScope'],
    'flexibleengine': ['FlexibleEngine','FlexibleEngine'],
    'hcloud': ['HCloud','Hetzner Cloud'],
    'azurestack': ['AzureStack','Azure Stack'],
    'telefonicaopencloud': ['TelefonicaOpenCloud','TelefonicaOpenCloud'],
    'huaweicloud': ['HuaweiCloud','HuaweiCloud'],
    'brightbox': ['Brightbox','Brightbox'],
    'tfe': ['Tfe','Terraform Enterprise'],
    'acme': ['ACME','ACME'],
    'rightscale': ['RightScale','RightScale'],
    'bigip': ['BIGIP','F5 BIG-IP'],
    'tencentcloud': ['TencentCloud','TencentCloud'],
    'nutanix': ['Nutanix','Nutanix'],
    'linode': ['Linode','Linode'],
    'selvpc': ['SelVPC','Selectel'],
    'skytap': ['Skytap','Skytap'],
    'hedvig': ['Hedvig','Hedvig'],
    'ucloud': ['UCloud','UCloud'],
    'akamai': ['Akamai','Akamai'],
    'azuread': ['AzureAD','Azure Active Directory'],
    'ad': ['AD','Active Directory'],
    'archive': ['Archive','Archive'],
    'boundary': ['Boundary','Boundary'],
    'ciscoasa': ['CiscoASA','Cisco ASA'],
    'cloudinit': ['Cloudinit','Cloudinit'],
    'external': ['External','External'],
    'google-beta': ['GoogleBeta','Google Beta'],
    'hcp': ['HCP','HashiCorp Cloud Platform'],
    'hcs': ['HCS','HashiCorp Consul Service'],
    'helm': ['Helm','Helm'],
    'http': ['HTTP','HTTP'],
    'kubernetes-alpha': ['KubernetesAlpha','Kubernetes (Alpha)'],
    'null': ['Null','Null'],
    'terraform': ['Terraform','Terraform'],
    'time': ['Time','Time'],
    'aci': ['ACI','Cisco ACI'],
    'ah': ['AH','AdvancedHosting Cloud'],
    'aiven': ['Aiven','Aiven'],
    'alkira': ['Alkira','Alkira'],
    'amixr': ['Amixr','Amixr'],
    'anxcloud': ['Anxcloud','Anexia Cloud'],
    'artifactory': ['Artifactory','Artifactory'],
    'avi': ['AVI','AVI Networks'],
    'aviatrix': ['Aviatrix','Aviatrix'],
    'azurecaf': ['AzureCAF','Azure Cloud Adoption Framework'],
    'azuredevops': ['AzureDevOps','Azure DevOps'],
    'b2': ['B2','B2'],
    'buildkite': ['Buildkite','Buildkite'],
    'checkly': ['Checkly','Checkly'],
    'checkpoint': ['CheckPoint','Check Point'],
    'civo': ['Civo','Civo'],
    'cloudeos': ['CloudEOS','Arista CloudEOS'],
    'cloudsigma': ['CloudSigma','CloudSigma'],
    'cloudsmith': ['Cloudsmith','Cloudsmith'],
    'cloudtamerio': ['Cloudtamerio','cloudtamer.io'],
    'configcat': ['ConfigCat','ConfigCat'],
    'constellix': ['Constellix','Constellix'],
    'databricks': ['Databricks','Databricks'],
    'dcnm': ['DCNM','Cisco DCNM'],
    'dome9': ['Dome9','Dome9'],
    'dynatrace': ['Dynatrace','Dynatrace'],
    'ecl': ['ECL','NTT Enterprise Cloud 2.0'],
    'equinix': ['Equinix','Equinix'],
    'exoscale': ['Exoscale','Exoscale'],
    'fortios': ['FortiOS','FortiOS'],
    'gridscale': ['Gridscale','Gridscale'],
    'ilert': ['ILert','iLert'],
    'intersight': ['Intersight','Cisco Intersight'],
    'ionoscloud': ['IONOSCloud','IONOS Cloud'],
    'lacework': ['Lacework','Lacework'],
    'launchdarkly': ['LaunchDarkly','LaunchDarkly'],
    'limelight': ['Limelight','Limelight'],
    'logzio': ['Logzio','Logz.io'],
    'metal': ['Metal','Equinix Metal'],
    'mongodbatlas': ['MongoDBAtlas','MongoDB Atlas'],
    'mso': ['MSO','Cisco MSO'],
    'netapp-cloudmanager': ['NetAppCloudManager','NetApp Cloud Volumes ONTAP'],
    'netapp-elementsw': ['NetAppElementSW','NetApp ElementSW'],
    'netapp-gcp': ['NetAppGCP','NetApp Cloud Volumes Service for Google Cloud'],
    'nutanixkps': ['NutanixKPS','Nutanix KPS'],
    'octopusdeploy': ['OctopusDeploy','Octopus Deploy'],
    'okta': ['Okta','Okta'],
    'oktaasa': ['OktaASA','Okta ASA'],
    'onelogin': ['OneLogin','OneLogin'],
    'onepassword': ['OnePassword','1Password'],
    'oneview': ['OneView','HPE OneView'],
    'opennebula': ['OpenNebula','OpenNebula'],
    'pnap': ['PNAP','phoenixNAP'],
    'prismacloud': ['PrismaCloud','Palo Alto Networks Prisma Cloud'],
    'quorum': ['Quorum','Quorum'],
    'rancher2': ['Rancher2','Rancher v2'],
    'rediscloud': ['RedisCloud','Redis Enterprise Cloud'],
    'rke': ['RKE','Rancher Kubernetes Engine'],
    'rollbar': ['Rollbar','Rollbar'],
    'sdm': ['SDM','strongDM'],
    'sematext': ['Sematext','Sematext'],
    'signalfx': ['SignalFx','SignalFx'],
    'sigsci': ['SigSci','Signal Sciences'],
    'splunk': ['Splunk','Splunk'],
    'stackpath': ['StackPath','StackPath'],
    'sumologic': ['SumoLogic','Sumo Logic'],
    'thunder': ['Thunder','A10 Thunder'],
    'transloadit': ['Transloadit','Transloadit'],
    'turbot': ['Turbot','Turbot'],
    'upcloud': ['UpCloud','UpCloud'],
    'venafi': ['Venafi','Venafi'],
    'victorops': ['VictorOps','VictorOps'],
    'vmc': ['VMC','VMware Cloud'],
    'volterra': ['Volterra','Volterra'],
    'vra': ['VRA','VMware vRealize Automation'],
    'vra7': ['VRA7','VMware vRealize Automation 7'],
    'vultr': ['Vultr','Vultr'],
    'wavefront': ['Wavefront','Wavefront'],
    'zerotier': ['ZeroTier','ZeroTier']
}


import re

def tf_to_cfn_str(obj):
    """
    Converts a Terraform string to a CloudFormation string by converting underscores to camelCase.

    Args:
        obj (str): The Terraform string to convert.

    Returns:
        str: The CloudFormation string.
    """
    return re.sub(r'(?:^|_)(\w)', lambda x: x.group(1).upper(), obj)


def tf_type_to_cfn_type(tf_name, provider_name):
    """
    Converts a Terraform resource type name to a CloudFormation resource type name.

    Args:
        tf_name (str): The Terraform resource type name.
        provider_name (str): The name of the provider for the resource.

    Returns:
        str: The CloudFormation resource type name.
    """
    split_provider_name = tf_name.split("_")
    split_provider_name.pop(0)
    cfn_provider_name = PROVIDERS_MAP[provider_name][0]

    prefix = "TF"
    if len(sys.argv) > 2:
        prefix = sys.argv[2]

    return prefix + "::" + cfn_provider_name + "::" + tf_to_cfn_str("_".join(split_provider_name))


import subprocess

def exec_call(args, cwd):
    """
    Executes a command with arguments in a specified directory.

    Args:
        args (list): A list of command-line arguments to execute.
        cwd (str): The directory to execute the command in.

    Returns:
        bytes: The standard output of the executed command.

    Raises:
        subprocess.CalledProcessError: If the command returns a non-zero exit code.
    """
    proc = subprocess.Popen(args,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=cwd)
    stdout, stderr = proc.communicate()
    if proc.returncode != 0:
        print("Error in call:")
        raise subprocess.CalledProcessError(
            returncode=proc.returncode,
            cmd=args)
    
    return stdout


def jsonschema_type(attrtype, definitions, parentname):
    """
    Given an attribute type, generate a JSON schema for it.

    Args:
    - attrtype (str): The attribute type to generate a JSON schema for.
    - definitions (dict): A dictionary of JSON schema definitions.
    - parentname (str): The name of the parent attribute.

    Returns:
    - A tuple containing the JSON schema for the attribute type and the updated definitions dictionary.
    """
    if attrtype == "string":
        return {
            'type': 'string'
        }, definitions
    elif attrtype == "number":
        return {
            'type': 'number'
        }, definitions
    elif attrtype == "bool":
        return {
            'type': 'boolean'
        }, definitions
    elif len(attrtype) == 2 and attrtype[0] == "list":
        items, definitions = jsonschema_type(attrtype[1], definitions, parentname)
        return {
            'type': 'array',
            'insertionOrder': False,
            'items': items
        }, definitions
    elif len(attrtype) == 2 and attrtype[0] == "set":
        items, definitions = jsonschema_type(attrtype[1], definitions, parentname)
        return {
            'type': 'array',
            'insertionOrder': True,
            'items': items
        }, definitions
    elif len(attrtype) == 2 and attrtype[0] == "object":
        properties = {}
        for k,v in attrtype[1].items():
            cfnattrname = tf_to_cfn_str(k)
            properties[cfnattrname], definitions = jsonschema_type(v, definitions, parentname)

        defcount = 1
        defname = "{}Definition".format(parentname)
        while defname in definitions:
            defcount += 1
            defname = "{}Definition{}".format(parentname, defcount)

        definitions[defname] = {
            'type': 'object',
            'additionalProperties': False,
            'properties': properties
        }

        return {
            '$ref': '#/definitions/{}'.format(defname)
        }, definitions
    elif len(attrtype) == 2 and attrtype[0] == "map":
        mapvalue, definitions = jsonschema_type(attrtype[1], definitions, parentname)

        defcount = 1
        defname = "{}Definition".format(parentname)
        while defname in definitions:
            defcount += 1
            defname = "{}Definition{}".format(parentname, defcount)

        definitions[defname] = {
            'type': 'object',
            'additionalProperties': False,
            'properties': {
                'MapKey': {
                    'type': 'string'
                },
                'MapValue': mapvalue
            },
            'required': [
                'MapKey',
                'MapValue'
            ]
        }

        return {
            'type': 'array',
            'insertionOrder': True,
            'items': {
                '$ref': '#/definitions/{}'.format(defname)
            }
        }, definitions
    else:
        print("ERROR: Unknown attribute type")
        print(attrtype)
        return {
            'type': 'string'
        }, definitions


def generate_empty_override(schema, definition):
    """
    Recursively generates an empty dictionary that matches the structure of a given JSON schema definition.

    Args:
        schema (dict): The JSON schema containing the definition.
        definition (dict): The definition for which to generate an empty override.

    Returns:
        dict: An empty dictionary that matches the structure of the given definition.
    """
    ret = {}

    if '$ref' in definition:
        return generate_empty_override(schema, schema['definitions'][definition['$ref'].replace("#/definitions/", "")])

    for propname, prop in definition['properties'].items():
        if '$ref' in prop:
            ret[propname] = generate_empty_override(schema, schema['definitions'][prop['$ref'].replace("#/definitions/", "")])
        elif prop['type'] == "string":
            ret[propname] = ""
        elif prop['type'] == "number":
            ret[propname] = 1
        elif prop['type'] == "boolean":
            ret[propname] = False
        elif prop['type'] == "object":
            ret[propname] = generate_empty_override(schema, prop['properties'])
        elif prop['type'] == "array":
            if '$ref' in prop['items']:
                ret[propname] = [generate_empty_override(schema, prop['items'])]
            elif prop['items']['type'] == "string":
                ret[propname] = [""]
            elif prop['items']['type'] == "number":
                ret[propname] = [1]
            elif prop['items']['type'] == "boolean":
                ret[propname] = [False]
        else:
            print("Unknown type: " + prop['type'])

    return ret


def process_provider(provider_type):
    """
    Downloads the latest version of a Terraform provider and generates a CloudFormation equivalent for each resource in the provider.

    Args:
    provider_type (str): The name of the Terraform provider to generate CloudFormation resources for.

    Returns:
    None
    """
def process_provider(provider_type):
    tmpdir = tempfile.TemporaryDirectory()
    tempdir = Path(tmpdir.name)

    provider_data = requests.get("https://registry.terraform.io/v2/providers?filter%5Bname%5D={}&filter%5Bmoved%5D=true&filter%5Btier%5D=official%2Cpartner".format(provider_type)).json()
    if len(provider_data["data"]) == 0:
        print("Provider data not found for {}".format(provider_type))
        return

    with open(tempdir / "base.tf", "w") as f:
        f.write('''
    terraform {{
        required_providers {{
            {provider} = {{
                source = "{source}"
            }}
        }}
    }}

    provider "{provider}" {{}}
        '''.format(provider=provider_type, source=provider_data["data"][0]["attributes"]["full-name"]))

    print("Downloading latest {} provider version...".format(provider_type))
    exec_call(['terraform', 'init'], tempdir.absolute())
    tfschemadata = exec_call(['terraform', 'providers', 'schema', '-json'], tempdir.absolute())
    tfschema = json.loads(tfschemadata.decode("utf-8").strip())

    exec_call(['git', 'clone', provider_data["data"][0]["attributes"]["source"], provider_type], tempdir.absolute())

    outstandingblocks = {}
    schema = {}
    ## temporarily disabled doc generation
    doc_resources = generate_docs(tempdir, provider_type, tfschema, provider_data)

    for k,v in tfschema['provider_schemas']["registry.terraform.io/{}".format(provider_data["data"][0]["attributes"]["full-name"].lower())]['resource_schemas'].items():
        endnaming = tf_to_cfn_str(k)
        if k.startswith(provider_type + "_"):
            endnaming = tf_to_cfn_str(k[(len(provider_type)+1):])

        prefix = "TF"
        if len(sys.argv) > 2:
            prefix = sys.argv[2]
        
        cfntypename = prefix + "::" + PROVIDERS_MAP[provider_type][0] + "::" + endnaming
        cfndirname = prefix + "-" + PROVIDERS_MAP[provider_type][0] + "-" + endnaming

        try:
            providerdir = Path('.') / 'resources' / provider_type / cfndirname

            getatt = []
            allprops = []

            if not providerdir.exists():
                providerdir.mkdir(parents=True, exist_ok=True)
                exec_call(['cfn', 'init', '--type-name', cfntypename, '--artifact-type', 'RESOURCE', 'python37', '--use-docker'], providerdir.absolute())

            schema = {
                "typeName": cfntypename,
                "description": "CloudFormation equivalent of {}".format(k),
                "sourceUrl": "https://github.com/iann0036/cfn-tf-custom-types.git",
                "documentationUrl": "https://github.com/iann0036/cfn-tf-custom-types/blob/docs/resources/{}/{}/docs/README.md".format(provider_type, cfndirname),
                "definitions": {},
                "properties": {
                    "tfcfnid": {
                        "description": "Internal identifier for tracking resource changes. Do not use.",
                        "type": "string"
                    }
                },
                "additionalProperties": False,
                "required": [],
                "readOnlyProperties": [
                    "/properties/tfcfnid"
                ],
                "primaryIdentifier": [
                    "/properties/tfcfnid"
                ],
                "handlers": {
                    "create": {
                        "permissions": [
                            "s3:GetObject",
                            "s3:DeleteObject",
                            "lambda:InvokeFunction"
                        ]
                    },
                    "read": {
                        "permissions": [
                            "s3:GetObject"
                        ]
                    },
                    "update": {
                        "permissions": [
                            "s3:GetObject",
                            "s3:DeleteObject",
                            "lambda:InvokeFunction"
                        ]
                    },
                    "delete": {
                        "permissions": [
                            "s3:GetObject",
                            "s3:DeleteObject",
                            "lambda:InvokeFunction"
                        ]
                    },
                    "list": {
                        "permissions": [
                            "s3:GetObject",
                            "s3:ListBucket"
                        ]
                    }
                }
            }
            ## Temporarily disabled doc resource generation
            if k in doc_resources and len(doc_resources[k]['description']) > 10:
                schema['description'] = doc_resources[k]['description']
                if len(schema['description']) > 1023:
                    schema['description'] = schema['description'][:1020] + "..."

            if 'attributes' in v['block']:
                for attrname,attr in v['block']['attributes'].items():
                    cfnattrname = tf_to_cfn_str(attrname)
                    attrtype = attr['type']

                    allprops.append(cfnattrname + "=None")

                    computed = False
                    optional = None

                    if attrname == "id":
                        computed = True
                        #schema['primaryIdentifier'] = ["/properties/Id"]
                        schema['readOnlyProperties'].append("/properties/Id")
                        getatt.append("Id")
                    else:
                        if 'optional' in attr:
                            if not attr['optional']:
                                schema['required'].append(cfnattrname)
                                optional = False
                            else:
                                optional = True
                        elif 'required' in attr:
                            if attr['required']:
                                schema['required'].append(cfnattrname)
                        if 'computed' in attr:
                            if attr['computed']:
                                computed = True
                                if not optional:
                                    schema['readOnlyProperties'].append("/properties/" + cfnattrname)
                                    getatt.append(cfnattrname)
                        if 'sensitive' in attr:
                            if attr['sensitive']:
                                if 'writeOnlyProperties' not in schema:
                                    schema['writeOnlyProperties'] = []
                                schema['writeOnlyProperties'].append("/properties/" + cfnattrname)

                    schema['properties'][cfnattrname], schema['definitions'] = jsonschema_type(attrtype, schema['definitions'], cfnattrname)

                    if k in doc_resources:
                        for docarg in doc_resources[k]['arguments']:
                            if docarg['name'] == attrname and docarg['property_of'] is None and docarg['description']:
                                schema['properties'][cfnattrname]['description'] = docarg['description']

            if 'block_types' in v['block']:
                for blockname, block in v['block']['block_types'].items():
                    cfnblockname = tf_to_cfn_str(blockname)

                    allprops.append(tf_to_cfn_str(cfnblockname) + "=None")

                    if block['nesting_mode'] == "list":
                        schema['properties'][cfnblockname] = {
                            'type': 'array',
                            'insertionOrder': False,
                            'items': {
                                '$ref': '#/definitions/' + cfnblockname + 'Definition'
                            }
                        }
                    elif block['nesting_mode'] == "set":
                        schema['properties'][cfnblockname] = {
                            'type': 'array',
                            'insertionOrder': True,
                            'items': {
                                '$ref': '#/definitions/' + cfnblockname + 'Definition'
                            }
                        }
                    elif block['nesting_mode'] == "single":
                        schema['properties'][cfnblockname] = {
                            '$ref': '#/definitions/' + cfnblockname + 'Definition'
                        }
                    else:
                        print("Unknown nesting_mode: " + block['nesting_mode'])

                    if 'max_items' in block:
                        schema['properties'][cfnblockname]['maxItems'] = block['max_items']
                    if 'min_items' in block:
                        schema['properties'][cfnblockname]['minItems'] = block['min_items']

                outstandingblocks.update(v['block']['block_types'])
            
            while len(outstandingblocks):
                blockname = next(iter(outstandingblocks))
                block = outstandingblocks.pop(blockname)
                cfnblockname = tf_to_cfn_str(blockname)

                schema['definitions']['{}Definition'.format(cfnblockname)] = {
                    'type': 'object',
                    'additionalProperties': False,
                    'properties': {},
                    'required': []
                }

                if 'attributes' in block['block']:
                    for attrname,attr in block['block']['attributes'].items():
                        cfnattrname = tf_to_cfn_str(attrname)
                        attrtype = attr['type']

                        computed = False
                        optional = None
                        if 'optional' in attr:
                            if not attr['optional']:
                                schema['definitions']['{}Definition'.format(cfnblockname)]['required'].append(cfnattrname)
                                optional = False
                            else:
                                optional = True
                        elif 'required' in attr:
                            if attr['required']:
                                schema['definitions']['{}Definition'.format(cfnblockname)]['required'].append(cfnattrname)
                        if 'computed' in attr:
                            if attr['computed']:
                                computed = True
                                if not optional:
                                    continue # read-only props in subdefs are skipped from model
                        if 'sensitive' in attr:
                            if attr['sensitive']:
                                if 'writeOnlyProperties' not in schema:
                                    schema['writeOnlyProperties'] = []
                                schema['writeOnlyProperties'].append("/definitions/" + cfnblockname + "Definition/" + cfnattrname)

                        schema['definitions']['{}Definition'.format(cfnblockname)]['properties'][cfnattrname], schema['definitions'] = jsonschema_type(attrtype, schema['definitions'], cfnattrname)

                        if k in doc_resources:
                            for docarg in doc_resources[k]['arguments']:
                                if docarg['name'] == attrname and docarg['property_of'] == blockname and docarg['description']:
                                    schema['definitions']['{}Definition'.format(cfnblockname)]['properties'][cfnattrname]['description'] = docarg['description']
                
                if 'block_types' in block['block']:
                    outstandingblocks.update(block['block']['block_types'])
                    for subblockname,subblock in block['block']['block_types'].items():
                        cfnsubblockname = tf_to_cfn_str(subblockname)
                        if subblock['nesting_mode'] == "list":
                            schema['definitions']['{}Definition'.format(cfnblockname)]['properties'][cfnsubblockname] = {
                                'type': 'array',
                                'insertionOrder': True,
                                'items': {
                                    '$ref': '#/definitions/' + cfnsubblockname + 'Definition'
                                }
                            }
                        elif subblock['nesting_mode'] == "set":
                            schema['definitions']['{}Definition'.format(cfnblockname)]['properties'][cfnsubblockname] = {
                                'type': 'array',
                                'insertionOrder': False,
                                'items': {
                                    '$ref': '#/definitions/' + cfnsubblockname + 'Definition'
                                }
                            }
                        elif subblock['nesting_mode'] == "single":
                            schema['definitions']['{}Definition'.format(cfnblockname)]['properties'][cfnsubblockname] = {
                                '$ref': '#/definitions/' + cfnsubblockname + 'Definition'
                            }
                        else:
                            print("Unknown subblock nesting_mode: " + subblock['nesting_mode'])

                        if 'max_items' in subblock:
                            schema['definitions']['{}Definition'.format(cfnblockname)]['properties'][cfnsubblockname]['maxItems'] = subblock['max_items']
                        if 'min_items' in subblock:
                            schema['definitions']['{}Definition'.format(cfnblockname)]['properties'][cfnsubblockname]['minItems'] = subblock['min_items']

                if not bool(schema['definitions']['{}Definition'.format(cfnblockname)]['properties']):
                    if bool(block['block']):
                        del schema['definitions']['{}Definition'.format(cfnblockname)] # no properties found
                        print("Skipped propertyless block: " + cfnblockname)
                        continue
                    else:
                        schema['definitions']['{}Definition'.format(cfnblockname)]['properties']['IsPropertyDefined'] = {
                            'type': 'boolean'
                        }
                        print("Retained propertyless block: " + cfnblockname)

                # TODO: Block descriptions/max/min/etc.

            # write overrides
            override_block = {}
            for propertyname, propertyblock in schema['properties'].items():
                if '$ref' in propertyblock:
                    pass
                elif propertyblock['type'] == "array" and '$ref' in propertyblock['items']:
                    definition = schema['definitions'][propertyblock['items']['$ref'].replace("#/definitions/", "")]
                    override_block['/' + propertyname] = [
                        generate_empty_override(schema, definition)
                    ]
            overrides = {
                "CREATE": override_block,
                "UPDATE": override_block
            }
            with open(providerdir / "overrides.json", "w") as f:
                f.write(json.dumps(overrides))

            # write schema
            with open(providerdir / (cfndirname.lower() + ".json"), "w") as f:
                f.write(json.dumps(schema, indent=4))
            
            exec_call(['cfn', 'generate'], providerdir.absolute())

            # update handlers.py
            with open("handlers.py.template", "r") as handlerstemplate:
                with open(providerdir / "src" / cfndirname.lower().replace("-","_") / "handlers.py", "w") as f:
                    template = handlerstemplate.read().replace("###CFNTYPENAME###",cfntypename).replace("###TFTYPENAME###",k).replace("###PROVIDERFULLNAME###",provider_data["data"][0]["attributes"]["full-name"]).replace("###PROVIDERTYPENAME###",provider_type).replace("###GETATT###",json.dumps(getatt)).replace("###ALLPROPS###",', '.join(allprops))
                    f.write(template)

            # exec_call(['cfn', 'submit', '--dry-run'], providerdir.absolute())

            print("Generated " + cfntypename)
        except KeyboardInterrupt:
            quit()
        except:
            traceback.print_exc(file=sys.stdout)
            print("Failed to generate " + cfntypename)


# Docs
def process_resource_docs(provider_name, file_contents, provider_readme_items, provider_data):
    """
    Parses the resource documentation and returns a dictionary containing the resource type, description, example, arguments, and attributes.

    Args:
    - provider_name (str): The name of the provider.
    - file_contents (str): The contents of the file.
    - provider_readme_items (list): A list of provider readme items.
    - provider_data (dict): A dictionary containing the provider data.

    Returns:
    - dict: A dictionary containing the resource type, description, example, arguments, and attributes.
    """
    section = ""

    resource_type = ""
    description = ""
    example = ""
    arguments = []
    argument_lines = []
    attributes = {}

    lines = file_contents.split("\n")
    for line in lines:
        if line.startswith("# " + provider_name):
            resource_type = line[2:].replace("\\", "")
            section = "description"
        elif line.startswith("# Resource: " + provider_name): # aws docs differences
            resource_type = line[len("# Resource: "):].replace("\\", "")
            section = "description"
        elif line == "## Example Usage":
            section = "example"
        elif line == "## Argument Reference":
            section = "arguments"
        elif line == "## Attributes Reference":
            section = "attributes"
        elif line.startswith("##"):
            section = ""
        elif section == "description":
            description += line + "\n"
        elif section == "example":
            example += line + "\n"
        elif section == "arguments":
            argument_lines.append(line)
        elif section == "attributes":
            if line.strip().startswith("* "):
                startpos = line.strip().find("`")
                endpos = line.strip().find("`", startpos+1)
                if startpos != -1 and endpos != -1:
                    attribute_name = line.strip()[startpos+1:endpos]
                    if line.strip()[endpos+1:].strip().startswith("- ") or line.strip()[endpos+1:].strip().startswith("= "):
                        attribute_description = line.strip()[endpos+1:].strip()[2:]
                        if attribute_description[-1] != ".":
                            attribute_description += "."
                        attributes[attribute_name] = attribute_description
    
    # process arguments
    argument_names = []
    argument_block = None
    for line_number, line in enumerate(argument_lines):
        if line.strip().startswith("* ") or line.strip().startswith("- "):
            startpos = line.strip().find("`")
            endpos = line.strip().find("`", startpos+1)
            if startpos != -1 and endpos != -1:
                argument_name = line.strip()[startpos+1:endpos]
                argument_names.append(argument_name)
                if line.strip()[endpos+1:].strip().startswith("- ") or line.strip()[endpos+1:].strip().startswith("= "):
                    argument_description = line.strip()[endpos+1:].strip()[2:]

                    # concat lines in newlines for description of attribute
                    line_num_iterator = 1
                    while len(argument_lines) > line_number+line_num_iterator and (argument_lines[line_number+line_num_iterator].strip() != "" and not argument_lines[line_number+line_num_iterator].startswith("* ") and not argument_lines[line_number+line_num_iterator].startswith("#")):
                        argument_description += "\n" + argument_lines[line_number+line_num_iterator].strip()
                        line_num_iterator += 1

                    argument_attributes = []
                    argument_description = argument_description.strip()
                    if argument_description[0] == "(":
                        endbracked_index = argument_description.find(')')
                        argument_attributes = map(str.strip, argument_description[1:endbracked_index].split(","))
                        argument_description = argument_description[endbracked_index+1:].strip()

                    if argument_description and len(argument_description) > 2:
                        if argument_description[-1] != ".":
                            argument_description += "."
                    else:
                        argument_description = None
                    
                    arguments.append({
                        'name': argument_name,
                        'description': argument_description,
                        'property_of': argument_block,
                        'attributes': argument_attributes
                    })
        if line.strip().endswith(":") and argument_lines[line_number+1].strip() == "":
            for argument_name in argument_names:
                if "`{}`".format(argument_name) in line:
                    argument_block = argument_name

    if resource_type != "":
        if provider_name not in PROVIDERS_MAP:
            return
        
        description = description.strip()

        return {
            'resource_type': resource_type,
            'description': description,
            'example': example,
            'arguments': arguments,
            'attributes': attributes
        }
    
    return None


def generate_docs(tempdir, provider_type, tfschema, provider_data):
    """
    Generates documentation for a given provider.

    Args:
    - tempdir (pathlib.Path): The path to the temporary directory.
    - provider_type (str): The type of provider.
    - tfschema (dict): The Terraform schema.
    - provider_data (dict): The provider data.

    Returns:
    - ret (dict): A dictionary containing the resource properties.
    """
    resources_path = (tempdir / provider_type / "website" / "docs" / "r").absolute()
    index_path = (tempdir / provider_type / "website" / "docs" / "index.html.markdown").absolute()
    provider_reference_path = (tempdir / provider_type / "website" / "docs" / "provider_reference.html.markdown").absolute()
    provider_readme_items = []
    ret = {}

    if not os.path.isdir(resources_path):
        resources_path = (tempdir / provider_type/ "docs" / "resources").absolute()
        index_path = (tempdir / provider_type / "docs" / "index.md").absolute()
        provider_reference_path = (tempdir / provider_type / "docs" / "provider_reference.html.markdown").absolute()

    if os.path.isdir(resources_path) and provider_type in PROVIDERS_MAP:
        
        with open(Path("docs") / "{}.md".format(provider_type), 'w') as provider_readme:
            readable_provider_name = PROVIDERS_MAP[provider_type][1]
            
            # provider info
            with open(index_path, 'r') as f:
                section = ""
                first_argument_found = False
                arguments = []
                index_file_contents = f.read()
                lines = index_file_contents.split("\n")
                for line in lines:
                    if line.startswith("*") and section == "arguments":
                        first_argument_found = True
                    if line.startswith("## Argument Reference") or line.startswith("## Arguments Reference") or line.startswith("## Configuration Reference") or "the following arguments:" in line or "provide the following credentials:" in line:
                        section = "arguments"
                    elif line.startswith("#"):
                        section = ""
                    elif section == "arguments" and first_argument_found:
                        arguments.append(line)
            
            # try provider reference (eg. google)
            if len(arguments) == 0:
                try:
                    with open(provider_reference_path, 'r') as f:
                        section = ""
                        first_argument_found = False
                        arguments = []
                        index_file_contents = f.read()
                        lines = index_file_contents.split("\n")
                        for line in lines:
                            if (line.startswith("*") or line.startswith("-")) and section == "arguments":
                                first_argument_found = True
                            if line.startswith("## Argument Reference") or line.startswith("## Arguments Reference") or line.startswith("## Configuration Reference") or "the following arguments:" in line or "provide the following credentials:" in line:
                                section = "arguments"
                            elif line.startswith("#"):
                                section = ""
                            elif section == "arguments" and first_argument_found and not "navigation to the left" in line:
                                if line.startswith("-"):
                                    line[0] = "*"
                                arguments.append(line)
                except:
                    pass
            
            # remove environmental variable references
            argument_text = "\n".join(arguments)
            if provider_type not in ['digitalocean', 'fastly', 'flexibleengine', 'google', 'oneandone', 'profitbricks']:
                sentences = argument_text.split(".")
                i = 0
                while len(sentences) > i:
                    if ("environment variable" in sentences[i] or "environmental variable" in sentences[i] or "Can be sourced from" in sentences[i]):
                        del sentences[i]
                    else:
                        i+=1
                argument_text = ".".join(sentences)
            
            # replace tf references
            if provider_type in ['aws']:
                argument_text = re.sub(r"(\`%s\_.+\`)" % provider_type, lambda x: "`" + tf_type_to_cfn_type(x.group(1), provider_type), argument_text) # TODO - why only one backtick used?!?

            has_required_arguments = False
            if "required" in argument_text.lower() and provider_type not in ['aws']:
                has_required_arguments = True
            
            provider_readme.write("# {} Provider\n\n".format(readable_provider_name))
            if provider_type == "aws":
                provider_readme.write("> For the AWS provider, credentials will be inherited from the executor role, meaning you are not required to provide credentials in a configuration secret.\n\n")
            provider_readme.write("## Configuration\n\n")
            if len(arguments) == 0:
                provider_readme.write("No configuration is required for this provider.\n\n")
            elif not has_required_arguments:
                provider_readme.write("To configure this resource, you may optionally create an AWS Secrets Manager secret with the name **terraform/{}**. The below arguments may be included as the key/value or JSON properties in the secret:\n\n".format(provider_type))
                provider_readme.write(argument_text + "\n\n")
            else:
                provider_readme.write("To configure this resource, you must create an AWS Secrets Manager secret with the name **terraform/{}**. The below arguments may be included as the key/value or JSON properties in the secret:\n\n".format(provider_type))
                provider_readme.write(argument_text + "\n\n")

            # iterate provider resources
            provider_readme.write("## Supported Resources\n\n")
            provider_readme_items = []
            files = [f for f in os.listdir(resources_path) if os.path.isfile(os.path.join(resources_path, f))]
            for filename in files:
                with open(os.path.join(resources_path, filename), 'r') as f:
                    #print(filename)
                    resource_file_contents = f.read()
                    resource_properties = process_resource_docs(provider_type, resource_file_contents, provider_readme_items, provider_data)
                    if resource_properties:
                        ret[resource_properties['resource_type']] = resource_properties
            
            # provider index
            for k,v in tfschema['provider_schemas']["registry.terraform.io/{}".format(provider_data["data"][0]["attributes"]["full-name"].lower())]['resource_schemas'].items():
                split_provider_name = k.split("_")
                split_provider_name.pop(0)

                endnaming = tf_to_cfn_str(k)
                if k.startswith(provider_type + "_"):
                    endnaming = tf_to_cfn_str(k[(len(provider_type)+1):])

                prefix = "TF"
                if len(sys.argv) > 2:
                    prefix = sys.argv[2]
                
                cfn_type = prefix + "::" + PROVIDERS_MAP[provider_type][0] + "::" + endnaming
                
                provider_readme_items.append("* [{cfn_type}](../resources/{provider_name}/{type_stub}/docs/README.md)".format(
                    cfn_type=cfn_type,
                    provider_name=provider_type,
                    type_stub=tf_type_to_cfn_type(provider_type + "_" + "_".join(split_provider_name), provider_type).replace("::","-")
                ))
            
            provider_readme_items = list(set(provider_readme_items))
            provider_readme_items.sort()
            provider_readme.write("\n".join(provider_readme_items))

    else:
        with open(Path("docs") / "{}.md".format(provider_type), 'w') as provider_readme:
            readable_provider_name = PROVIDERS_MAP[provider_type][1]

            provider_readme.write("# {} Provider\n\n".format(readable_provider_name))
            provider_readme.write("## Configuration\n\n")
            provider_readme.write("Configuration items could not be determined for this provider.\n\n")

            provider_readme.write("## Supported Resources\n\n")
            provider_readme_items = []
            
            # provider index
            for k,v in tfschema['provider_schemas']["registry.terraform.io/{}".format(provider_data["data"][0]["attributes"]["full-name"].lower())]['resource_schemas'].items():
                split_provider_name = k.split("_")
                split_provider_name.pop(0)

                endnaming = tf_to_cfn_str(k)
                if k.startswith(provider_type + "_"):
                    endnaming = tf_to_cfn_str(k[(len(provider_type)+1):])

                prefix = "TF"
                if len(sys.argv) > 2:
                    prefix = sys.argv[2]
                
                cfn_type = prefix + "::" + PROVIDERS_MAP[provider_type][0] + "::" + endnaming
                
                provider_readme_items.append("* [{cfn_type}](../resources/{provider_name}/{type_stub}/docs/README.md)".format(
                    cfn_type=cfn_type,
                    provider_name=provider_type,
                    type_stub=tf_type_to_cfn_type(provider_type + "_" + "_".join(split_provider_name), provider_type).replace("::","-")
                ))

            provider_readme_items = list(set(provider_readme_items))
            provider_readme_items.sort()
            provider_readme.write("\n".join(provider_readme_items))


    return ret


def main():
    """
    This function takes in a command line argument and processes the provider(s) accordingly.
    If the argument is "all", it processes all the providers in parallel using multiprocessing.
    Otherwise, it processes the provider specified in the argument.
    """
    if sys.argv[1] == "all":
        provider_list = PROVIDERS_MAP.keys()
        with multiprocessing.Pool(multiprocessing.cpu_count()) as p: # CPU warmer :S
            list(p.imap_unordered(process_provider, provider_list))
    else:
        process_provider(sys.argv[1])


if __name__ == "__main__":
    main()