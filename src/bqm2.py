#!/usr/bin/env python
import json
import logging
from optparse import OptionParser

from kvoption import KVOption
from genericpath import isfile
from os import listdir
import re
from time import sleep

from collections import defaultdict

import yaml
from google.cloud import storage
from google.cloud.bigquery.client import Client

from loader import DelegatingFileSuffixLoader, \
    BqQueryTemplatingFileLoader, BqDataFileLoader, \
    TableType
from resource import BqJobs
from google.cloud import bigquery

from google.api_core.exceptions import PreconditionFailed


def find_cycles(dependencies: dict):
    """
        dependencies: a dict keys point to sets of keys forming a graph
        return sub keys of dependencies which contain a cycle
    """
    while len(dependencies):
        torm = set()
        for key in dependencies.keys():
            if not len(dependencies[key]):
                torm.add(key)

        if not torm:
            # these keys have a cycle
            return set(dependencies.keys())

        # remove keys with no dependencies
        for key in torm:
            del dependencies[key]

        # remove removed keys from anyone that depends on it
        for key in dependencies.keys():
            dependencies[key] = dependencies[key] - torm

    return set()


class DependencyBuilder:
    """
    Dependency builder loads resources from the folders specified.
    """

    def __init__(self, loader):
        self.loader = loader

    def buildDepend(self, folders, dryrun) -> tuple:
        """ folders arg is an array of strings which should point
        at folders containing resource descriptions loadable by
        self.loader """
        resources = {}
        for folder in folders:
            folder = re.sub("/$", "", folder)
            for name in listdir(folder):
                file = "/".join([folder, name])
                if isfile(file) and self.loader.handles(file):
                    for rsrc in self.loader.load(file, dryrun):
                        resources[rsrc.key()] = rsrc

        resourceDependencies = {rsrc.key(): set() for rsrc in resources.values()}

        for rsrc in resources.values():
            for osrc in resources.values():
                if rsrc.dependsOn(osrc):
                    resourceDependencies[rsrc.key()].add(osrc.key())

        copy = {key: set([x for x in resourceDependencies[key]]) for key in resourceDependencies}
        cycles = find_cycles(copy)
        if cycles:
            raise Exception("There are cycles in your templates.  Please make sure "
                            "your recent changes have not introduced any cycles")

        return (resources, resourceDependencies)


