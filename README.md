# bqm2


## What is bqm2?

bqm2 stands for BigQuery Materializer 2.   In short, it allows you to
- write queries
- save them as files
- execute those queries in the correct order
- and save the results of each query in datasets and tables of your choosing.
- change those queries and re-run and only re-execute that query AND any of its dependants.
- load and extract gcs data to and from tables

# Requirements
- Google project and access to bigquery and preferably cloud storage
- Docker or equivalent.
- Mac or Unix like machine.  The scripting in root folder has been developed on a mac.   Running under unix should be fine as well.  Windows world is possible but will require your own creation of scripts

# Usage

```
root@0055716555ea:/queries/demo1# python -m bqm2
Usage: [options] folder[ folder2[...]]

Options:
  -h, --help            show this help message and exit
  --var=KEY=VALUE       Define one or more key=value pairs which will be
                        available as if they were declared in a global vars
                        file. Always takes precedence over any var in global
                        vars. Values may be json list. Supported lists are
                        same as list types supported in global, local, or
                        template vars files
  --execute             'execute' mode.  Accepts a list of folders - folder[
                        folder2[...]].Renders the templates found in those
                        folders and executes them in proper order of their
                        dependencies
  --dotml               Generate dot ml graph of dag of execution.  For more
                        info on dot and graphviz, checkout
                        https://www.graphviz.org/
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
  --varsFile=VARSFILE   A json or yaml file whose data can be refered to in
                        view, query, and other templates.  Must be a simple
                        dictionary whose values are string, integers, or
                        arrays of strings and integers
  --bqClientLocation=BQCLIENTLOCATION
                        The location where datasets will be created. i.e. us-
                        east1, us-central1, etc
  --print-global-args   Creates a json output of the parsed global args
                        consumed from the command line
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

What verify.sh does is to check that all your queries and other resource types you've written "compile".  You'll see that templating is key to bqm2.   verify checks that all your template vars are set, no cycles, and then prints out a minimal dag representation of what /queries/demo1/run.sh will do.

``` bash verify.sh  ```

What you see output is a DAG of sorts.
For each of your tables and datasets, it will list what their dependencies are.

If you receive an error while working on your own use case, most likely you've forgetten to define a variable or are missing required files for your resource type.

Messages should be specific enough to guide but let us know if they're not and we'll fine tune them.

## run.sh
To be clear, this is the run.sh in /queries/demo1/ not to be confused with /run.sh which gets you into bqm2 container.

Executing run.sh will actually execute queries, save them to tables, create datasets, and load and unload data from gcs if specified.

The files in demo1 just create tables.  no table loading unloading etc.  More details about those operations in docs below.

## other files
demo1 folder contains querytempate, unionview, and uniontable types.  Each of those and others will be discussed elsewhere in doc.

# template types, file suffixes, and .vars files

Bqm2 allows you to write templates, save them as files, and have the results of their execution saved in tables.  That's the general idea.
The templates themselves may be any one of the supported file suffix and resource types.

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

The .vars files format is json or yaml.  The structure must be an array of objects.

```
[
  {
    "var1": "value for var1",
    "var2", "value for var2",
    "var3": "{var1} and {var2} are very var-iable"
  }
]
```

### local vars files
A local vars file is a folder level var file just like global vars i.e. a single json or yaml object. The name of the vars file must be 
``` local.vars ```

### nested arrays of objects

There are times when one needs to be able to generate arbitrary associations between key value sets i.e 
when a = b then c = d and when a = f , then c = g, etc.  Specifying
```
{
  "a": ["b", "f"]
  "c": ["d", "g"]
}
```

Would generate a cross product and four resulting objects with unwanted associations.

Instead, you can specify arrays of objects as a key value.  For example
```
[
  {
    "var1": [
        {
            "a": "b",
            "c": "d",
        },
        {
            "a": "f",
            "c": "g"
        }
    ]
    "var2", "value for var2",
  }
]
```

The resulting objects available for use in your templates are
```
{
    "a": "b",
    "c": "d",
    "var2": "value for var2"
}

