# ![Icon](images/TypeLoader_32.png) The pretypings file

For every submitted allele, IPD requires, among other data, genotyping results for several loci to characterize the sample the novel allele originated from ("Source Sample Typing Profile"). To pass this information to TypeLoader, you put add it as a .csv file during [=> IPD submission](submission_ipd.md).

You can fill this file either manually or automatically, if your LIMS etc. provide this.

## Required loci
The following loci are the minimum acceptable pretyping profile for IPD submissions:
 
 * HLA-A
 * HLA-B
 * HLA-DQB1
 * the gene you are submitting

However, **IPD strongly encourages adding as much genotyping data about the sample as you have.**

## The file
The pretypings file must be a .csv file (comma separated text file). You can generate these from Excel or any text editor. **The delimiter used must be comma or semicolon.**

The file should contain **one row per sample you want to submit alleles from**.

### Columns:
  * **Internal donor ID**: **this column is used identify the sample!** 
  * **Cell line**: optional (can also be left blank but **NOT** deleted!)
  * **Customer**: optional (can be left blank but **NOT** deleted!); the customer who sent this sample; this information is saved in TypeLoader

**This is followed by several columns per locus:**

* **HLA loci:** 2 columns per locus (one per allele), "A1", "A2" etc. (genotyping results should be at maximal resolution and contain no locus)
* **KIR loci:** 4 columns per locus (one per possible allele), "KIR2DL1-1", "KIR2DL1-2" etc. (genotyping results should be shortened to 3 field resolution or be given as POS/NEG for absence/presence. Cells that are not needed should be left blank).

Example file:

![IPDSubmission2b](images/ipd_submission2a.png)

![Important](images/icon_important.png) **You can download an example file with the right format and headers from TypeLoader's menu: ``Options`` => ``Download example files`` => ``Pretypings File``. You can use this as a template to fill in your data, either manually or from your LIMS etc.**

### Formatting and resolution

* Use one field per allele. To accomodate for possible copy numbers, HLA-loci have 2 columns and KIR loci have 4. Leave fields, for which you have no genotyping results or which are not needed (not present KIR copies) blank.
* All genotyping results should be given at the highest resolution you can provide. 
* For KIR genes, POS (presence) and NEG (absence) are valid typing results **except for the target locus**, where allele level resolution is mandatory. 
* **Mark all novel alleles as new like this:**
 * HLA: 003:new
 * KIR: 003new 

### Requirement checks
TypeLoader checks the given pretypings for the following requirements, and shows a popup asking you to clarify if necessary:

#### Invalid pretypings
If any of the following things happen, TypeLoader will recognize the pretyping as invalid:

* POS is contained in the pretyping of the target locus.
* None of the alleles of the target locus are marked as new even though this is not a confirmatory sequence (= identical to an already known full-length sequence).
* The closest known allele is not contained in the pretypings of the target locus. (This is quite common if your pretypings were not created with the most recent database version.)
* Pretypings for any of the required loci are missing.

If any of these are encountered, TypeLoader will show a popup dialog listing all affected samples from this submission, with the encountered problem:

![pic](images/invalid_pretypings_dialog.png)

If this happens, you have to adjust the pretypings file accordingly. Then you can try again.

#### Multiple novel alleles in the target locus

If any of the target alleles in your submission are from samples with more than one novel allele in the target locus, TypeLoader will try to figure out which of these pretypings belongs to which target allele by comparing the content of "Target allele" and "Partner allele" in the [=> SampleView](view_sample.md) (lower half, tab "New Genotyping") to the provided pretypings (these values are extracted from the original Fasta or XML file during [=> New sequence file upload](new_allele.md)).

If these do not match, TypeLoader will show you a popup dialog asking you for each unclear target allele, which of the provided pretypings belongs to this target allele:

![pic](images/multiple_novel_alleles_dialog.png)

After you click ``Save choices``, TypeLoader will save the results of your choice in the aforementioned fields and re-attempt creating the IPD files, which should work now. 

(TypeLoader needs this information in order to properly format the IPD file in accordance with IPD's wishes.)