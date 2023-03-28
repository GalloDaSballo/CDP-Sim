import os

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

sns.set_style("whitegrid")
plt.rcParams["figure.figsize"] = 15, 30


class GenericEntry:
    def __init__(self, values):
        self.values = values

    def __repr__(self):
        return str(self.__dict__)

    def to_entry(self):
        return self.values


class GenericLogger:
    def __init__(self, path, headers):
        self.path = "logs/" + path + "/"
        self.entries = []
        self.headers = headers
        os.makedirs(self.path, exist_ok=True)

    def add_entry(self, entry: GenericEntry):
        self.entries.append(entry)

    def __repr__(self):
        return str(self.__dict__)

    def to_csv(self):
        # Create a file with current time as name
        now = pd.Timestamp.now()

        df = pd.DataFrame(self.entries, columns=self.headers)

        # Divide actors as class clusters for now
        df_system = df[df["Name"].str.contains("System")]
        df_users = df[df["Name"].str.contains("User")]
        df_troves = df[df["Name"].str.contains("Trove")]

        new_directory = f"{self.path}/{now}"
        if not os.path.exists(new_directory):
            os.makedirs(new_directory)

        df_system.to_csv(f"{new_directory}/system.csv", index=False)
        df_users.to_csv(f"{new_directory}/users.csv", index=False)
        df_troves.to_csv(f"{new_directory}/troves.csv", index=False)

        return df_system, df_users, df_troves

    def plot_price_line_graph(self, df):
        plt.plot(df["Time"], df["Amount"])
        plt.xlabel("System Time")
        plt.ylabel("Oracle Price")
        plt.show()
        