from json.decoder import JSONDecodeError

import json
import yaml
from yaml import YAMLError
from google.cloud.bigquery import WriteDisposition, QueryJobConfig, Dataset
from google.cloud.bigquery.client import Client
from google.cloud.bigquery.schema import SchemaField
from google.cloud.bigquery.table import Table
from os.path import getmtime
import os
from enum import Enum
from google.cloud import storage, bigquery
from google.cloud.exceptions import NotFound

import tmplhelper
from resource import BqExternalTableBasedResource
from resource import Resource, _buildDataSetKey_, BqDatasetBackedResource, \
    BqJobs, BqQueryBackedTableResource, _buildDataSetTableKey_, \
    BqViewBackedTableResource, BqDataLoadTableResource, \
    BqExtractTableResource, BqGcsTableLoadResource, BqProcessTableResource
from tmplhelper import evalTmplRecurse, explodeTemplate
from date_formatter_helper import helpers


class FileLoader:
    def __init__(self):
        pass

    def load(self, file) -> Resource:
        """ The resource loader will attempt to load the resources
        which it handles from the file arg """
        pass

    def handles(self, file) -> bool:
        """ Given a file, the resource should answer true or false
        whether or not this loader can handle loading that file
        """
        pass


class DelegatingFileSuffixLoader(FileLoader):
    """ Manages a map of loader keyed by file suffix """

    def __init__(self, **kwargs):
        if not len(kwargs):
            raise ValueError("Please specify one or more FileLoader")
        for key in kwargs:
            if not issubclass(kwargs[key].__class__, FileLoader):
                raise ValueError("args must be subclass of FileLoader")
            self.loaders = kwargs

    def load(self, file, dryrun):
        suffixParts = file.split("/")[-1].split(".")
        if len(suffixParts) == 1:
            raise ValueError(file +
                             " must have suffix and be from one of " +
                             str(self.loaders.keys()) + " to be processed"
                             )
        try:
            return self.loaders[suffixParts[-1]].load(file, dryrun)
        except KeyError:
            raise ValueError("No loader associated with suffix: " +
                             suffixParts[-1])

    def handles(self, file):
        return self.suffix(file) in self.loaders.keys()

    def suffix(self, file):
        try:
            return file.split("/")[-1].split(".")[-1]
        except BaseException:
            raise ValueError(
                "Invalid file for loading: " + file + ". No suffix")


def parseDatasetTable(filePath, defaultDataset: str, bqClient: Client,
                      defaultProject: str) \
        -> Table:
    tokens = filePath.split("/")[-1].split(".")
    if len(tokens) == 3:
        return bqClient.dataset(tokens[0], project=defaultProject)\
                       .table(tokens[1])
    elif len(tokens) == 2:  # use default dataset
        if not defaultDataset:
            raise ValueError("Must specify a default dataset")
        return bqClient.dataset(defaultDataset, project=defaultProject)\
                       .table(tokens[0])
    elif len(tokens) > 3:
        raise ValueError("Invalid filename: " + filePath +
                         ". File names "
                         "must be of form "
                         "dataset.table.suffix or table.suffix")


def parseDataset(filePath):
    """ Takes a file path and parses to dataset string"""
    tokens = filePath.split("/")[-1].split(".")
    if len(tokens) == 2:
        return tokens[0]
    else:
        raise ValueError("Invalid filename: " + filePath +
                         ". File names for datasets "
                         "must be of form "
                         "dataset.suffix")


def cacheDataSet(bqClient: Client, bqTable: Table, datasets: dict):
    """

    :param bqClient: The client to big query
    :param bqTable: The table whose dataset dependency will be generated
    :param datasets: a place where the dataset will be stuffed
    :return: BqDatasetBackedResource instance, either new or from cache
    """
    dsetKey = _buildDataSetKey_(bqTable)
    if dsetKey not in datasets:
        dset = Dataset(".".join([bqTable.project, bqTable.dataset_id]))
        datasets[dsetKey] = BqDatasetBackedResource(dset, bqClient)
    return datasets[dsetKey]


