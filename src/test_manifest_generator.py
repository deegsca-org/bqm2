import json
import logging
import sys
import unittest
import pytest

from unittest import mock
from google.cloud.storage import Client, Blob, Bucket
from unittest.mock import MagicMock

from manifest_generator import * 


class Test(unittest.TestCase):

    test_blob1 = type('Blob', (), {})()
    test_blob1.name = "blob1.txt"
    test_blob1.size = "1"
    test_blob2 = type('Blob', (), {})()
    test_blob2.name = "blob2.txt"
    test_blob2.size = "1"

    @pytest.fixture(autouse=True)
    def capsys(self, capsys):
        self.capsys = capsys

    def test_split_uri(self):
        bucket, prefix = split_uri("s3://bucket/prefix/")
        self.assertEqual(bucket, "bucket")
        self.assertEqual(prefix, "prefix/")

    def test_bad_input(self):
        manifest_path = "s3://bucket/prefix/manifest/"
        try:
            generate_manifest("s3://bucket/prefix/", manifest_path, None, manifest_path, True)
            self.fail(f"The manifest-path argument provided ({manifest_path}) cannot end with a trailing slash")
        except:
            pass

    @mock.patch('manifest_generator.list_blobs', return_value=[test_blob1, test_blob2], autospec=True)
    def test_good_input(self, mock):
        manifest_path = "s3://bucket/prefix/manifest"
        target_prefix = 's3://s3_bucxket/prefix/'
        generate_manifest("s3://bucket/prefix/", ".txt", target_prefix, manifest_path, True)
        out, err = self.capsys.readouterr()
        assert target_prefix + self.test_blob1.name in out
        assert target_prefix + self.test_blob2.name in out

    def test_entries(self):
        suffix = "txt"
        blobs = ["file.txt"]
        res = create_entries(blobs, suffix)
        self.assertEqual(res['entries'][0]['meta']['content_length'], 1)
        self.assertEqual(res['entries'][0]['mandatory'], True)
        self.assertEqual(res['entries'][0]['url'], f"s3://bucket/file.txt")

    def test_string(self):
        output_dict = {
            "entries": [
                {
                    "meta": 1,
                    "mandatory": True,
                    "url": "s3//bucket/manifest"
                }
            ]
        }
        output_dict_string = json.dumps(output_dict, sort_keys=True)
        self.assertEqual(output_dict_string, '{"entries": [{"mandatory": true, "meta": 1, "url": "s3//bucket/manifest"}]}')


#if __name__ == '__main__':
#    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
#    unittest.main()
