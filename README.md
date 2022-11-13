# bqm2

## What is bqm2?

bqm2 stands for BigQuery Materializer 2.   In short, it allows you to
- write queries
- save them as files
- execute those queries in the correct order
- and save the results of each query in datasets and tables of your choosing.
- change those queries and re-run and only re-execute that query AND any of its dependants.

# Requirements
- Google project and access to bigquery and preferably cloud storage
- Docker or equivalent.
- Mac or Unix like machine.  The scripting in root folder has been developed on a mac.   Running under unix should be fine as well.  Windows world is possible but will require your own creation of scripts

# Usage
bqm2 is a python program for executing queries you've developed and saving those results into tables.

```
root@0055716555ea:/queries/demo1# python /python/bqm2.py
Usage: [options] folder[ folder2[...]]

Options:
  -h, --help            show this help message and exit
  --execute             'execute' mode.  Accepts a list of folders - folder[
                        folder2[...]].Renders the templates found in those
                        folders and executes them in proper order of their
                        dependencies
  --dotml               Generate dot ml graph of dag of execution
  --show                Show the dependency tree
  --dumpToFolder=DUMPTOFOLDER
                        Dump expanded templates to disk to the folder as files
                        using the key of resource and content of template.
  --showJobs            Show the jobs
  --defaultDataset=DEFAULTDATASET
                        The default dataset which will be used if file
                        definitions don't specify one.  This will be
                        automatically created during 'execute' mode
  --maxConcurrent=MAXCONCURRENT
                        The maximum number of bq or other jobs to run in
                        parallel.
  --defaultProject=DEFAULTPROJECT
                        The default project which will be used if file
                        definitions don't specify one
  --checkFrequency=CHECKFREQUENCY
                        The loop interval between dependency tree evaluation
                        runs
  --maxRetry=MAXRETRY   Relevant to 'execute' mode. The maximum retries for
                        any single resource creation. Once this number is hit,
                        the program will exit non-zero
  --varsFile=VARSFILE   A json file whose data can be refered to in view and
                        query templates.  Must be a simple dictionary whose
                        values are string, integers, or arrays of strings and
                        integers
  --bqClientLocation=BQCLIENTLOCATION
                        The location where datasets will be created. i.e. us-
                        east1, us-central1, etc
```

# Getting Started

The outline of getting started is
- execute run.sh to build container and get inside it
- establish gcp authentication using service account file
- cd into /queries/demo1
- run verify.sh
- run run.sh (a different run.sh inside /queries)

We walk through /queries/demo1 as a basic example of how to use bqm2.

## obtain service account json file
You'll need to get this yourself from google console or ask an admin to generate it for you.  Download this file and save it somewhere secure.  You will mount it inside the subsequent docker container.

## run.sh and container building
For maximal ease of use, work with bqm2 inside of the docker container built by executing /run.sh.  Running without docker is perfectly possible but these docs don't assist with that.

``` GOOGLE_APPLICATION_SERVICE_ACCOUNT=/path/to/your/service/accountfile bash run.sh bash  ```

You may also export the var above. and then simply run

``` bash run.sh bash  ```

So what's going on with above?  The run.sh script passes trailing args to the docker container.  So you can run arbitrary commands including ``` python /python/bqm2.py  ``` itself or even ``` ls ``` or ``` pwd ```.

Passing ``` bash ``` as the arg, puts you into the container with a command prompt as shown

``` root@dea00cd2ffd4:/# ```

## google connectivity
This readme is no substiatue for gcp training, but we do offer some minimal assistance on how to make contact i.e authenticate.

### bqm2 usage
From inside /queries/demo1, after editing /queries/demo1/env.sh to match your project, cd into /queries/demo1. If you can successfully run
- bash verify.sh
- bash run.sh
You should be set.

If not, inspect the errors and work from there.

### using google sdk tools
Executing the following, will allow use of google command line tools

```

gcloud auth activate-service-account --key-file=/gcloud-private-key
gcloud config set project $(jq -r .project_id /gcloud-private-key)

```

From the command line prompt above, type
``` bq ls ```
or
``` gsutil ls ```

If you see your project's datasets or buckets, you're set.  If there an error indicating, you're not logged in or some such, work with your admin to figure it out.

# /queries/demo1/ files

For the rest of this usage guide, you need to be inside ``` /queries/demo1 ``` while inside the container i.e. after running /run.sh from your host computer.

Take a look at the files in here.  Look at vars files.  Look at querytemplate files.  Unionview's etc.

