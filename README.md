# bqm2

## What is bqm2?

bqm2 stands for BigQuery Materializer 2.   In short, it allows you to
- write queries
- save them as files
- execute those queries in the correct order
- and save the results of each query in datasets and tables of your choosing.

# Requirements
- Google project and access to bigquery and preferably cloud storage
- Docker or equivalent.
- Mac or Unix like machine.  The scripting in root folder has been developed on a mac.   Running under unix should be fine as well.  Windows world is possible but will require your own creation of scripts

# Usage

The outline of usage is
- execute run.sh to build container and get inside it
- establish gcp authentication using service account file
- cd into /queries/demo1
- run verify.sh
- run run.sh (a different run.sh inside /queries)

This usage walk through uses /queries/demo1 as a basic example of how to use bqm2

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

This isn't gcp training.  But we do offer some minimal assistance on how to make contact.

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

For the rest of this usage guide, you need to be inside ``` /queries/demo1 ```

Take a look at the files in here.  Look at vars files.  Look at querytemplate files.  Unionview's etc.

## env.sh
Edit this file - fill in your project and fill in your default dataset

```
PROJECT=yourproject
DEFAULT_DATASET=mydefault_ds
```

save it. exit.

## verify.sh
What verify.sh does is to check that all your queries and other resource types you've written "compile".  You'll see that templating is key to bqm2.   verify checks that all your template vars are set, no cycles, and then prints out a minimal dag representation of what /queries/run.sh will do

``` bash verify.sh  ```

What you see output is a DAG of sorts.
For each of your tables and datasets, it will list what their dependencies are.

If you receive an error while working on your own use case, most likely you've forgetten to define a variable or are missing required files for your resource type.

Messages should be specific enough to guide but let us know if they're not and we'll fine tune them.

## run.sh
To be clear this is the run.sh in /queries/demo1/.

Executing run.sh

To see the usage


# resource types

## .querytemplate

## .view

## .unionview

## .uniontable

## .localdata

## .bashtemplate
## .externaltable


# Directory structure
## /python
Contains actual python code i.e. bqm2 and others

## /int-test
Contains a host of folders and script which together comprise a fairly comprehensive set of integration tests


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
