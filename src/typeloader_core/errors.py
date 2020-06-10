#!/usr/bin/env python
'''
Created on 26.11.2018

contains custom exception classes

@author: schoene
'''

class IncompleteSequenceWarning(Exception):
    """raised when TypeLoader encounters a sequence with an incomplete 5'UTR and/or 3'UTR
    """
    def __init__(self, missing_bp_front, missing_bp_end):
        self.missing_bp_front = missing_bp_front
        self.missing_bp_end = missing_bp_end

        missing = []
        if self.missing_bp_front:
            missing.append("the first {} bp (5' end)".format(self.missing_bp_front))
        if self.missing_bp_end:
            missing.append("the last {} bp (3' end)".format(self.missing_bp_end))
        self.missing = " and ".join(missing)

        self.msg = "This sequence misses {}!\nDo you want to upload it anyway?\n".format(self.missing)
        self.msg += "(Note that IPD requires at least 1 bp per UTR to be contained in genomic sequences.)\n\n"
        self.msg += "Please consider carefully: this might lead to an incorrect closest allele being selected. "
        self.msg += "Also, submitting incomplete sequences decreases the quality of the official IPD databases."


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
        if allele_name:
            if not "new" in allele_name:
                if self.locus.startswith("KIR"):
                    self.allele_name = allele_name + "new"
                else:
                    self.allele_name = allele_name + ":new"
        self.alleles = ",".join(alleles) # list of both alleles from the pretypings csv
        self.problem = problem


class DevianceError(Exception):
    """raised when TypeLoader encounters a sequence that is too different from all known full-length
    alleles, which makes BLAST produce nonsense alignments (#138)
    """
    def __init__(self, unaligned_bp_front, reference_allele):
        self.unaligned_bp_front = unaligned_bp_front

        self.msg = f"{self.unaligned_bp_front} unaligned bases at alignment start "
        self.msg += f"when aligned to closest found allele {reference_allele}:\n\n"
        self.msg += "This sequence is probably too dissimilar to all known full-length alleles.\n\n"
        self.msg += "TypeLoader currently can't handle this allele, sorry!"


class FileFormatError(Exception):
    """raised when TypeLoader encounters a sequence input file that it cannot parse
    """
    def __init__(self, msg):
        self.msg = f"Sorry, TypeLoader cannot handle this input file!\n\n{msg}"
