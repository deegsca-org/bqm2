import logging
import sys
import unittest

from unittest import mock
from unittest.mock import Mock
from google.cloud.storage import Client, Blob, Bucket

from python.manifest_generator import * 


class Test(unittest.TestCase):
    def test_split_uri(self):
        bucket, prefix = split_uri("s3://bucket/prefix/")
        self.assertEqual(bucket, "bucket")
        self.assertEqual(prefix, "prefix")

    def test_bad_input(self):
        manifest_path = "s3://bucket/prefix/manifest/"
        generate_manifest("s3://bucket/prefix/", manifest_path, manifest_path, True)
        self.fail(f"The manifest-path argument provided ({manifest_path}) cannot end with a trailing slash")

    def test_entries(self):
        suffix = "txt"
        blobs = ["file.txt"]
        res = create_entries(blobs, suffix)
        self.assertEqual(res['entries']['content_length'], 1)
        self.assertEqual(res['entries']['mandatory'], True)
        self.assertEqual(res['entries']['url'], f"s3://bucket/file.txt")

    @mock.patch('google.cloud.storage.Client')
    @mock.patch('google.cloud.storage.Blob')
    @mock.patch('google.cloud.storage.Bucket')
    def test_blob(self, mock_client: Client, mock_blob: Blob, mock_bucket: Bucket):
        mock_client.bucket = mock_bucket
        pass


if __name__ == '__main__':
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
    unittest.main()