class DependencyExecutor:
    """ """

    def __init__(self, resources, dependencies, maxRetry=2):
        self.resources = resources
        self.dependencies = dependencies
        self.maxRetry = maxRetry

    def dump(self, folder):
        """ dump expanded templates to a folder """
        for (k, s) in sorted(self.dependencies.items()):
            if len(s):
                msg = " ".join([x for x in sorted(s)])
            else:
                msg = "nothing"

            print(k, "depends on", msg)
        while len(self.dependencies):
            todel = set([])
            for n in sorted(self.dependencies.keys()):
                if not len(self.dependencies[n]):
                    todel.add(n)
                    toWrite = folder + "/" \
                        + self.resources[n].key().replace("/", "_") \
                        + ".debug"
                    with open(toWrite, "w") as f:
                        f.write(self.resources[n].dump())
                        f.close()
                    del self.dependencies[n]

            for n in sorted(self.dependencies.keys()):
                torm = set([])
                for k in self.dependencies[n]:
                    if k not in self.dependencies:
                        torm.add(k)

                    self.dependencies[n] = self.dependencies[n] - torm

    def show(self):
        for (k, s) in sorted(self.dependencies.items()):
            if len(s):
                msg = " ".join([x for x in sorted(s)])
            else:
                msg = "nothing"

            print(k, "depends on", msg)

        while len(self.dependencies):
            todel = set([])
            for n in sorted(self.dependencies.keys()):
                if not len(self.dependencies[n]):
                    todel.add(n)
                    print("would execute", n)
                    del self.dependencies[n]

            for n in sorted(self.dependencies.keys()):
                torm = set([])
                for k in self.dependencies[n]:
                    if k not in self.dependencies:
                        torm.add(k)

                    self.dependencies[n] = self.dependencies[n] - torm

    def dotml(self):
        print("digraph g {\n")
        for (k, s) in sorted(self.dependencies.items()):
            if not len(s):
                continue
            for n in s:
                # if len(str(n).split(".")) == 1:
                #     continue
                print("".join(['"', k, '"']), "->", "".join(['"', n, '"']))
        print("}")

    def handleRetries(self, retries, rsrcKey):
        retries[rsrcKey] -= 1
        if retries[rsrcKey] < 0:
            raise Exception("Maximum retries hit for resource",
                            rsrcKey)

    def execute(self, checkFrequency=10, maxConcurrent=10):
        retries = defaultdict(lambda: self.maxRetry)
        running = set([])

        # def update times is a dict of maximum of the update
        # times of the dependencies of a resource
        """
        i.e., self.dependencies = {
           "table1": {"table_that_table1_depends_on"},
           "table_that_table1_depends_on": {},
        }

        We loop through this and execute keys with no dependencies.
        When each finishes, we remove that from the values
            of all other keys that contain it
        """

        depUpdateTimes = defaultdict(lambda: 0)
        while len(self.dependencies):
            todel = set([])
            completed = set([])
            for n in sorted(self.dependencies.keys()):
                if not len(self.dependencies[n]):
                    todel.add(n)

            """ flag to capture if anything was running.  If so,
            we will pause before looping again.
            Check running tasks first to clear them, then others"""
            for n in sorted(todel, key=lambda k: (int(k not in running), k)):
                try:
                    # check if it's already running
                    if (self.resources[n].isRunning()):
                        print(self.resources[n], "already running")
                        running.add(n)
                        # continue so we can check other resource statuses
                        continue
                    else:
                        running.discard(n)
                    # check if it doesn't exist in bq
                    if not self.resources[n].exists():
                        # break on max concurrency
                        if len(running) >= maxConcurrent:
                            print("max concurrent running already")
                            # continue so we can check other resource statuses
                            break
                        self.handleRetries(retries, n)
                        # try to create resource
                        print("executing: because it doesn't exist ", n)
                        self.resources[n].create()
                        # confirm resource is actually running
                        # this prints <job_id> <status> <response>
                        if (self.resources[n].isRunning()):
                            running.add(n)
                        # continue so we can check other resource statuses
                        continue
                    # check if the query hash has changed
                    # by checking the description for it
                    elif self.resources[n].shouldUpdate():
                        # break on max concurrency
                        if len(running) >= maxConcurrent:
                            print("max concurrent running already")
                            # continue so we can check other resource statuses
                            break
                        self.handleRetries(retries, n)
                        print("executing: because our definition has changed",
                              n, self.resources[n])
                        # recreate resource again
                        self.resources[n].create()
                        # confirm resource is running
                        if (self.resources[n].isRunning()):
                            running.add(n)
                        # continue so we can check other resource statuses
                        continue
                    # check if dependencies were updated more recently than resource
                    # if so, we should regenerate resource since dependencies
                    #     may have changed.
                    elif self.resources[n].updateTime() < depUpdateTimes[n]:
                        # break on max concurrency
                        if len(running) >= maxConcurrent:
                            print("max concurrent running already")
                            # continue so we can check other resource statuses
                            break
                        self.handleRetries(retries, n)
                        print("executing: because our dependencies have "
                              "changed since we last ran",
                              n, self.resources[n])
                        # recreate resource again
                        self.resources[n].create()
                        # confirm resource is running
                        if (self.resources[n].isRunning()):
                            running.add(n)
                        # continue so we can check other resource statuses
                        continue
                    # otherwise, nothing to do but cleanup
                    else:
                        print(self.resources[n],
                              " resource exists and is up to date")
                        # delete from dependency dict
                        del self.dependencies[n]
                        # remove from running set (if in there)
                        running.discard(n)
                        completed.add(n)
                except PreconditionFailed as e:
                    print("trapping precondition fail error")
                    print(e)
                    self.handleRetries(retries, n)
                    continue

            # less n-squared
            if completed:
                for n in sorted(self.dependencies.keys()):
                    intersect = set.intersection(self.dependencies[n], completed)
                    if intersect:
                        newDepUpdateTime = max(
                            depUpdateTimes[n],
                            *[self.resources[k].updateTime() for k in intersect],
                        )
                        depUpdateTimes[n] = newDepUpdateTime
                        self.dependencies[n] = self.dependencies[n] - intersect

            # sleep if there is still work AND things are still running
            if len(self.dependencies) and len(running):
                sleep(checkFrequency)


