'''
Created on 26.11.2018

contains custom exception classes

@author: schoene
'''

class IncompleteSequenceWarning(Exception):
    """raised when TypeLoader encounters a sequence without a complete 3'UTR
    """
    def __init__(self, missing_bp):
        self.missing_bp = missing_bp
        self.msg = "This sequence misses the first {} bp!\nDo you want to upload it anyway?\n(Note that IPD requires at least 1 bp per UTR to be contained in genomic sequences.)\n\n".format(missing_bp)
        self.msg += "Please consider carefully: this might lead to an incorrect closest allele being selected. Also, submitting incomplete sequences decreases the quality of the official IPD databases."


class MissingUTRError(Exception):
    """raised when TypeLoader encounters a sequence with at least one completely missing UTR
    """
    def __init__(self, UTR):
        """UTR should be 3 or 5 (int)
        """
        self.UTR = UTR
        if not UTR in [3,5]:
            raise ValueError("UTR must be given as integer 3 or 5!")
        self.msg = "This sequence completely misses the {}' UTR!\nTypeLoader requires at least 1 bp of each UTR to be included in genomic sequences in order to comply with IPD's requirements.".format(self.UTR)


class BothAllelesNovelError(Exception):
    """raised when TypeLoader tries to create an IPD file for an allele where both alleles of this locus are novel
    but TypeLoader can't figure out which of the pretyping alleles is 'self' and which is 'other'
    """
    def __init__(self, allele, alleles):
        self.allele = allele #TargetAllele object
        self.alleles = alleles # list of both alleles from the pretypings csv
        self.problem = "Cannot tell which novel allele from pretyping this is"
        
        
class InvalidPretypingError(Exception):
    """raised when TypeLoader tries to create an IPD file for an allele with an invalid pretyping
    """
    def __init__(self, target_allele, alleles, allele_name, locus, problem):
        self.allele = target_allele #TargetAllele object
        self.allele_name = allele_name # name of closest allele, assigned by TypeLoader
        self.locus = locus
        if not "new" in allele_name:
            if self.locus.startswith("KIR"):
                self.allele_name = allele_name + "new"
            else:
                self.allele_name = allele_name + ":new"
        self.alleles = ",".join(alleles) # list of both alleles from the pretypings csv
        self.problem = problem
