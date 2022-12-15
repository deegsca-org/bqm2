from google.cloud.bigquery import CopyJobConfig, CreateDisposition

import loader
import yaml

class BaseJobConfigLoader(loader.FileLoader):
    def __init__(self):
        pass

    def load(self, file) -> list:
        """

        Args:
            file: The yaml file containing a template of
            one of QueryJobConfig, LoadJobConfig, ExtractJobConfig, CopyJobConfig

        Returns:

        """

        c = CopyJobConfig()

        with open(file, 'r') as f:
            d = yaml.safe_load(f)

        print(d)
        return []

    def handles(self, file) -> bool:
        """ Given a file, the resource should answer true or false
        whether or not this loader can handle loading that file
        """
        pass