{
    "a": "f",
    "c": "g",
    "var2": "value for var2"
}

Note that var1 is NOT a usable key for any template.  It "drops away" during the expansion.
```

Nested arrays of objects may be used in 
- --var arguments as inline json
- --varsFile files
- local.vars
- {template}.vars files

This allows you to have folder level overrides to global vars and or introduce new variables for use in templates at a folder level.  Note that bqm2 does not recurse into folders.

### special vars

For all templates, there are a few special variables

- table

The table var controls the name of the bigquery table name which will be used to store the resources of the template execution.  In the case of querytemplate or view templates, each generated query must be mapped to a single table name.  This is not the case for unionview and uniontable.

The default value for table var is the name of the template without the suffix. So foo.querytemplate gets a table value of ``` foo ```.

- dataset

A default data set is required to be set by the command line.  It will be used to create the full table name to store template execution results if not over ridden.

You can reference any number of dataset you wish and over ride the default one in any of your templates .vars files

```
[
  {
    "my_dataset": "some_other_dataset",
    "dataset": "overridesthedefaultdataset"
  },
  .
  .
]
```

- project

A default project is taken from the command line argument or infered from the bq client used for execution of bqm2 i.e. the service account file used currently.

You may reference any number of projects and establish different variables to use their names and load or query their data.

- filename
This is the filename of the current template without the suffix.   When the table var is not specified, this is used as the table var.  You may use it anywhere in vars files or template itself as shown.

```
[
  {
    "table": "{filename}_{yyyymmdd}"
    .
    .
  },
  ...
]
```

or in an actual template

```
#standardSQL

select "{filename}" as template
```

- folder

This is the folder name of the current template.  Note if you specify your folder as ., then your folder var will be named literal . .

- is_script

The is_script variable is only applicable for .querytemplate.vars files.  

The result of the setting the is_script var affects the 
generated QueryJobConfig object which is passed to BigQuery for job execution.  

In short, a destination table will NOT be set
when the is_script variable is set.  As such, it is vitally important that 
your script manage the creation of a table or view itself.  

Doing so ensures that after 
successful execution, your .querytemplate template aka script will not be repeatedly executed.

Not doing so ensures that you script will be retried up to the maxRetries 
setting of the bqm2.py program execution.

bqm2 checks for the existence of 
{dataset}.{table} before executing the querytemplate again.

For more information about scripting in bigquery, checkout out this reference - https://cloud.google.com/bigquery/docs/multi-statement-queries

- location

When set in a .vars file which affects a .querytemplate or .uniontable, the location variable controls the location where the QueryJob is run.  This has been needed
when executing LOAD .... FROM FILES ... with CONNECTION that use an OMNI connection.   To use an omni connection, it appears that all jobs must be run in the same region
as the OMNI connection itself.  That said, data loaded may land outside of the OMNI region.

If you try to use an omni connection and the execution errors complain that the connection is not found, you may need to set the location var in your .vars of the querytemplate.



### special date based variables

bqm2 allows a short hand for specifying relative to NOW date ranges. The specially interpreted variables are

- .*yyyy - for years like 2022
- .*yyyymm - for year months like 202212
- .*yyyymmdd - for year month days like 20221231
- .*yyyymmddhh - for year, month, day, hour like 2022123100

Any var which is equal to or ends with the above suffixes and has integer values, will be treated as a date variable.

You may specify dates using an integer or a range of dates using an integer array of length 2.

Examples

If this year is 2022, then
```
"yyyy": -1,
"foo_yyyy": [-1, -2]
````

yields
- "yyyy": "2021"
- "foo_yyyy": ["2020", "2021"]
respectively.

or if today is 20221001, then
```
"yyyymmdd": 2,
"foo_yyyymmdd": [-1, 1]
```
yields

- "20221003"
- ["20220931", "20221001", "20221002"]

respectively.