IS_SCRIPT_KEY = "is_script"


def load_query_job_config(table, jobconfigpath, templatevars):
    if not os.path.exists(jobconfigpath):
        job_config = bigquery.QueryJobConfig()
        job_config.allow_large_results = True
        job_config.flatten_results = False
        if templatevars.get(IS_SCRIPT_KEY, False) is False:
            job_config.destination = table
            job_config.write_disposition = WriteDisposition.WRITE_TRUNCATE

        return job_config

    with open(jobconfigpath, 'r') as f:
        try:
            # first as yaml
            obj = yaml.safe_load(f.read().format(**templatevars))
            job_config = QueryJobConfig.from_api_repr(obj)
            if templatevars.get(IS_SCRIPT_KEY, False) is False:
                job_config.destination = table
            return job_config
        except Exception as e:
            raise Exception(f"unable to load {jobconfigpath} as yaml", e)


class TableType(Enum):
    VIEW = 1
    TABLE = 2
    TABLE_EXTRACT = 3
    TABLE_GCS_LOAD = 4
    UNION_TABLE = 5
    UNION_VIEW = 6
    BASH_TABLE = 7
    EXTERNAL_TABLE = 8


class BqQueryTemplatingFileLoader(FileLoader):
    """
    Query Template loader

    Requires the following
    1. A query file passed to the load method with 0 or more string.format
    simple
    template expressions.
    2. An additional file of the same + .vars, which must be a json array
    of simple key value pairs

    Within each object, there MUST be a 'table' key value.  This maybe a
    string format expression string as well.

    Within each object, there MAY be a 'dataset' key value.  It may also
    be a string.format expression value

    Files passed to the load method MUST have a suffix

    todo: add support for project although this is pretty limiting in
    reality
    """

    def __init__(self, bqClient: Client, gcsClient: storage.Client,
                 bqJobs: BqJobs, tableType:
                 TableType, defaultVars={}):
        """

        :param bqClient: The big query client to use
        :param gcsClient: THe gcs client to use
        :param bqJobs: An initialized BqJobs
        :param tableType Either TABLE or VIEW
        :param defaultDataset: A default dataset to use in templates
        """
        self.bqClient = bqClient
        self.gcsClient = gcsClient
        self.defaultVars = defaultVars
        self.bqJobs = bqJobs
        self.datasets = {}
        self.tableType = tableType
        self.cachedFileLoads = {}
        if not self.tableType or self.tableType not in TableType:
            raise Exception("TableType must be set")

    def explodeTemplateVarsArray(rawTemplates: list,
                                 folder: str,
                                 filename: str,
                                 localVars: dict,
                                 defaultVars: dict):
        ret = []
        for t in rawTemplates:
            copy = t.copy()
            copy['folder'] = folder
            copy['filename'] = filename
            if 'table' not in copy:
                copy['table'] = filename

            copy = {**defaultVars, **localVars, **copy}

            ret += [evalTmplRecurse(t) for t in explodeTemplate(copy)]

        return ret

    def cached_file_read(self, file):
        if file in self.cachedFileLoads:
            return self.cachedFileLoads[file]
        else:
            with open(file) as filestr:
                filestr = filestr.read()
            self.cachedFileLoads[file] = filestr
            return filestr

    def processTemplateVar(self, templateVars: dict, template: str,
                           filePath: str, mtime: int, out: dict, dryrun=False):
        """

        :param templateVars: These are the variables which will be used
        to format the query and generate the table name
        :param template: This is the query which will be templatized
        :param filePath: The local file path where the query exists
        :param mtime: The modification time to give the resource we're
        building
        :param out: a dictionary where any resources which are built
        during method execution will be stored.  Duplicate tables
        generated is considered an error and will raise Exception.
        Datasets are ok.
        :return: void
        """
        templateVarsCopy = templateVars.copy()
        helpers.format_all_date_keys(templateVarsCopy)

        if 'dataset' not in templateVars:
            raise Exception("Missing dataset in template vars for " +
                            filePath + ".vars")
        dataset = templateVars['dataset']
        needed = tmplhelper.keysOfTemplate(template)
        if not needed.issubset(templateVars.keys()):
            missing = str(needed - templateVars.keys())
            raise Exception("Please define values for " +
                            missing + " in a file: ",
                            filePath + ".vars")
        query = template.format(**templateVars)
        legacySql = "#legacysql" in query.lower()

        table = templateVars['table']
        project = None
        if 'project' in templateVars:
            project = templateVars['project']

        # ensure if we have a value for expiration it is an int
        expiration = None
        if 'expiration' in templateVars:
            try:
                expiration = int(templateVars['expiration'])
            except Exception:
                expiration = None

        project_dryrun = project or "default"
        dataset_dryrun = dataset or self.defaultVars["dataset"]

        bqDataset_dryrun, bqTable_dryrun = get_dryrun_bq_dataset_table(
                                                project_dryrun, dataset_dryrun, table)

        if dryrun:
            bqTable = bqTable_dryrun
            bqDataset = BqDatasetBackedResource(bqDataset_dryrun, None)
        else:
            bqTable = self.bqClient.dataset(dataset,
                                            project=project).table(table)
            bqDataset = cacheDataSet(self.bqClient, bqTable, self.datasets)

        # todo - must we really exclude - from table names?
        key = _buildDataSetTableKey_(bqTable)

        prev = key in out and out[key] or None

        if self.tableType == TableType.TABLE:
            qjobconfig = None
            jT = None
            if not dryrun:
                jT = self.bqJobs.getJobForTable(bqTable, "create")
                qjobconfig = load_query_job_config(bqTable,
                                                   filePath + ".queryjobconfig",
                                                   templateVars)
                qjobconfig.use_legacy_sql = legacySql
            arsrc = BqQueryBackedTableResource([query], bqTable,
                                               self.bqClient,
                                               queryJob=jT,
                                               queryJobConfig=qjobconfig,
                                               expiration=expiration,
                                               location=templateVars.get('location', None))
            out[key] = arsrc
            # check if there is extraction logic
            # todo: we need to populate the extraction job
            if 'extract' in templateVars:
                extract_job = None
                if not dryrun:
                    extract_job = self.bqJobs.getJobForTable(bqTable, "extract")
                extractRsrc \
                    = BqExtractTableResource(bqTable,
                                             self.bqClient,
                                             self.gcsClient, extract_job,
                                             templateVars['extract'],
                                             templateVars)
                out[extractRsrc.key()] = extractRsrc
        elif self.tableType == TableType.VIEW:
            arsrc = BqViewBackedTableResource([query], bqTable,
                                              self.bqClient)
            out[key] = arsrc

        elif self.tableType == TableType.TABLE_GCS_LOAD:
            jT = None
            if not dryrun:
                jT = self.bqJobs.getJobForTable(bqTable, "create")

            schema = None
            if "source_format" not in templateVars:
                raise Exception("source_format not found in template vars")

            if templateVars["source_format"] not in set(["PARQUET", "ORC"]):
                schemaFileStr = self.cached_file_read(filePath + ".schema")
                schema = loadSchemaFromString(schemaFileStr.strip())
                templateVars["schema"] = schema

            rsrc = BqGcsTableLoadResource(bqTable,
                                          self.bqClient,
                                          self.gcsClient,
                                          jT, query, schema,
                                          templateVars)
            out[key] = rsrc
        elif self.tableType == TableType.UNION_TABLE:
            # disallow scripts
            if templateVars.get(IS_SCRIPT_KEY, False) is True:
                raise Exception(f"{IS_SCRIPT_KEY} is not allowed "
                                f"for union tables")

            if key in out:
                arsrc = out[key]
                arsrc.addQuery(query)
            else:
                qjobconfig = None
                jT = None
                if not dryrun:
                    qjobconfig = load_query_job_config(bqTable,
                                                       filePath
                                                       + ".queryjobconfig",
                                                       templateVars)
                    qjobconfig.use_legacy_sql = legacySql
                    jT = self.bqJobs.getJobForTable(bqTable, "create")
                arsrc = BqQueryBackedTableResource([query], bqTable,
                                                   self.bqClient,
                                                   queryJob=jT,
                                                   queryJobConfig=qjobconfig,
                                                   expiration=expiration,
                                                   location=templateVars.get('location', None))
                out[key] = arsrc

        elif self.tableType == TableType.UNION_VIEW:
            if key in out:
                arsrc = out[key]
                arsrc.addQuery(query)
            else:
                arsrc = BqViewBackedTableResource([query], bqTable,
                                                  self.bqClient)
                out[key] = arsrc

        elif self.tableType == TableType.BASH_TABLE:
            jT = None
            if not dryrun:
                jT = self.bqJobs.getJobForTable(bqTable, "create")
            stripped = self.cached_file_read(filePath + ".schema").strip()
            schema = loadSchemaFromString(stripped)
            # with open(filePath + ".schema") as schemaFile:
            #     schema = loadSchemaFromString(schemaFile.read().strip())
            arsrc = BqProcessTableResource(query, bqTable, schema, self.bqClient, job=jT)
            out[key] = arsrc
        elif self.tableType == TableType.EXTERNAL_TABLE:
            from google.cloud.bigquery import ExternalConfig
            # query here is actually json
            ext_config_obj = json.loads(query)
            ext_config = ExternalConfig.from_api_repr(ext_config_obj)
            autodetect = "autodetect" in ext_config_obj \
                         and ext_config_obj["autodetect"]
            schema = None
            if not autodetect:
                try:
                    stripped = \
                        self.cached_file_read(filePath + ".schema").strip()
                    schema = loadSchemaFromString(stripped)
                except Exception:
                    raise Exception("Please provide a .schema "
                                    "file for your external table. " +
                                    filePath + ".schema")

            if not project:
                project = "default"
            bqTable = Table(".".join([project, dataset, table]), schema)
            arsrc = BqExternalTableBasedResource(self.bqClient, bqTable,
                                                 ext_config)
            out[key] = arsrc

        dsetKey = _buildDataSetKey_(bqTable)
        if dsetKey not in out:
            out[dsetKey] = bqDataset

        if prev and prev != out[key] and \
                self.tableType not in set([TableType.UNION_TABLE,
                                          TableType.UNION_VIEW]):
            raise Exception("Templating generated duplicate "
                            "tables outputs for " + filePath)

    def load(self, filePath, dryrun):
        mtime = getmtime(filePath)
        ret = {}
        with open(filePath) as f:
            template = f.read()
            try:
                filename = filePath.split("/")[-1].split(".")[-2]
                localVarsPath = os.path.join(os.path.dirname(filePath), "local.vars")
                folder = filePath.split("/")[-2]
                templateVars = \
                    BqQueryTemplatingFileLoader.explodeTemplateVarsArray(
                        self.loadTemplateVars(filePath + ".vars"),
                        folder,
                        filename,
                        self.loadLocalVars(localVarsPath),
                        self.defaultVars
                    )

            except FileNotFoundError:
                raise Exception("Please define template vars in a file "
                                "called " + filePath + ".vars")
            for v in templateVars:
                self.processTemplateVar(v, template, filePath, mtime, ret, dryrun)
        return ret.values()

    def loadLocalVars(self, filePath):
        local_vars = dict()
        if filePath \
            and os.path.exists(filePath) \
                and os.path.isfile(filePath):
            with open(filePath) as f:
                local_vars = yaml.safe_load(f)
                if not isinstance(local_vars, dict):
                    raise Exception(
                        "Must be single json or yaml object in "
                        + filePath)
        return local_vars

    def loadTemplateVars(self, filePath) -> list:
        try:
            with open(filePath) as f:
                template_vars_list = yaml.safe_load(f)
                if not isinstance(template_vars_list, list):
                    raise Exception(
                        "Must be json or yaml list of objects in " + filePath)
                for definition in template_vars_list:
                    if not isinstance(definition, dict):
                        raise Exception(
                            "Must be json list of objects in " + filePath)

                return template_vars_list
        except FileNotFoundError:
            return [{}]
        except (JSONDecodeError, YAMLError) as e:
            raise Exception("Problem reading json or yaml var list from file: ",
                            filePath, e)


