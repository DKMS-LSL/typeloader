header = """ID   {submission_id}; Sequence Submission; {sequence length} BP.
XX
AC   {submission_id};
XX
SV   {submission_id}.{allele_counter}
XX
DT   {submission_date} (Submitted)
DT   {release_date} (Release)
XX
DE   {cell line}
XX
KW   INTERNAL SUBMISSION;
XX
{refallele_diffs}
XX
OS   Homo sapiens (human);
OC   Eukaryota; Metazoa; Chordata; Vertebrata; Mammalia; Eutheria; Primates;
OC   Catarrhini; Hominidae; Homo.
XX
DR   GenBank; {ena id}.
XX
RN   [1]
RC   Unpublished.
XX
FH   Key            Location/Qualifier
FH
FT   submittor      1..{sequence length}
FT                  /ID="10973T44"
FT                  /name="Ms. Viviane Albrecht"
FT                  /alt_contact=""
FT                  /email="albrecht@dkms-lab.de<mailto:albrecht@dkms-lab.de>,boehme@dkms-lab.de<mailto:boehme@dkms-lab.de>"
FT   source         1..{sequence length}
FT                  /cell_id="{cell line}"
FT                  /ethnic_origin="Unknown"
FT                  /sex="Unknown"
FT                  /consanguineous="Unknown"
FT                  /homozygous="No"
FT                  /lab_of_origin="DKMS Life Science Lab GmbH"
FT                  /lab_contact="Viviane Albrecht"
FT                  /material_available="Whole Blood Sample"
FT                  /cell_bank="Not Available"
{other_alleles}
FT   method         1..{sequence length}
FT                  /primary_sequencing="NGS - Illumina Sequencing Technology"
FT                  /secondary_sequencing="Direct sequencing of PCR product from DNA(SBT)"
FT                  /type_of_primer="Both allele and locus specific"
FT                  /sequenced_in_isolation="Yes"
FT                  /no_of_reactions="1"
FT                  /sequencing_direction="Both"
FT                  /Confirmation_Methods="SBT"
FT                  /alignment="{related allele}"
FT   CDS            join({exon_coord_list})
"""

refalleleDiffString = """CC   {text}"""

otherAllelesString = """FT   /{gene}*:{alleleNames}"""


exonString = """FT   exon            {{start}..{stop}}
FT                   /number={exon_num}
"""

intronString = """FT   intron          {{start}..{stop}}
FT                   /number={intron_num}
"""

footer= """SQ   Sequence {sequence length} BP; {countA} A; {countC} C; {countG} G; {countT} T; {countOther} other;
    {sequence}
//
"""