### generated date based vars
In order to support many different formats for date sequences, bqm2 generates template variables representing the year, month, day, and hour components of any of the 3 date base key types

- yyyymm
- yyyymmdd
- yyyymmddhh

So if foo_yyyymm = -1 and that is 202112 then the generated vars
- yyyymm_yyyy = 2021
- yyyymm_mm = 12

will also be available for use in templates.

so specifying
- yyyymmdd = -1 where -1 is 20211231

will generate
- yyyymmdd_yyyy = 2021
- yyyymmdd_yy = 21
- yyyymmdd_mm = 11
- yyyymmdd_dd = 31

and specifying
- yyyymmddhh = -1 where -1 is 2021123101

will generate

- yyyymmddhh_yyyy = 2021
- yyyymmddhh_mm = 11
- yyyymmddhh_dd = 23
- yyyymmddhh_hh = 01

template vars for use based upon the same date sequence.

### global vars file OR --varsFile

The global vars file (optional but recommended) is a file containing a single json object or yaml object.
You can set vars inside this which will be accessible to all templates.
You may also override global vars with 
- a --var key and value passed on the command line
- a folders local vars file 
- the individal .vars file of your template.

# supported file suffixes

We repeat the list of supported suffixes here before sharing details of each.

- querytemplate
- view
- unionview
- uniontable
- localdata
- bashtemplate
- externaltable
- gcsdata

## .querytemplate
A querytemplate is treated as a template executed as a bigquery QueryJobConfig.

Only legacy and standard sql variants of BigQuery are available.  The default is standard sql.  

In addition to an optional .vars file, an optional .queryjobconfig file may be specified.   The only accepted data format 
for the queryjobconfig files is yaml. .queryjobconfig files are also handled as templates.  


- Example .querytemplate file

If your template is in a file named bar.querytemplate

```
#standardSQL

select "{var1}" as colA
```

And your .vars file is in a file name bar.querytemplate.vars
```
[
  {
    "var1": "foo"
  }
]
```
Then your your generated query will be

```
#standardSQL

select "foo" as colA
```

And the results of that query will get stored in a table name ``` bar ```

- An example .querytemplate.queryconfig file 

```
query:
  allowLargeResults: true
  clustering:
    fields:
      - a
      - b
  maximumBillingTier: 4
  maximumBytesBilled: '10'
  priority: BATCH
  rangePartitioning:
    field: foo
  defaultDataset: null
  createDisposition: CREATE_IF_NEEDED
  timePartitioning:
    type: DAY
    field: x
labels:
  a: b
```

For information on the configurations for .queryjobconfig files available, read through 

https://cloud.google.com/python/docs/reference/bigquery/latest/google.cloud.bigquery.job.QueryJobConfig


### special keys / vars
- extract - this resolve to a gcs path your service account identity can read and write to/from.  This will trigger a bq extract jobs.
- compression - relevant when extract is set.  Values GZIP, SNAPPY, DEFLATE, or NONE
- destination_format - relevant when extract is set.  Values - PARQUET, AVRO, NEWLINE_DELIMITED_JSON, CSV
- field_delimiter - relevant when extract is set.  Any single char.
- print_header - relevant when extract is set AND destination_format = CSV.
  This must be a json/yaml boolean i.e bare true or false.  A string value throws exception.
- expiration - table expiration in days from the create time of table
- is_script - accepted values are json/yaml booleans.   See elsewhere in this doc for more detail on is_script var.  
## .view

.views are just like .querytemplate but executed synchronously because at time of writing there's no async mode for creating views.

## .unionview

A union view performs a union all of each generated query mapped to the same table name and saves it as a view.

Example:

So if your .unionview is stored in a file name awesomeview.unionview and contains

```
#standardSQL

select "{foo}" as col

```
and your .vars is
```
[
  {
    "foo": "bar"
  },
  {
    "foo": "bazz"
  }
]
```
Your generated query would be

```
#standardSQL

select "bar" as col

union all

#standardSQL

select "bazz" as col

```

