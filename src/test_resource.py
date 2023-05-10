import unittest

import mock
from google.cloud.bigquery.client import Client
from google.cloud.bigquery.dataset import Dataset
from google.cloud.bigquery.job import SourceFormat
from google.cloud.bigquery.job import QueryJob
from google.cloud.bigquery.table import Table

import resource
from resource import strictSubstring, \
    BqDatasetBackedResource, BqViewBackedTableResource, \
    BqQueryBasedResource, BqDataLoadTableResource

import pytest


class Test(unittest.TestCase):

    def test_getFiltered(self):
        self.assertTrue(resource.getFiltered(".") == ". ")
        self.assertTrue(resource.getFiltered("@") == " ")

    def test_strictSubstring(self):
        self.assertTrue(strictSubstring("A", "AA"))
        self.assertFalse(strictSubstring("A", "A"))
        self.assertTrue(strictSubstring("A", " Asxx "))

    @mock.patch('google.cloud.bigquery.Client')
    @mock.patch('google.cloud.bigquery.table.Table')
    @mock.patch('google.cloud.bigquery.table.Table')
    @mock.patch('google.cloud.bigquery.Dataset')
    def test_realExampleOfDependencyDiscoveryMis(self, mock_Client: Client,
                                               mock_Table1: Table,
                                               mock_Table2: Table,
                                               mock_Dataset: Dataset):
        input1 = "SELECT 1"""
        input2 = "FROM build_production_20230201.business_emails_fill_rates"""
        mock_Dataset.dataset_id = "build_production_20230201"
        mock_Table1.table_id = "business_emails_fill_rates"
        mock_Table1.dataset_id = "build_production_20230201"
        mock_Table2.table_id = "business_emails_fill_rates_delta"
        mock_Table2.dataset_id = "build_production_20230201"

        query1 = BqQueryBasedResource([input1], mock_Table1, mock_Client)
        query2 = BqQueryBasedResource([input2], mock_Table2, mock_Client)
        dataset = BqDatasetBackedResource(mock_Dataset, mock_Client)
        dataset.dataset = mock_Dataset
        self.assertFalse(dataset.dependsOn(query1))
        self.assertTrue(query1.dependsOn(dataset))

        self.assertTrue(query2.dependsOn(query1))

    @mock.patch('google.cloud.bigquery.Client')
    @mock.patch('google.cloud.bigquery.table.Table')
    @mock.patch('google.cloud.bigquery.Dataset')
    def test_realExampleOfSubstringingMisMatch(self, mock_Client: Client,
                                               mock_Table: Table,
                                               mock_Dataset: Dataset):
        input_ = "FROM taxonomy.url_kw_expansion_assignment_descendant """
        mock_Dataset.dataset_id = "taxonomy"
        mock_Table.table_id = "atable_on_something"
        mock_Table.dataset_id = "taxonomy"
        mock_Client.get_dataset = mock_Dataset

        query = BqQueryBasedResource([input_], mock_Table, mock_Client)
        dataset = BqDatasetBackedResource(mock_Dataset, mock_Client)
        dataset.dataset = mock_Dataset

        self.assertFalse(dataset.dependsOn(query))
        self.assertTrue(query.dependsOn(dataset))

    @mock.patch('google.cloud.bigquery.Client')
    @mock.patch('google.cloud.bigquery.Client')
    @mock.patch('google.cloud.bigquery.table.Table')
    def test_ComplicatedlegacyBqQueryDependsOnFunc(self, mock_Client:
    Client,
                                        mock_Table: Table,
                                        mock_Table2: Table):
        mock_Table.project_id = "yourproject:qualifier"
        mock_Table.table_id = "url_taxonomy_assignment_ranked_url_title_tokens_kw_20170601"
        mock_Table.dataset_id = "test"
        query = """#standardSQL

SELECT *
FROM (
(select * from `yourproject:qualifier.test.url_taxonomy_assignment_0_url_title_tokens_kw_20170601`)
union all
(select * from `yourproject:qualifier.test.url_taxonomy_assignment_1_url_title_tokens_kw_20170601`)
union all
(select * from `yourproject:qualifier.test.url_taxonomy_assignment_2_url_title_tokens_kw_20170601`)
union all
(select * from `yourproject:qualifier.test.url_taxonomy_assignment_3_url_title_tokens_kw_20170601`)
union all
(select * from `yourproject:qualifier.test.url_taxonomy_assignment_4_url_title_tokens_kw_20170601`)
union all
(select * from `yourproject:qualifier.test.url_taxonomy_assignment_5_url_title_tokens_kw_20170601`)
union all
(select * from `yourproject:qualifier.test.url_taxonomy_assignment_6_url_title_tokens_kw_20170601`)
union all
(select * from `yourproject:qualifier.test.url_taxonomy_assignment_7_url_title_tokens_kw_20170601`)
union all
(select * from `yourproject:qualifier.test.url_taxonomy_assignment_8_url_title_tokens_kw_20170601`)
union all
(select * from `yourproject:qualifier.test.url_taxonomy_assignment_9_url_title_tokens_kw_20170601`)
)
"""

        left = BqQueryBasedResource([query,], mock_Table, mock_Client)

        mock_Table2.table_id = "url_taxonomy_assignment_8_url_title_tokens_kw_20170601"
        mock_Table2.dataset_id = "test"
        query2 = """select
    *,
    row_number() over (partition by id, description order by overlap desc) id_to_urls_rank
from (
select
  group_concat(unique(kw)) matching_kw,
  id,
  description,
  url,
  sum(float(tscore) * float(fscore)) overlap
from (
select id, description, url, kw, fscore, score tscore from [yourproject:qualifier:test.url_title_tokens_kw_20170601]
join each
(select id, description, feature, score fscore from
[yourproject:qualifier:test.kw_features_ranked]
where abs(hash(id)) % 10 == 8 ) fkw
on kw = fkw.feature
group each by id, description, url, kw, tscore, fscore
)
group each by id, description, url
)
"""

        right = BqQueryBasedResource([query2], mock_Table2, mock_Client)
        self.assertTrue(left.dependsOn(right))
        self.assertFalse(right.dependsOn(left))

    @mock.patch('google.cloud.bigquery.Client')
    @mock.patch('google.cloud.bigquery.Client')
    @mock.patch('google.cloud.bigquery.table.Table')
    def test_legacyBqQueryDependsOnFunc(self, mock_Client: Client,
                                        mock_Table: Table,
                                        mock_Table2: Table):
        mock_Table.table_id = "v1_"
        mock_Table.dataset_id = "dset"
        query = "... yourproject:qualifier:mergelog.v1_], " \
                "DATE_ADD(CURRENT_TIMESTAMP(), -2, 'DAY'), ... "

        left = BqQueryBasedResource([query], mock_Table, mock_Client)

        mock_Table2.table_id = "v1_"
        mock_Table2.dataset_id = "mergelog"
        query2 = "select 1 as one"

        right = BqQueryBasedResource([query2], mock_Table2, mock_Client)
        self.assertTrue(left.dependsOn(right))
        self.assertFalse(right.dependsOn(left))


    @mock.patch('google.cloud.bigquery.Client')
    @mock.patch('google.cloud.bigquery.table.Table')
    @mock.patch('google.cloud.bigquery.Dataset')
    def test_DatasetDependency(self, mock_Client: Client,
                               mock_Table: Table, mock_Dataset: Dataset):
        mock_Dataset.dataset_id = "mergelog"
        mock_Table.table_id = "aview_on_something"
        mock_Table.dataset_id = "mergelog"

        dataset = BqDatasetBackedResource(mock_Dataset, mock_Client)
        dataset.dataset = mock_Dataset
        view = BqViewBackedTableResource(["select * from mergelog.foobar"],
                                         mock_Table, mock_Client)

        self.assertTrue(view.dependsOn(dataset))
        self.assertFalse(dataset.dependsOn(view))

    @mock.patch('google.cloud.bigquery.table.Table')
    def test_buildDataSetKey_(self, table):
        table.project = 'p'
        table.dataset_id = 'd'
        actual = resource._buildDataSetKey_(table)
        expected = 'd'
        self.assertEqual(actual, expected)

    @mock.patch('google.cloud.bigquery.table.Table')
    def test_buildTableKey_(self, table: Table):
        table.project = 'p'
        table.dataset_id = 'd'
        table.table_id = 't'
        actual = resource._buildDataSetTableKey_(table)
        expected = 'd:t'
        self.assertEqual(actual, expected)

    # @mock.patch('google.cloud.bigquery.Client')
    # @mock.patch('google.cloud.iterator.Iterator')
    # @mock.patch('google.cloud.bigquery.job.QueryJob')
    # @mock.patch('google.cloud.bigquery.table.Table')
    # def testBqJobsLoadTableJobs(self, client: Client, it: Iterator,
    #                             job: QueryJob, table: Table):
    #     client.list_jobs.return_value = it
    #     it.next_page_token = None

    #     job.destination = table
    #     table.dataset_id = "d"
    #     table.friendly_name = "t"
    #     table.project = "p"

    #     jobs = BqJobs(client, {})
    #     client.list_jobs.return_value = it
    #     jobs.loadTableJobs()
    #     client.list_jobs.assert_has_calls([
    #         mock.call(max_results=1000, state_filter='pending'),
    #         mock.call(max_results=1000, state_filter='running')], any_order=True)

    # @mock.patch('google.cloud.bigquery.Client')
    # @mock.patch('google.cloud.iterator.Iterator')
    # @mock.patch('google.cloud.bigquery.job.QueryJob')
    # @mock.patch('google.cloud.bigquery.table.Table')
    # def testBqJobsLoadTableJobsRuning(self, client: Client, it: Iterator,
    #                                   job: QueryJob, table: Table):

    #     job.destination = table
    #     table.dataset_id = "d"
    #     table.friendly_name = "t"
    #     table.project = "p"

    #     jobs = BqJobs(client, {})
    #     it.page_number = 0
    #     it.next_page_token = False
    #     client.list_jobs.return_value = it

    #     it.__iter__ = Mock(return_value=iter([job]))

    #     jobs.__loadTableJobs__('running')
    #     self.assertEqual(jobs.tableToJobMap['p:d:t'], job)


    def testDetectSourceFormatForJson(self):
        self.assertEqual(
            SourceFormat.NEWLINE_DELIMITED_JSON,
            BqDataLoadTableResource.detectSourceFormat("[]"))

    def testDetectSourceFormatForCsv(self):
        self.assertEqual(
            SourceFormat.CSV,
            BqDataLoadTableResource.detectSourceFormat(
            "a"))


    #def test_print_non_error_result_to_stdout(capsys):
    #gcs_blob_path = "path/of/blob.txt"
    #gcs_bucket_name = "bucket"
    #target_s3_prefix = "s3://bucket/prefix/"
    #operation = main.Operation.copy
    #expected_msg = f"{operation} gs://bucket/path/of/blob.txt s3://bucket/prefix/blob.txt"
    #msg = main.build_pubsub_message(gcs_blob_path, gcs_bucket_name, target_s3_prefix, operation)
    #out, err = capsys.readouterr()
    #assert expected_msg in out


    # @mock.patch('google.cloud.bigquery.job.LoadTableFromStorageJob')
    # def test_HandleLoadTableOptionSourceFormat(self, sj):
    #     options = {
    #         "source_format": "NEWLINE_DELIMITED_JSON"
    #     }

    #     processLoadTableOptions(options, sj)
    #     self.assertEqual(sj.write_disposition, SourceFormat.NEWLINE_DELIMITED_JSON)

    # @mock.patch('google.cloud.bigquery.job.LoadTableFromStorageJob')
    # def test_HandleLoadTableOptionWriteDisposition(self, sj):
    #     options = {"write_disposition": "WRITE_TRUNCATE"}

    #     processLoadTableOptions(options, sj)
    #     self.assertEqual(sj.write_disposition,
    #                       WriteDisposition.WRITE_TRUNCATE)

    # @mock.patch('google.cloud.bigquery.job.LoadTableFromStorageJob')
    # def test_HandleLoadTableOptionInvalidDispositionOrFormat(self, sj):
    #     options = {"write_disposition": "invalid"}

    #     try:
    #         processLoadTableOptions(options, sj)
    #         self.fail("unknown value")
    #     except KeyError:
    #         pass

    #     options = {"source_format": "invalid"}
    #     try:
    #         processLoadTableOptions(options, sj)
    #         self.fail("unknown value")
    #     except KeyError:
    #         pass


def testPrintErrorResultToStderr(capsys):
    err_msg = "got error"
    import google.cloud.bigquery.job
    mock_error_job = mock.create_autospec(google.cloud.bigquery.job.QueryJob)
    mock_error_job.reload.return_value = None
    mock_error_job.job_id = "some-random-id"
    mock_error_job.state = "FAILED"
    mock_error_job.error_result = err_msg
    resource.isJobRunning(mock_error_job)
    out, err = capsys.readouterr()
    assert err is not None
    assert not out


def testPrintNoErrorResultToStdout(capsys):
    import google.cloud.bigquery.job
    mock_error_job = mock.create_autospec(google.cloud.bigquery.job.QueryJob)
    mock_error_job.reload.return_value = None
    mock_error_job.job_id = "some-random-id"
    mock_error_job.state = "DONE"
    mock_error_job.errors = None
    mock_error_job.error_result = None
    resource.isJobRunning(mock_error_job)
    out, err = capsys.readouterr()
    assert not err
    assert out is not None

#if __name__ == '__main__':
#    unittest.main()