This set of files is a great starting point for your own usage of bqm2.  Copy that folder somewhere on your host.  Edit the files to suit your need.  You won't need any of the files except the .sh files and even those are optional. Why?  bqm2 is just a python program so you can invoke it however you like.

Now we dive into some of the files in /queries/demo1

## env.sh
Edit this file - fill in your project and fill in your default dataset

```
PROJECT=yourproject
DEFAULT_DATASET=mydefault_ds
```

save it. exit.

## verify.sh
You don't need to do anything to this but you should take a look.

What verify.sh does is to check that all your queries and other resource types you've written "compile".  You'll see that templating is key to bqm2.   verify checks that all your template vars are set, no cycles, and then prints out a minimal dag representation of what /queries/run.sh will do.

``` bash verify.sh  ```

What you see output is a DAG of sorts.
For each of your tables and datasets, it will list what their dependencies are.

If you receive an error while working on your own use case, most likely you've forgetten to define a variable or are missing required files for your resource type.

Messages should be specific enough to guide but let us know if they're not and we'll fine tune them.

## run.sh
To be clear this is the run.sh in /queries/demo1/ not to be confused with /run.sh which gets you into bqm2 container.

Executing run.sh

To see the usage


# template types, file suffixes, and .vars files

Bqm2 allows you to write templates, save them as files, and have the results of their execution saved in tables.  That's the general idea.

## supported file suffixes

To enable this, you need to save your file with one of the extensions listed below.

- querytemplate
- view
- unionview
- uniontable
- localdata
- bashtemplate
- externaltable
- gcsdata

## vars files
### template .vars files
For each template file, you may specify an optional .vars file which allows you to specify additional template variables just for use within the given template.

For example, if your template file is foo.querytemplate, its .vars file would need to be saved in foo.querytemplate.vars.

The .vars files format is json.  The structure must be a json array of json objects.  It can be formatted or JSONL - a single line json array of obejcts.

```
[
  {
    "var1": "value for var1"
    "var2", "value for var2"
  }
]
```

### global vars file OR --varsFile

The global vars file (optional but recommended) is a single json object.
You can set vars inside this which will be accessible to all templates.
You may also override global vars within the individal .vars file of your template.


## .querytemplate

### special keys / vars
- extract - this resolve to a gcs path your service account identity can read and write to/from.  This will trigger a bq extract jobs.
- compression - relevant when extract is set.  Values GZIP, SNAPPY, or NONE
- destination_format - relevant when extract is set.  Values - PARQUET, AVRO, NEWLINE_DELIMITED_JSON, CSV
- field_delimiter - relevant when extract is set.  Any single char.
- print_header - relevant when extract is set. This must be a json boolean i.e bare true or false.  A string value throws exception.

## .view

## .unionview

## .uniontable

## .localdata

## .bashtemplate

## .externaltable

## .gcsdata
- max_bad_records

# Directory structure
## /python
Contains actual python code i.e. bqm2 and others

## /int-test
Contains a host of folders and script which together comprise a fairly comprehensive set of integration tests

# State Management
# async execution
bqm2 launches query execution, table loading from gcs, and table extraction to gcs in the background. It caches the job object received from biquery and checks its status at the interval specified with the ``` checkFrquency ``` argument.
## queryhash and description
bqm2 uses the description field of biquery tables to store a hash of the query which was used to create the table.
If the hash is the same as the query to be executed, the query will not be re-run UNLESS one of the tables or views the query depends on has been changed since the time of the current tables creation.

## BigQuery Jobs Api
At start up and when bqm2 is run in ``` execute ``` mode, bqm2 loads up all the jobs in the PENDING or RUNNING state.   It identifies anything which it is trying to manage, update, or create.  If there is a match, bqm2 will wait for the RUNNING or PENDING job to complete.
# todo

- local dev issues
  - deal with M1 and other mac platform types for local execution
  - platform type is hard coded in /run.sh

- integration tests
  - we should switch from creating a new dataset for each run and instead have a single dataset with very tight default expiration set

- enhancements
  - add materialized view support
  - add create table as support
  - add csv|tsv|json|psv extension handlers
    - we already have .localdata support - above extensions would just fill in some default values
  - add better date generation support
  - add support for running as current gcp user i.e no need for service account file
  - add native support for bq external tables
  - longer term - add support for redshift
  - add support for declarative definitions of gcs transfer service
  - add support for declartive definitions of bigquery transfer service
  - investigate k8s job extension i.e use k8 jobs in same manner as we use bq jobs
  - add extension to define pre-existing tables and establish those as dependencies.
