import csv
import os
import time
from random import random

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

sns.set_style('whitegrid')
plt.rcParams['figure.figsize'] = 15, 30

class GenericEntry():
    def __init__(
        self,
        values
    ):
      self.values = values

    def __repr__(self):
        return str(self.__dict__)

    def to_entry(self):
        return self.values

class GenericLogger:
    def __init__(self, path, headers):
        self.path = 'logs/' + path + '/'
        self.entries = []
        self.headers = headers
        os.makedirs(self.path, exist_ok=True)

    def add_entry(self, entry: GenericEntry):
        self.entries.append(entry)

    def __repr__(self):
        return str(self.__dict__)

    def to_csv(self):
        # Create a file with current time as name
        filename = f'{self.path}/{pd.Timestamp.now()}.csv'

        with open(filename, 'w', encoding='UTF8') as f:
            writer = csv.writer(f)

            # write the header
            writer.writerow(self.headers)

            # write the data
            for entry in self.entries:
                writer.writerow(entry.to_entry())