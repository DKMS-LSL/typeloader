header = """ID   XXX; XXX; linear; XXX; XXX; XXX; XXX.
XX
AC   XXX;
XX
DE   {species}, {partial} {gene} gene for {product}, cell line {cell line}, allele {allele}
XX
FH   Key             Location/Qualifiers
FH
FT   source          1..{sequence length}
FT                   /organism="{species}"
FT                   /mol_type="genomic DNA"
FT                   /cell_line="{cell line}"
FT   CDS             join({exon_coord_list})
FT                   /codon_start={reading frame}
FT                   /gene="{gene}"
FT                   /allele="{allele}"
FT                   /product="{product}"
FT                   /function="antigen presenting molecule"
"""

exonString = """FT   exon            {start}..{stop}
FT                   /number={exon_num}
FT                   /gene="{gene}"
FT                   /allele="{allele}"
"""

intronString = """FT   intron          {start}..{stop}
FT                   /number={intron_num}
FT                   /gene="{gene}"
FT                   /allele="{allele}"
"""

footer = """XX
SQ
{sequence}
//

"""