class BqDataFileLoader(FileLoader):
    def __init__(self, bqClient: Client, defaultDataset=None,
                 defaultProject=None, bqJobs=None):
        self.bqClient = bqClient
        self.defaultDataset = defaultDataset
        self.defaultProject = defaultProject
        self.datasets = {}
        self.bqJobs = bqJobs

    def load(self, filePath, dryrun=False):
        mtime = getmtime(filePath)
        schemaFilePath = filePath + ".schema"
        mtime_schema = getmtime(schemaFilePath)
        mtime = max([mtime, mtime_schema])

        with open(schemaFilePath) as schemaFile:
            schema = loadSchemaFromString(schemaFile.read().strip())

        jT = None
        if dryrun:
            project_dryrun = self.defaultProject or "default"
            dataset_dryrun = self.defaultDataset
            table_dryrun = filePath.split("/")[-1].split(".")[0].replace('-', '_')
            bqDataset_dryrun, bqTable_dryrun = get_dryrun_bq_dataset_table(
                                                project_dryrun, dataset_dryrun, table_dryrun)
            bqTable = bqTable_dryrun
            bqDataset = bqDataset_dryrun
            bqDataset = BqDatasetBackedResource(bqDataset, None)

        else:
            bqTable = parseDatasetTable(filePath, self.defaultDataset,
                                        self.bqClient, self.defaultProject)
            bqDataset = cacheDataSet(self.bqClient, bqTable,
                                     self.datasets)
            jT = self.bqJobs.getJobForTable(bqTable, "create")

        ret = []
        ret.append(BqDataLoadTableResource(filePath, bqTable, schema,
                                           self.bqClient, jT))
        ret.append(bqDataset)

        return ret


