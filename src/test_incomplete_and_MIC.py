'''
Created on 19.03.2019

@author: schoene
'''
from typeloader_core import coordinates, imgt_text_generator

def check_diff_line(diff_line, sample_id_int):
    std = "HLA-A*01:new differs from HLA-A*01:01:01:01 like so : Mismatches = pos 503 (G -> C);pos 2981 (G -> C);pos 1046 in codon 325 (AGC -> ACC);pos 1093 in codon 341 (GTG -> CTG);pos 3030 (G -> C);."
    std_ins1 = "HLA-A*01:new differs from HLA-A*01:01:01:01 like so : Mismatches = pos 503 (G -> C);pos 2981 (G -> C);pos 1046 in codon 325 (AGC -> AAC);pos 1093 in codon 341 (GTG -> ACT);pos 3030 (G -> C);."
    std_del1 = "HLA-A*01:new differs from HLA-A*01:01:01:01 like so : Mismatches = pos 503 (G -> C);pos 2981 (G -> C);pos 1046 in codon 325 (AGC -> CCA);pos 1093 in codon 341 (GTG -> TGT);pos 3030 (G -> C);."
    
    mic6 = "MICA*001:new differs from MICA*001 like so : Mismatches = pos 7796 (G -> C);pos 8069 (G -> C);pos 326 in codon 86 (GGC -> GCC);pos 613 in codon 182 (GTG -> CTG);."
    mic7 = mic6 + " Deletions = pos 7911 (G),pos 8974 (C). Insertions = pos 7520 (G)."
    
    test_dic = {"DKMS-LSL_HLA-A1" : std,
                "DKMS-LSL_HLA-A2" : std + " Deletions = pos 2792 (A).",
                "DKMS-LSL_HLA-A3" : std + " Deletions = pos 2790 (A). Insertions = pos 2769 (A).",
                "DKMS-LSL_HLA-A4" : std_del1 + " Deletions = pos 2825 (A).",
                "DKMS-LSL_HLA-A5" : std_ins1 + " Insertions = pos 2822 (C).",
                "DKMS-LSL_HLA-A6" : std,
                "DKMS-LSL_HLA-A7" : std_del1 + " Deletions = pos 2825 (A).",
                "DKMS-LSL_HLA-A8" : std_ins1 + " Insertions = pos 2822 (C).",
                "DKMS-LSL_HLA-A9" : std_ins1 + " Insertions = pos 2822 (C).",
                
                "DKMS-LSL_MICA-1" : "MICA*001:new differs from MICA*001 like so : Mismatches = pos 326 in codon 86 (GGC -> GCC);.",
                "DKMS-LSL_MICA-2" : "MICA*001:new differs from MICA*001 like so : Mismatches = pos 8069 (G -> C);.",
                "DKMS-LSL_MICA-3" : "MICA*001:new differs from MICA*001 like so : Mismatches = pos 1024 in codon 319 (GAG -> AGC);. Deletions = pos 9348 (A).",
                "DKMS-LSL_MICA-4" : "MICA*001:new differs from MICA*001 like so : Mismatches = pos 1024 in codon 319 (GAG -> CAG);.",
                "DKMS-LSL_MICA-5" : "MICA*001:new differs from MICA*001 like so : Mismatches = pos 660 (G -> C);pos 7840 (G -> C);.",
                "DKMS-LSL_MICA-6" : mic6,
                "DKMS-LSL_MICA-7" : mic7,
                "DKMS-LSL_MICA-8b" : mic7,
                "DKMS-LSL_MICA-8e" : mic7
                }
    
    if sample_id_int in test_dic:
        if diff_line.strip() == test_dic[sample_id_int].strip():
            print("\t=> diff-string ok")
        else:
            print("\t=> DIFFERENCE: (exp. vs. found)")
            expected = test_dic[sample_id_int].strip().split()
            found = diff_line.strip().split()
            for i, chunk in enumerate(expected):
                if chunk != found[i]:
                    print ((expected[i], found[i]))
    else:
        print("No expectation-string to compare to")
                

def check_file(blast_xml_file, allelesFilename, targetFamily, settings, log):
    log.info("Calculating coordinates...")
    annotations = coordinates.getCoordinates(blast_xml_file, allelesFilename, targetFamily, settings, log, incomplete_ok = True)
    gendxAllele = list(annotations.keys())[0]
    diff_line = imgt_text_generator.make_diff_line(annotations[gendxAllele]["differences"],
                               annotations[gendxAllele]["imgtDifferences"], 
                               annotations[gendxAllele]["closestAllele"])
    length = 125
    for i in range(0, len(diff_line), length):
        print(diff_line[0+i:length+i])
    check_diff_line(diff_line, sample_id_int)
    
    print()


if __name__ == "__main__":
    from general import start_log
    from GUI_login import get_settings
    log = start_log(level="debug")
    log.info("<Start>")
    settings = get_settings("admin", log)
    
    #check HLA:
    for nr in range(1,10):
        sample_id_int = "DKMS-LSL_HLA-A{}".format(nr)
        print(">", sample_id_int)
     
        blast_xml_file = r"\\nasdd12\daten\data\Typeloader\admin\projects\20190321_ADMIN_MIC_1\HLA-A-{}\DKMS-LSL_HLA-A-{}_A_1.blast.xml".format(nr, nr)
        allelesFilename = r"\\nasdd12\daten\data\Typeloader\_general\reference_data\hla.dat"
        targetFamily = "HLA"
        check_file(blast_xml_file, allelesFilename, targetFamily, settings, log)
    
    #check MIC:
    for nr in [1,2,3,4,5,6,7,"8b","8e"]:
        sample_id_int = "DKMS-LSL_MICA-{}".format(nr)
        print(">", sample_id_int)
        blast_xml_file = r"\\nasdd12\daten\data\Typeloader\admin\projects\20190321_ADMIN_MIC_1\MICA-{}\DKMS-LSL_MICA-{}_MICA_1.blast.xml".format(nr, nr)
        allelesFilename = r"\\nasdd12\daten\data\Typeloader\_general\reference_data\hla.dat"
        targetFamily = "HLA"
        check_file(blast_xml_file, allelesFilename, targetFamily, settings, log)
       
        
    log.critical("<End> :-)")

