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
        self.msg = "This sequence misses the first {} bp!\nTypeLoader requires the full 3' UTR to be included in the sequence.".format(missing_bp)
        