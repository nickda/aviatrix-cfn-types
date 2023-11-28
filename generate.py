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
import re
from pathlib import Path

provider_avx = 'Aviatrix'

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

    prefix = "TF"
    if len(sys.argv) > 2:
        prefix = sys.argv[2]

    return prefix + "::" + provider_avx + "::" + tf_to_cfn_str("_".join(split_provider_name))


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
    Downloads the latest version of Aviatrix Terraform provider and generates a CloudFormation equivalent for each resource in the provider.

    Args:
    provider_type (str): The name of the Terraform provider to generate CloudFormation resources for.

    Returns:
    None
    """
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
    
    doc_resources = generate_docs(tempdir, provider_type, tfschema, provider_data)

    for k,v in tfschema['provider_schemas']["registry.terraform.io/{}".format(provider_data["data"][0]["attributes"]["full-name"].lower())]['resource_schemas'].items():
        endnaming = tf_to_cfn_str(k)
        if k.startswith(provider_type + "_"):
            endnaming = tf_to_cfn_str(k[(len(provider_type)+1):])

        prefix = "TF"
        if len(sys.argv) > 2:
            prefix = sys.argv[2]
        
        cfntypename = prefix + "::" + provider_avx + "::" + endnaming
        cfndirname = prefix + "-" + provider_avx + "-" + endnaming

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
                "sourceUrl": "https://github.com/nickda/aviatrix-cfn-types.git",
                "documentationUrl": "https://github.com/nickda/aviatrix-cfn-types/blob/docs/resources/{}/{}/docs/README.md".format(provider_type, cfndirname),
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
        elif line.startswith("# Resource: " + provider_name):
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
        # if provider_name not in PROVIDERS_MAP:
        #     return
        
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
    Generates documentation for the Aviatrix provider.

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

    if os.path.isdir(resources_path):
        os.makedirs("aviatrix_provider_docs", exist_ok=True)
        with open(Path("aviatrix_provider_docs") / "README.md".format(provider_type), 'w') as provider_readme:
            readable_provider_name = provider_avx
            
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
            

            provider_readme.write("# Aviatrix Provider\n\n")
            
            provider_readme.write("## Configuration\n\n")
            provider_readme.write("To configure this resource, you must create an AWS Secrets Manager secret with the name `aviatrix_secret`. The following arguments have to be included as the key/value or JSON properties in the secret:\n\n")
            provider_readme.write("| Argument | Description |\n")
            provider_readme.write("| --- | --- |\n")
            provider_readme.write("| `controller_ip` | The IP address of the Aviatrix controller |\n")
            provider_readme.write("| `password` | The password of the `admin` user |\n")

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
                
                cfn_type = prefix + "::" + provider_avx + "::" + endnaming
                
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
            readable_provider_name = provider_avx

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
                
                cfn_type = prefix + "::" + provider_avx + "::" + endnaming
                
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
    process_provider("aviatrix")

if __name__ == "__main__":
    main()