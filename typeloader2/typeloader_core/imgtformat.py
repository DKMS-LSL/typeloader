#!/usr/bin/env python

header = """ID   {submission_id}; Sequence Submission; {sequence length} BP.
XX
AC   {submission_id};
XX
SV   {submission_id}.{allele_counter}
XX
DT   {submission_date} (Submitted)
DT   {release_date} (Release)
XX
DE   {local_name}
XX
KW   INTERNAL SUBMISSION;
XX
{refallele_diffs}
XX
OS   Homo sapiens (human);
OC   Eukaryota; Metazoa; Chordata; Vertebrata; Mammalia; Eutheria; Primates;
OC   Catarrhini; Hominidae; Homo.
XX
DR   GenBank; {ena_id}.
XX
RN   [1]
RC   Unpublished.
XX
FH   Key            Location/Qualifier
FH
FT   submitter      1..{sequence length}
FT                  /ID="{submittor id}"
FT                  /name="{lab contact}"
FT                  /alt_contact="{full user name}"
FT                  /email="{email}"
FT   source         1..{sequence length}
FT                  /cell_id="{cell_line}"
FT                  /ethnic_origin="Unknown"
FT                  /sex="Unknown"
FT                  /consanguineous="Unknown"
FT                  /homozygous="No"
FT                  /lab_of_origin="{lab of origin}"
FT                  /lab_contact="{lab contact}"
FT                  /material_available="{material available}"
FT                  /cell_bank="Not Available"
FT                  /software="TypeLoader V{typeloader version}"
FT                  /reference_version="{database} V{db version}"
{other_alleles}FT   method         1..{sequence length}
FT                  /primary_sequencing="{primary sequencing tech}"
FT                  /secondary_sequencing="{secondary sequencing tech}"
FT                  /type_of_primer="{type of primer}"
FT                  /sequenced_in_isolation="{sequenced in isolation}"
FT                  /no_of_reactions="{no of reactions}"
FT                  /sequencing_direction="{sequencing directions}"
FT                  /Confirmation_Methods="{confirmation methods}"
FT                  /alignment="{related allele}"
"""

refAlleleDiffString = """CC   {text}"""

otherAllelesString = "FT                  /{gene}*=\"{alleleNames}\"\n"

fiveUtrString = """FT   5'UTR          1..{fiveUtrEnd}"""
threeUtrString = """FT   3'UTR          {threeUtrStart}..{threeUtrEnd}"""

footer= """SQ   Sequence {sequence length} BP; {countA} A; {countC} C; {countG} G; {countT} T; {countOther} other;
{sequence}
//
"""