if __name__ == "__main__":
    parser = OptionParser("[options] folder[ folder2[...]]")
    parser.add_option(KVOption(
        "--var",
        metavar="KEY=VALUE",
        help="Define one or more key=value pairs which will be available "
             "as if they were declared in a global vars file. "
             "Always takes precedence over any var in global vars. Values may be "
             "json list. Supported lists are same as list types supported "
             "in global, local, or template vars files   "
    ))

    parser.add_option("--execute", dest="execute",
                      action="store_true", default=False,
                      help="'execute' mode.  Accepts a list of folders "
                           "- folder[ folder2[...]]."
                      "Renders the templates found in those folders "
                      "and executes them in proper order "
                           "of their dependencies")
    parser.add_option("--dotml", dest="dotml",
                      action="store_true", default=False,
                      help="Generate dot ml graph of dag of execution.  "
                           "For more info on dot and graphviz, "
                           "checkout https://www.graphviz.org/")
    parser.add_option("--show", dest="show",
                      action="store_true", default=False,
                      help="Show the dependency tree")
    parser.add_option("--dumpToFolder", dest="dumpToFolder",
                      default=None,
                      help="Dump expanded templates to disk to the "
                           "folder as files using the key of resource and "
                           "content of template.  ")
    parser.add_option("--showJobs", dest="showJobs",
                      action="store_true", default=False,
                      help="Show the jobs")
    parser.add_option("--defaultDataset", dest="defaultDataset",
                      help="The default dataset which will be used if "
                           "file definitions don't specify one.  This "
                           "will be automatically created during "
                           "'execute' mode")
    parser.add_option("--maxConcurrent", dest="maxConcurrent", type=int,
                      default=10, help="The maximum number of bq or "
                                       "other jobs to run in parallel.")
    parser.add_option("--defaultProject", dest="defaultProject",
                      help="The default project which will be used if "
                           "file definitions don't specify one")
    parser.add_option("--checkFrequency", dest="checkFrequency", type=int,
                      default=10,
                      help="The loop interval between dependency tree"
                           " evaluation runs")

    parser.add_option("--maxRetry", dest="maxRetry", type=int,
                      default=2,
                      help="Relevant to 'execute' mode. The maximum "
                           "retries for any single resource "
                           "creation. Once this number is hit, "
                           "the program will exit non-zero")

    parser.add_option("--varsFile", dest="varsFile", type=str,
                      help="A json or yaml file whose data can be refered to in "
                           "view, query, and other templates.  Must be a simple "
                           "dictionary whose values are string, integers, "
                           "or arrays of strings and integers")

    parser.add_option("--bqClientLocation", type=str,
                      help="The location where datasets will be "
                           "created. i.e. us-east1, us-central1, etc",
                      default="US")

    parser.add_option("--print-global-args",
                      help="Creates a json output of the parsed global "
                           "args consumed from the command line",
                      action="store_true", default=False)

    (options, args) = parser.parse_args()

    FORMAT = '%(asctime)-15s %(clientip)s %(user)-8s %(message)s'
    logging.basicConfig(format=FORMAT)

    additional_args = {'location': options.bqClientLocation}
    kwargs = {}
    kwargs["dataset"] = options.defaultDataset
    kwargs["project"] = options.defaultProject

    globalVars = {}
    if options.varsFile:
        with open(options.varsFile) as f:
            globalVars = yaml.safe_load(f)

    vars = {}
    if options.var:
        vars = options.var
        # double check that if project is set, it must
        # be a single val of type string
        if "project" in vars and type(vars["project"]) != str:
            raise Exception("if you specify project as a var, it must be a simple string")

    globalVars = {**kwargs, **globalVars, **vars}

    loadClient = None
    gcsClient = None
    client = None
    bqJobs = None

    dryrun = False
    if options.dumpToFolder:
        dryrun = True

    if not dryrun:
        loadClient = Client(project=globalVars["project"], **additional_args)
        gcsClient = storage.Client(project=globalVars["project"])
        client = Client(**additional_args)
        if not options.defaultProject and not globalVars.get("project", None):
            client = Client(**additional_args)
            globalVars["project"] = client.project
        bqJobs = BqJobs(client)
        if options.execute:
            bqJobs.loadTableJobs()

    builder = DependencyBuilder(
        DelegatingFileSuffixLoader(
            uniontable=BqQueryTemplatingFileLoader(client, gcsClient,
                                                   bqJobs,
                                                   TableType.UNION_TABLE,
                                                   globalVars),
            unionview=BqQueryTemplatingFileLoader(client, gcsClient,
                                                  bqJobs,
                                                  TableType.UNION_VIEW,
                                                  globalVars),
            querytemplate=BqQueryTemplatingFileLoader(client, gcsClient,
                                                      bqJobs,
                                                      TableType.TABLE,
                                                      globalVars),
            view=BqQueryTemplatingFileLoader(client, gcsClient,
                                             bqJobs,
                                             TableType.VIEW,
                                             globalVars),
            # TODO: give better control over where localdata files end up
            localdata=BqDataFileLoader(loadClient,
                                       globalVars['dataset'],
                                       globalVars['project'],
                                       bqJobs),
            gcsdata=BqQueryTemplatingFileLoader(client, gcsClient,
                                                bqJobs,
                                                TableType.TABLE_GCS_LOAD,
                                                globalVars),
            bashtemplate=BqQueryTemplatingFileLoader(loadClient, gcsClient,
                                                     bqJobs,
                                                     TableType.BASH_TABLE,
                                                     globalVars),
            externaltable=BqQueryTemplatingFileLoader(loadClient, gcsClient,
                                                      bqJobs,
                                                      TableType.EXTERNAL_TABLE,
                                                      globalVars))
    )
    (resources, dependencies) = builder.buildDepend(args, dryrun=dryrun)
    executor = DependencyExecutor(resources, dependencies,
                                  maxRetry=options.maxRetry)

    if options.print_global_args:
        print(json.dumps(globalVars))
        exit(0)

    if options.execute:
        executor.execute(checkFrequency=options.checkFrequency, maxConcurrent=options.maxConcurrent)
    elif options.show:
        executor.show()
    elif options.dotml:
        executor.dotml()
    elif options.dumpToFolder:
        executor.dump(options.dumpToFolder)
    elif options.showJobs:
        print("showing jobs")
        for j in BqJobs(bigquery.Client(**additional_args)).jobs():
            if j.state in set(['RUNNING', 'PENDING']):
                print(j.name, j.state, j.errors)
    else:
        parser.print_help()
