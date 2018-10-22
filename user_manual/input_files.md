# ![Icon](images/TypeLoader_32.png) Input files
TypeLoader accepts sequences for [=> New Alleles](new_allele.md) in either of two formats:

 * Fasta format
 * XML format produced by NGSEngine (GenDX) 

## Fasta files
Fasta files should contain exactly one sequence. (If they contain more than that, only the first sequence is used. To add multiple fasta sequences at once, use the [=> Bulk Fasta Upload](new_allele_bulk.md).)

**Optionally**, You can use the sequence header to pass data along to TypeLoader, which it will then store for your allele. This should be a list of key-value pairs separated by ";". The following keys are  currently recognized:

 * **locus**
 * **ref**, **second**, **third**, **fourth** (all of these allele names are concatenated with 'or' and stored as "partner_allele")
 * **LIMS\_DONOR\_ID** or **SAMPLE\_ID\_INT** (internal sample ID)
 * **Spendernummer** or **SAMPLE\_ID\_EXT** (external sample ID)
 * **notes** (comment)
 * **short\_read_data**
 * **short\_read_type**
 * **long\_read_data**
 * **long\_read_type**
 * **software** (software used for full-length genotyping)
 * **version** (version of the software used for full-length genotyping)
 * **date** (date of secondary genotyping)

## XML files
The XML file exported from NSGEngine contains both alleles of one locus of one sample. If you upload such a file to TypeLoader, the dialog will ask you to clarify which of the alleles you want to add. (If you want to add both alleles, run the [=> New Allele Dialog](new_allele.md) twice with the same file, and choose the other allele during the second run.)