Then a view will be created in a table named awesomeview in the value of {dataset}.

Note - you can get fancy and override table in here to point to multiple tables

```
[
  { "table": "wheat", "foo": "bar"},
  { "table": "corn", "foo": "bazz"},
  { "table": "corn": "bazzy star"}
]
```

Now the result would be 2 views
- wheat - union of one query
- corn - union of two mapped to corn

## .uniontable

A union table performs a union all of each generated query mapped to the same table name and executes the resulting query and saves it as a table.


Same logic as unionview.

note: an error will be produced if the is_script variable is set in the .vars files for uniontable queries.

In addition to an optional .vars file, an optional .queryjobconfig file may be specified.   The only accepted data format 
for the queryjobconfig files is yaml.

## .localdata
A localdata is a flat file of either tab separated data or new delimited json (NDJSON) which may be uploaded to a table by the same name as the file itself.

A limitation of localdata files is that currently they can only be loaded into the default dataset of the bqm2 --defaultDataset argument.

A .localdata.schema file is required. This may be shorthand syntax like the bq cli accepts i.e. col1:string,col2:int,... etc OR a json file containing googles bigquery json schema -  https://cloud.google.com/bigquery/docs/schemas#specifying_a_json_schema_file

A hash of the entire file is used to determine if a reload is necessary.  That hash will be stored in the description of the created table.

The dataset where .localdata tables will be stored is in the --defaultDataset of the current bqm2 command.

Another possibility, not recommended, is to name your .localdata file with 3 dot separated portions instead of two.   

For example, naming a .localdata as tmp.foo.localdata will create a table named foo in the tmp dataset.  
Naming a .localdata foo.localdata will create a table named foo in the --defaultDataset of the bqm2 command.

### default values used
- skip_leading_rows is set to 1 by default.  In case of CSV i.e. tab delimited data, be sure to include a header.
- table - will always be the name of file without the suffix and it will be stored in the default dataset of the current bqm2 execution.

## .bashtemplate
Allows for the stdout of a bash script to be used as table data to load to biquery tables.  The execution of bashtemplate are NOT asynchronous.

A .bashtemplate.schema file is required.

- json form - https://cloud.google.com/bigquery/docs/schemas#specifying_a_json_schema_file
or
- shorthand form - i.e. col1:col1type[col2:col2type[,....]]

### special keys / vars
- source_format
- field_delimiter - defaults to '\t'

### default values used
- WRITE_DISPOSITION is set to WRITE_TRUNCATE i.e. always replace table.
- ignore_unknown_values is alway True.

## .externaltable

Big Query external tables may be created using this suffix.  The template format is json itself.  In order to inter-operate with
python's .format templating, the curly braces must be double escaped as follows.

```
{{
    "sourceUris": ["gs://{project}-bqm2-int-test/parquet_test.parquet"],
    "sourceFormat": "PARQUET",
}}
```

Above example is taken from /int-test/bq/test_parquet.externaltable

.externaltable.schema file is required if "autodetect" is not true

- json form - https://cloud.google.com/bigquery/docs/schemas#specifying_a_json_schema_file
or
- shorthand form - i.e. col1:col1type[col2:col2type[,....]]

Supported structure of template follows the ExternalConfig structure - https://cloud.google.com/python/docs/reference/bigquery/latest/google.cloud.bigquery.external_config.ExternalConfig

Exhaustive testing of all options hasn't occured but everything you specify in your external table template file is passed through to biquery python apis directly.

The from_api_repr method is used to load your template
- https://cloud.google.com/python/docs/reference/bigquery/latest/google.cloud.bigquery.external_config.ExternalConfig#google_cloud_bigquery_external_config_ExternalConfig_from_api_repr


## .gcsdata
These templates allow you to load gcs data into tables.

.gcsdata.schema file is required.

- json form - https://cloud.google.com/bigquery/docs/schemas#specifying_a_json_schema_file
or
- shorthand form - i.e. col1:col1type[col2:col2type[,....]]

### special keys / vars