def get_dryrun_bq_dataset_table(project_dryrun, dataset_dryrun, table_dryrun):
    bqTable_dryrun = type('Table', (), {})()
    bqTable_dryrun.table_id = table_dryrun
    bqTable_dryrun.dataset_id = dataset_dryrun
    bqTable_dryrun.project = project_dryrun

    bqDataset_dryrun = type('Dataset', (), {})()
    bqDataset_dryrun.dataset_id = dataset_dryrun
    bqDataset_dryrun.project = project_dryrun
    return bqDataset_dryrun, bqTable_dryrun


def loadSchemaFromString(schema: str):
    """ only support simple schema for i.e. not json just cmd line
    like format """

    # first we try to load as json
    try:
        fields = [loadSchemaField(jsonField)
                  for jsonField in json.loads(schema)]
        return fields
    except JSONDecodeError:
        pass

    try:
        ret = []
        for s in schema.split(","):
            (col, type) = s.split(":", maxsplit=2)
            ret.append(SchemaField(col, type))
        return ret
    except ValueError:
        raise Exception("Schema file should contain either bq "
                        "json schema definition or a string "
                        "following the"
                        "format "
                        "col:type," +
                        "col2:type.")


def loadSchemaField(jsonField: dict):
    lMapping = {k.lower(): k for k in jsonField}
    mode = 'NULLABLE'
    if "mode" in lMapping:
        mode = jsonField[lMapping['mode']]

    description = None
    if "description" in lMapping:
        description = jsonField[lMapping['description']]

    fields = ()
    if "fields" in lMapping:
        fields = [loadSchemaField(x)
                  for x in jsonField[lMapping['fields']]]

    return SchemaField(jsonField[lMapping["name"]],
                       jsonField[lMapping["type"]],
                       mode=mode,
                       description=description,
                       fields=fields)
