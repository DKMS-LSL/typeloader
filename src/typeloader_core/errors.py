'''
Created on 26.11.2018

contains custom exception classes

@author: schoene
'''

class IncompleteSequenceError(Exception):
    """raised when TypeLoader encounters a sequence without a complete 3'UTR
    """
    def __init__(self, missing_bp):
        self.missing_bp = missing_bp
        self.msg = "This sequence misses the first {} bp!\nTypeLoader requires the full 5' UTR to be included in the sequence.".format(missing_bp)

class BothAllelesNovelError(Exception):
    """raised when TypeLoader tries to create an IPD file for an allele where both alleles of this locus are novel
    but TypeLoader can't figure out which of the pretyping alleles is 'self' and which is 'other'
    """
    def __init__(self, allele):
        self.allele = allele
