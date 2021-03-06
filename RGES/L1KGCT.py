"""
This script defines a representation for an input .gct file containing
L1000-assay mRNA expression data. This representation assumes the format
as provided by the iLINCS browser, which can be downloaded here:
http://www.ilincs.org/ilincs/signaturesL1000/LDG-1188/search/
"""

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
import cmapPy.pandasGEXpress as GEX
import cmapPy.pandasGEXpress.write_gctx as write_gctx
import pandas as pd
import time

class MultiL1KGCT:
    """
    This class represents a .gct file for 1 or more signatures from the
    L1000 assay drug signature database. 
    """
    def __init__(self, path, normalized=False):
        """
        Initalizes a MultiL1KGCT instance and call the load function
        on path

            path (str): A path to a file with one more L1000 signatures
            normalize (bool): If true, apply normalization as described below
                            in self.normalize()

            returns: None
        """
        self.names = []
        self.metadata = {}  #{sig: {metadata}}
        self.data = None  #pd.DataFrame

        self.path = path
        self.normalized = normalized

        if path != None:
            self.load()
            if self.normalized:
                self.normalize()

    """
    Loading Data
    """

    def load(self):
        """
        Reads data from self.path and populates self.data and metadata fields
        for each LINCS signature in the file

            returns: None
        """
        sig_md = {}
        self.data = pd.read_csv(self.path, sep='\t', skiprows=[0,1,3,4,5,6,7,8,9])
        self.data['ID_geneid'] = self.data['ID_geneid'].astype(str)
        for i, line in enumerate(open(self.path)):
            if i in [0,1]:
                continue
            if i > 9:
                break
            lv = line.strip('\n').split('\t')
            sig_md[lv[0]] = lv[4:]
        for i, sig in enumerate(sig_md['id']):
            self.metadata[sig] = {key: sig_md[key][i] for key in sig_md.keys()
                                        if key != "id"}
            self.data = self.data.sort_values(by=sig)
            self.data[sig+'_drug_rank'] = range(1, len(self.data)+1)

    """
    Normalize Data
    """

    def normalize(self):
        """
        This function transforms self.data such that each value
        becomes a z-score constrained between [-3, 3] and then shifted by 6
        such that all values are in the interval [0, 6]

            returns: None
        """
        no_change = lambda x: x
        zscore = lambda x: (x-x.mean())/x.std(ddof=0)
        norm = lambda x: 6 if x>3 else (0 if x<-3 else x+3)

        col_d = {c: zscore if c in self.metadata.keys() else no_change for c in list(self.data)}
        self.data = self.data.transform(col_d)

        col_d = {c: norm if c in self.metadata.keys() else no_change for c in list(self.data)}
        self.data = self.data.transform(col_d)

class L1KGCTX:
    """
    This class overrides the loading methods for MultiL1KGCT to load data from
    a gctx binary file using the cmapPy parsers

    Note: Writing .gctx files does not work as of 2018-04-04

    see https://github.com/cmap/cmapPy/issues/25
    """
    def __init__(self, path):
        """
        Initializes an L1KGCTX instance - calls cmapPy parsers

            path (str): A path to a .gctx file

            returns: None
        """
        self.path = path

        if self.path != None:
            self.load()

    """
    Loading Data
    """

    def load(self):
        """
        Calls the cmapPy gctx parser, retrieves matrix and metadata

            returns: None
        """
        self.data = GEX.parse(self.path).data_df

        ##Dealing with cmapPy data type instability:
        rows = list(map(lambda x: x[2:-1], list(self.data.index)))
        self.data.index = rows
        columns = list(map(lambda x: x[2:-1], list(self.data)))
        self.data.columns = columns

if __name__ == "__main__":
    DIR = "/scratch/alexw/l1k/"    

    lincs_ranked_path = "/scratch/alexw/l1k/LINCS_FULL_GEO/GSE70138_2017-03-06_landmarks_ranked_n118050x972.gctx"
    gctx = L1KGCTX(lincs_ranked_path)
    print(gctx.data)
    print(gctx.data.index.dtype)
