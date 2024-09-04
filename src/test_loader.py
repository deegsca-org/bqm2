import json
import unittest

from google.cloud.bigquery.client import Client
from google.cloud.bigquery.schema import SchemaField
from google.cloud.storage import Client as GcsClient


import mock
from mock.mock import MagicMock
import logging

import date_formatter_helper
from loader import DelegatingFileSuffixLoader, FileLoader, \
    parseDatasetTable, \
    parseDataset, BqQueryTemplatingFileLoader, TableType, loadSchemaFromString
from resource import BqJobs, BqViewBackedTableResource, \
    BqQueryBackedTableResource


class Test(unittest.TestCase):

    @mock.patch('google.cloud.bigquery.Client')
    @mock.patch('google.cloud.storage.Client')
    @mock.patch('resource.BqJobs')
    def test_ToggleToTableForTemplatingLoader(self, bqClient: Client, gcsClient: GcsClient,
                                                bqJobs: BqJobs):
        self.toggleToTableOrViewForTemplatingLoader(bqClient, gcsClient, bqJobs,
                                                    TableType.TABLE,
                                                    BqQueryBackedTableResource)

    @mock.patch('google.cloud.bigquery.Client')
    @mock.patch('google.cloud.storage.Client')
    @mock.patch('resource.BqJobs')
    def test_ToggleToViewForTemplatingLoader(self, bqClient: Client, gcsClient: GcsClient,
                                                  bqJobs: BqJobs):
        self.toggleToTableOrViewForTemplatingLoader(bqClient, gcsClient, bqJobs,
                                                    TableType.VIEW,
                                                    BqViewBackedTableResource)

    def toggleToTableOrViewForTemplatingLoader(self, bqClient: Client, gcsClient: GcsClient,
                                                    bqJobs: BqJobs,
                                                    tableType: TableType,
                                                    theType):

        bqClient.dataset('adataset').table('atable').table_id = 'atable'
        bqClient.dataset('adataset').table('atable').dataset_id = \
            'adataset'
        bqClient.dataset('adataset').table('atable').project = 'aproject'

        ldr = BqQueryTemplatingFileLoader(bqClient, gcsClient, bqJobs,
                                          tableType,
                                          {"dataset": "dataset"})
        self.assertEqual(ldr.tableType, tableType)
        out = {}
        ldr.processTemplateVar({ "dataset": "dataset", "table": "foo"},
                               "select * from fiddle.sticks",
                               "afilepath", 0, out)
        key = "adataset:atable"
        self.assertTrue(key in out)
        self.assertTrue(isinstance(out[key], theType))


    @mock.patch('google.cloud.bigquery.Client')
    @mock.patch('google.cloud.storage.Client')
    @mock.patch('resource.BqJobs')
    def test_IdenticalButDuplicateDefinitionsAllowed(self, bqClient: Client, gcsClient: GcsClient,
                                                     bqJobs: BqJobs):

        bqClient.dataset('adataset').table('atable').table_id = 'atable'
        bqClient.dataset('adataset').table('atable').dataset_id = \
            'adataset'
        bqClient.dataset('adataset').table('atable').project = 'aproject'

        ldr = BqQueryTemplatingFileLoader(bqClient, gcsClient, bqJobs,
                                          TableType.VIEW,
                                          {"dataset": "dataset"})
        out = {}
        # the introduction of [a,b] because they are unused should complete without error
        ldr.processTemplateVar({ "dataset": "dataset", "table": "foo", "unusedkey": ["a", "b"]},
                               "select * from fiddle.sticks",
                               "afilepath", 0, out)


    @mock.patch('google.cloud.bigquery.Client')
    @mock.patch('google.cloud.storage.Client')
    @mock.patch('resource.BqJobs')
    def test_NotIdenticalButDuplicateKeysAreNotAllowed(self, bqClient: Client, gcsClient: GcsClient,
                                                     bqJobs: BqJobs):

        bqClient.dataset('adataset').table('atable').table_id = \
            'atable'
        bqClient.dataset('adataset').table('atable').dataset_id = \
            'adataset'
        bqClient.dataset('adataset').table('atable').project = 'aproject'

        ldr = BqQueryTemplatingFileLoader(bqClient, gcsClient, bqJobs,
                                          TableType.VIEW,
                                          {"dataset": "dataset"})
        out = {}
        # the introduction of [a,b] because they are unused should complete without error
        ldr.processTemplateVar({"dataset": "dataset", "table": "foo"},
                               "select * from fiddle.sticks",
                               "afilepath", 0, out)

        try:
            ldr.processTemplateVar({"dataset": "dataset", "table": "foo"},
                           "select * from fiddle.poles",
                           "afilepath", 0, out)
            self.fail("we should have failed here!")
        except Exception:
            pass

    def test_DelegatingFileLoader_EmptyLoader(self):
        try:
            DelegatingFileSuffixLoader()
            self.assertTrue(False, "Should have thrown exception on empty constructor")
        except:
            pass

    def test_DelegatingFileLoaderValidLoader(self):
        aLoader = FileLoader()
        DelegatingFileSuffixLoader(query=aLoader)

    def test_DelegatingFileLoaderInValidLoader(self):
        class Foo:
            pass

        aLoader = Foo()
        try:
            DelegatingFileSuffixLoader(query=aLoader)
            self.assertTrue(False, "Should have failed")
        except ValueError:
            pass

    def test_DelegatingFileLoaderParseInvalidSuffix(self):
        aLoader = FileLoader()
        try:
            DelegatingFileSuffixLoader(query=aLoader).load("nosuffixfile", True)
            self.assertTrue(False, "Should have failed with index error switched to value error")
        except ValueError:
            pass


    def test_DelegatingFileLoaderParseSuffix(self):
        aLoader = FileLoader()
        def f(file, dryrun):
            return True
        aLoader.load = f
        self.assertTrue(DelegatingFileSuffixLoader(query=aLoader).load("nosuffixfile.query", True))

    def testParseDataSetTable(self):
        ret = parseDatasetTable("a/b/dataset.table.suffix", "default",
                          "defaultProject")
        assert ret.__str__() == "defaultProject.dataset.table"

    def testParseDataSetTableWithoutDataset(self):
        ret = parseDatasetTable("a/b/table.suffix", "dataset",
                                "defaultProject")

        assert ret.__str__() == "defaultProject.dataset.table"

    @mock.patch('google.cloud.bigquery.Client')
    def testParseDataSetTableWithoutDefaultDataset(self, mock_client):
        try:
            parseDatasetTable("a/b/table.suffix", None, mock_client)
            self.assertTrue(False)
        except:
            pass

    def testParseDataSet(self):
        self.assertEqual(parseDataset("a/b/dataset.suffix"), "dataset")

    def testParseSchemaString(self):
        expected = [SchemaField("a", "int"), SchemaField("b", "string")]
        result = loadSchemaFromString("a:int,b:string")
        self.assertEqual(expected, result)

    def testParseSchemaJsonString(self):
        # note, we just use any valid json here
        # bq api will bomb out on invalid json
        expected = []
        result = loadSchemaFromString("[]")
        self.assertEqual(expected, result)

    def testExplodeTemplateVarsArray(self):
        from datetime import datetime, timedelta

        base = datetime.strptime("20210203", "%Y%m%d")
        n = datetime.now()
        offset = (n - base).days
        left = n - timedelta(days=offset)
        right = n - timedelta(days=offset+1)

        expectedDt = [dt.strftime("%Y%m%d") for dt in [left, right]]
        expectedY = [dt.strftime("%Y") for dt in [left, right]]
        expectedM = [dt.strftime("%m") for dt in [left, right]]
        expectedD = [dt.strftime("%d") for dt in [left, right]]
        expectedYY = [dt.strftime("%y") for dt in [left, right]]
        expectedmmm = [dt.strftime("%b").lower() for dt in [left, right]]
        expectedMMM = [dt.strftime("%b").upper() for dt in [left, right]]
        expectedMmm = [dt.strftime("%b") for dt in [left, right]]
        expectedq1 = [date_formatter_helper.quarter(dt, 1).strftime("%m") for dt in [left, right]]
        expectedq2 = [date_formatter_helper.quarter(dt, 2).strftime("%m") for dt in [left, right]]
        expectedq3 = [date_formatter_helper.quarter(dt, 3).strftime("%m") for dt in [left, right]]
        expectedq1yyyy = [date_formatter_helper.quarter(dt, 1).strftime("%Y") for dt in [left, right]]
        expectedq2yyyy = [date_formatter_helper.quarter(dt, 2).strftime("%Y") for dt in [left, right]]
        expectedq3yyyy = [date_formatter_helper.quarter(dt, 3).strftime("%Y") for dt in [left, right]]
        expectedq1dd = [date_formatter_helper.quarter(dt, 1).strftime("%d") for dt in [left, right]]
        expectedq2dd = [date_formatter_helper.quarter(dt, 2).strftime("%d") for dt in [left, right]]
        expectedq3dd = [date_formatter_helper.quarter(dt, 3).strftime("%d") for dt in [left, right]]

        one = {
            "yyyymmdd_yyyy": expectedY[0],
            "yyyymmdd_mm": expectedM[0],
            "yyyymmdd_dd": expectedD[0],
            "yyyymmdd_yy": expectedYY[0],
            "yyyymmdd_mmm": expectedmmm[0],
            "yyyymmdd_MMM": expectedMMM[0],
            "yyyymmdd_Mmm": expectedMmm[0],
            'yyyymmdd_qm1_mm': expectedq1[0],
            'yyyymmdd_qm2_mm': expectedq2[0],
            'yyyymmdd_qm3_mm': expectedq3[0],
            'yyyymmdd_qm1_yyyy': expectedq1yyyy[0],
            'yyyymmdd_qm2_yyyy': expectedq2yyyy[0],
            'yyyymmdd_qm3_yyyy': expectedq3yyyy[0],
            'yyyymmdd_qm1_dd': expectedq1dd[0],
            'yyyymmdd_qm2_dd': expectedq2dd[0],
            'yyyymmdd_qm3_dd': expectedq3dd[0],

        }

        two = {
            "yyyymmdd_yyyy": expectedY[1],
            "yyyymmdd_mm": expectedM[1],
            "yyyymmdd_dd": expectedD[1],
            "yyyymmdd_yy": expectedYY[1],
            "yyyymmdd_mmm": expectedmmm[1],
            "yyyymmdd_MMM": expectedMMM[1],
            "yyyymmdd_Mmm": expectedMmm[1],
            'yyyymmdd_qm1_mm': expectedq1[1],
            'yyyymmdd_qm2_mm': expectedq2[1],
            'yyyymmdd_qm3_mm': expectedq3[1],
            'yyyymmdd_qm1_yyyy': expectedq1yyyy[1],
            'yyyymmdd_qm2_yyyy': expectedq2yyyy[1],
            'yyyymmdd_qm3_yyyy': expectedq3yyyy[1],
            'yyyymmdd_qm1_dd': expectedq1dd[1],
            'yyyymmdd_qm2_dd': expectedq2dd[1],
            'yyyymmdd_qm3_dd': expectedq3dd[1],
        }

        template = {"folder": "afolder",
                    "foo": "bar_{folder}_{filename}",
                    "yyyymmdd": [-1 - offset, -offset]}


        result = BqQueryTemplatingFileLoader\
                .explodeTemplateVarsArray([template],
                'afolder', 'afile', {}, {"dataset": "adataset",
                                     "project": "aproject"})
        expected = [{'filename': 'afile', 'folder': 'afolder', 'dataset':
                    'adataset', 'yyyymmdd': expectedDt[1], 'foo':
                    'bar_afolder_afile', "table": "afile",
                     "project": "aproject", **two},
                    {'filename': 'afile', 'folder': 'afolder', 'dataset':
                    'adataset', 'yyyymmdd': expectedDt[0], 'foo':
                        'bar_afolder_afile', "table": "afile",
                     "project": "aproject", **one}]
        self.assertEqual(expected, result)

    @mock.patch('google.cloud.bigquery.Client')
    @mock.patch('google.cloud.storage.Client')
    @mock.patch('resource.BqJobs')
    def testProcessTemplateVarUnionView(self, bqClient, bqJobs, gcsClient):
        bqClient.dataset('adataset').table('atable').table_id = 'atable'
        bqClient.dataset('adataset').table('atable').dataset_id = \
            'adataset'
        bqClient.dataset('adataset').table('atable').project = 'aproject'
        unionViewLoader = BqQueryTemplatingFileLoader(bqClient, gcsClient, bqJobs, TableType.UNION_VIEW,
                                            {'dataset': 'default', 'project': 'aproject'})
        templateVar1 = {
            'table': 'atable',
            'dataset': 'adataset',
            "foo": "bar1",
        }
        templateVar2 = {
            'table': 'atable',
            'dataset': 'adataset',
            "foo": "bar2",
        }
        output = {}
        unionViewLoader.processTemplateVar(templateVar1, "select * from {foo}",
                                  "filepath", 0, output)
        unionViewLoader.processTemplateVar(templateVar2, "select * from {foo}",
                                           "filepath", 0, output)
        self.assertTrue(len(output))
        self.assertTrue("adataset:atable" in output)
        arsrc = output["adataset:atable"]
        self.assertEqual(arsrc.makeFinalQuery(), """select * from bar1\nunion all\nselect * from bar2""")

    @mock.patch('google.cloud.bigquery.Client')
    @mock.patch('google.cloud.storage.Client')
    @mock.patch('resource.BqJobs')
    def testProcessTemplateVarHappyPath(self, bqClient, bqJobs, gcsClient):

        bqClient.dataset('adataset').table('atable').table_id = \
            'atable'
        bqClient.dataset('adataset').table('atable').dataset_id = \
            'adataset'
        bqClient.dataset('adataset').table('atable').project = 'aproject'

        loader = BqQueryTemplatingFileLoader(bqClient, gcsClient, bqJobs,
                                             TableType.TABLE,
                                             {'dataset': 'default',
                                              'project': 'aproject'})
        templateVar = {
            'table': 'atable',
            'dataset': 'adataset',
            "foo": "bar",

        }
        output = {}
        loader.processTemplateVar(templateVar, "select * from {foo}",
                              "filepath", 0, output)
        self.assertTrue(len(output))
        self.assertTrue("adataset:atable" in output)
        arsrc = output["adataset:atable"]
        self.assertEqual(arsrc.queries[0], "select * from bar")

    @mock.patch('google.cloud.bigquery.Client')
    @mock.patch('google.cloud.storage.Client')
    @mock.patch('resource.BqJobs')
    def testProcessTemplateVarMissingDataset(self, bqClient, bqJobs,
                                             gcsClient):

        # templateVars: dict, template: str,
        # filePath: str, mtime: int, out: dict
        loader = BqQueryTemplatingFileLoader(bqClient, gcsClient, bqJobs,
                                             TableType.TABLE,{})
        templateVar = {
            'table': 'atable',
        }
        output = {}
        try:
            loader.processTemplateVar(templateVar, "select * from foo",
                                  "filepath", 0, output)
            self.fail("Should have thrown exception for missing dataset")
        except Exception:
            pass

    @mock.patch('google.cloud.bigquery.Client')
    @mock.patch('google.cloud.storage.Client')
    @mock.patch('resource.BqJobs')
    def testProcessTemplateVarMissingTable(self, bqClient, bqJobs,
                                           gcsClient):

        # templateVars: dict, template: str,
        # filePath: str, mtime: int, out: dict

        loader = BqQueryTemplatingFileLoader(bqClient, gcsClient, bqJobs,
                                             TableType.TABLE, 'default')
        templateVar = {
            'dataset': 'adataset',
        }
        output = {}
        try:
            loader.processTemplateVar(templateVar, "select * from foo",
                                  "filepath", 0, output)
            self.fail("Should have thrown exception for missing dataset")
        except Exception:
            pass

    def BuildJsonField(self, name: str, type: str, mode='NULLABLE',
                       description=None, fields=None):

        ret = {}
        ret['name'] = name
        ret['type'] = type

        if mode: ret['mode'] = mode
        if description: ret['description'] = description
        if fields: ret['fields'] = fields

        return ret

    def testSimpleLoadSchemaField(self):
        simpleField = [self.BuildJsonField("a", "float")]
        schema = loadSchemaFromString(json.dumps(simpleField))
        self.assertTrue(len(schema) == 1)
        self.assertTrue(schema[0].name == "a")

    def testComplexLoadSchemaField(self):
        log = logging.getLogger("TestLog")
        recordFields = [self.BuildJsonField("b", "float")]
        jsonFields = [
            self.BuildJsonField("c", "string", "repeated"),
            self.BuildJsonField("a", "record",
                                          fields=recordFields,
                                          mode='repeated')]
        schema = loadSchemaFromString(json.dumps(jsonFields))
        expectedStr = "[schemafield('c', 'string', 'repeated', none, none, (), none), schemafield('a', 'record', 'repeated', none, none, (schemafield('b', 'float', 'nullable', none, none, (), none),), none)]"

        actualStr = str(schema).lower()
        print(expectedStr)
        print(actualStr)
        self.assertEqual(expectedStr.lower(), actualStr)



    @mock.patch('google.cloud.bigquery.Client')
    @mock.patch('google.cloud.storage.Client')
    @mock.patch('resource.BqJobs')
    def testEmptyTableVar(self, bqClient, bqJobs, gcsClient):

        bqClient.dataset('adataset').table('atable').table_id = \
            'atable'
        bqClient.dataset('adataset').table('atable').dataset_id = \
            'adataset'
        bqClient.dataset('adataset').table('atable').project = 'aproject'

        loader = BqQueryTemplatingFileLoader(bqClient, gcsClient, bqJobs,
                                             TableType.TABLE,
                                             {'dataset': 'default',
                                              'project': 'aproject'})
        templateVar = {
            'table': '',
            'dataset': 'adataset',
            "foo": "bar",

        }
        output = {}
        loader.processTemplateVar(templateVar, "select * from {foo}",
                              "filepath", 0, output)
        self.assertTrue(len(output))



#if __name__ == '__main__':
#    import sys
#    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
#
#    unittest.main()
