# Intro

We would like to build a system similar to how Terraform works: there is a config file that defines
the current state of the system, and there is a new config file that defines the new desired state
of the system. We need to calculate the difference between these two states so that we can generate
appropriate commands that we can execute to move the system from the current state to the new one.

## Assignment

Write a Python script that takes two yaml configuration files, calculates the difference between them,
and prints the results.

There are three sample config files provided. Please produce the following output:

`config_file_1.yaml` vs `config_file_2.yaml`  
`config_file_2.yaml` vs `config_file_3.yaml`  
`config_file_1.yaml` vs `config_file_3.yaml`  

### Rules

1. You need to parse the config file and compare the defined objects, not a text comparison of the files  
2. You can only use Yaml parsing library and Python standard libraries, not third-part diffing libraries

### ⚠️ Simplification

It's hard to compare arbitrary lists and account for added, removed, reordered, or modified items.
In order to simplify list comparison we're going to introduce these simplification rules:

1. All list elements are dictionaries - no lists of scalars, or lists of lists, all elements have fields
2. All elements in a list have a unique key, the first field in the element is the unique key field
3. The unique key field is the same for all element in the same list, but not across lists
4. Order of elements in the list is not important

In this example `name` is the unique key field of `containers` since it's the first field in the object.
All containers in this list will have the `name` field as their first field.

```yaml
  containers:
  - name: nginx
    image: nginx:1.14.2
```

### Bonus points

- Bonus points if you use virtual environment
- Bonus points if you use a package manager
- Bonus points if you write pytest unit tests to execute the comparison

## Sample output

Sample output for your reference, your output doesn't have to match this format exactly
as long as the results are correct:

```text
Comparing files 'config_file_1.yaml' and 'config_file_2.yaml

The following items were removed:
.spec.template.spec.containers[nginx].env[DISCOVERY_SERVICE]:
  name: DISCOVERY_SERVICE
  value: loc.example.com

The following items were added:
.spec.template.spec.containers[nginx].env[MESSAGE_BROKER_HOST]:
  name: MESSAGE_BROKER_HOST
  value: kfk1.example.com

The following items were changed:
.spec.replicas:
  old value: 1
  new value: 3
.spec.template.spec.containers[nginx].env[DATABASE_HOST].value:
  old value: db1.example.com
  new value: db2.example.com
.spec.template.spec.containers[nginx].image:
  old value: nginx:1.14.2
  new value: nginx:1.16.3
```