- max_bad_records - max number of allowable bad records
- skip_leading_rows - number of leading rows to skip (CSV only)
- source_format
  - AVRO
  - CSV
  - DATASTORE_BACKUP (not tested)
  - NEWLINE_DELIMITED_JSON
  - ORC
  - PARQUET

- ignore_unknown_values
Consult google docs however this allows ignoring unknown columns in json or csv

- encoding
- quote_character - csv only
- null_marker - csv only
- allow_jagged_rows csv only
- destination_table_description - loaded table description


- require_exists - if set, this directive requires that the gcs path specified contains or is at least on gcs blob.

# Directory structure
## /python
Contains actual python code i.e. bqm2 and others

## /int-test
Contains a host of folders and scripts which together comprise a fairly comprehensive set of integration tests and examples of each file extension.

# State Management
## async execution
bqm2 launches query execution, table loading from gcs, and table extraction to gcs in the background. It caches the job object received from biquery and checks its status at the interval specified with the ``` checkFrequency ``` argument.
## queryhash and description
bqm2 uses the description field of biquery tables to store a hash of the query which was used to create the table or view.

If the hash is the same as the query to be executed, the query will not be re-run UNLESS one of the tables or views the query depends on has been changed since the time of the current tables creation.

The query used to create the table or view is also saved in the description for reference.

## BigQuery Jobs Api
At start up and when bqm2 is run in ``` execute ``` mode, bqm2 loads up all the jobs in the PENDING or RUNNING state.   It identifies anything which it is trying to manage, update, or create.  If there is a match, bqm2 will wait for the RUNNING or PENDING job to complete.

# Templating

## What templating engine is used?
None in fact.   Basic python .format(....) is used however it's enhanced significantly.

The enhancement allows template vars to be built using other template vars as follows.

```
{
  "a": "key a is built from value of {b} and value of {c}",
  "b": "b val",
  "c": "c val"
}

```

This is available in both .vars files as well as global vars files.

# Examples
The /int-test sub folders contain many examples of all if not most of the supported file extension and resource types.

There is an integration test /int-test/test-basic.sh which is run on pull request of this repo which exercised them all.

The /queries/demo1 also has examples


#  todo

- dataset is created even in dumpToFolder/verify mode
- local dev issues
  - deal with M1 and other mac platform types for local execution
  - platform type is hard coded in /run.sh

- function support
  - might already be supported.. (Mike Lee)
  - javascript udfs get wonky due to curly braces in js functions (easy solution is to exclude templating code blocks in triple quotes)
  - current solution is make all js functions with curly braces into a single line and double the braces to work with python format

- integration tests
  - we should switch from creating a new dataset for each run and instead have 
  a single dataset with very tight default expiration set

- enhancements
  - .dataset type and remove passive dataset creation
  - add materialized view support
  - add create table as support
  - add csv|tsv|json|psv extension handlers
    - we already have .localdata support - above extensions would just fill in some default values
  - add support for running as current gcp user i.e no need for service account file
  - longer term - add support for redshift
  - add support for declarative definitions of gcs transfer service
  - add support for declarative definitions of bigquery transfer service
  - investigate k8s job extension i.e use k8 jobs in same manner as we use bq jobs
  - add extension to define pre-existing tables and establish those as dependencies
  - add .model support - this is a to_api_repr and from_api_repr situation

# known issues

  - The descriptions of tables can end up being too long and interfere with execution and saving of results.  Any descriptions which end up being too long will be truncated to fit in the allowed table description field.
  - For --var date type variables, one cant currently pass in an offset i.e. -1, 1, etc.  The value is interpreted as a string and causes a parse failure during startup.

# script and .queryjobconfig scenarios

2023/01/10

We're enabling execution of multi-statement sql.  We're also enabling another means of controlling parameters of normal .querytemplate and .uniontable executions.

- .uniontables may not be scripts at this time
- script with and w/o queryconfig file
- uniontable with queryconfig file
- querytemplate with / with out queryconfig file
