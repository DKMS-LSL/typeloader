import xmltodict
from sys import argv

def change_utf_decl(xmlFileName):
    
    # xmltodict does not seem to like utf-16, changing this to utf-8
    
    lookFor = "utf-16"
    changeTo = "utf-8"
    
    xmlHandle = open(xmlFileName)
    xmlText = xmlHandle.read()
    xmlHandle.close()
    
    xmlHandle = open(xmlFileName,"w")
    xmlHandle.write(xmlText.replace(lookFor,changeTo))
    xmlHandle.close()
    
    return

def parseXML(xmlFileName):

    change_utf_decl(xmlFileName) #utf-16 to utf-8 change

    xmlHandle = open(xmlFileName)
    xmlText = xmlHandle.read()
    xmlHandle.close()

    return xmltodict.parse(xmlText)

def getAlleleNames(parsedXML):

    # look in xml for matches with minExonMismatches > 0

    found_alleles_flag = False

    while not found_alleles_flag:
        try:
            alleles = parsedXML["sample"]["matchsets"]["matchset"]["matchcombination"]["matchId"]
            found_alleles_flag = True
            break
        except: pass

        try:
            alleles = parsedXML["Sample"]["Matchsets"]["Matchset"]["Matchcombination"]["MatchId"]
            found_alleles_flag = True
            break
        except: pass

        try:
            alleles = parsedXML["ProjectXml"]["Samples"]["Sample"]["Loci"]["Locus"]["Matching"]["Matchset"]["MatchCombination"]["MatchID"]
            found_alleles_flag = True
            break
        except: pass

        try:
            alleles = parsedXML["Locus"]["Matching"]["Matchset"]["MatchCombination"]["MatchID"]
            found_alleles_flag = True
            break
        except: pass


    allele_names = []
    for allele in alleles:

	# the exceptions are for working with old XML versions from GenDX
        try:
            mm_count = int(allele["@PriorityMM"]) + int(allele["@NonPriorityMM"]) + int(allele["@ExonMM"]) + int(allele["@IntronMM"])
            if mm_count:
                alleleName_suffix = "-Novel"
            else:
                alleleName_suffix = "-Existing"
        except:
            alleleName_suffix = ""

        try: phasing_suffix = "-%s" % allele["@Phasing"]
        except:
            phasing_suffix = ""

        try:
            alleleName = allele["@refAllele"] + alleleName_suffix + phasing_suffix
        except:
            try: alleleName = allele["@RefAllele"] + alleleName_suffix + phasing_suffix
            except:
                try: alleleName = allele["#text"] + alleleName_suffix + phasing_suffix
                except: alleleName = ""

        allele_names.append(alleleName)

    return allele_names


def get_additional_XML_info(parsedXML, log):
    """trys to retrieve additional infos from XML file;
    returns default values for older XML files which don't contain this info
    """
    data_dic = {"new_timestamp" : "",
                "new_software" : "NGSengine",
                "new_version" : "",
                "lr_phasing" : "",
                "lr_data" : "yes"}
    try:
        timestamp = parsedXML["ProjectXml"]["User"]["@DateTime"]
        data_dic["new_timestamp"] = timestamp.split("T")[0]
    except:
        log.info("Could not find timestamp in XML file!")
    
    try:
        data_dic["new_software"] = parsedXML["ProjectXml"]["AnalysisSoftware"]["Software"]
        data_dic["new_version"] = parsedXML["ProjectXml"]["AnalysisSoftware"]["Version"]
    except:
        log.info("Could not find software info in XML file! Assuming NGSengine...")

    try:
        phasing = parsedXML["ProjectXml"]["Samples"]["Sample"]["Loci"]["Locus"]["PhasingRegions"]
        if phasing == "1":
            data_dic["lr_phasing"] = "yes"
        else:
            data_dic["lr_phasing"] = "no"
    except:
        log.info("Could not find phasing info in XML file!")
    
    return data_dic
    

def getHaplotypeIds(parsedXML, alleleName):

    try: matches = parsedXML["sample"]["matches"]["match"]
    except: pass

    try: matches = parsedXML["Sample"]["Matches"]["Match"]
    except: pass

    try: matches = parsedXML["ProjectXml"]["Samples"]["Sample"]["Loci"]["Locus"]["Matching"]["Matches"]["Match"]
    except: pass

    try: matches = parsedXML["Locus"]["Matching"]["Matches"]["Match"]
    except: pass

    for match in matches:

        try: currAlleleName = match["@id"]
        except: currAlleleName = match["@ID"]

        phasing = match["@phasing"]

        try: scrubbedAlleleName, newOrNot, phasingStatus = alleleName.split("-")
        except:
            scrubbedAlleleName = alleleName # old XML versions from GenDX
            phasingStatus = phasing # dirty hack to be able to work with old XML versions

        if (currAlleleName == scrubbedAlleleName) and (phasing == phasingStatus):
            try: return [haplotype for haplotype in match["haplotypecombination"]["haplotypeId"]]
            except: pass

            try: return [haplotype for haplotype in match["Haplotypecombination"]["HaplotypeId"]]
            except: pass

            try: return [haplotype for haplotype in match["HaplotypeCombination"]["HaplotypeID"]]
            except: return

def sequenceFromHaplotype(parsedXML, haplotypeList):

    try: haplotypes = parsedXML["sample"]["haplotypes"]["haplotype"]
    except: pass

    try: haplotypes = parsedXML["Sample"]["Haplotypes"]["Haplotype"]
    except: pass

    try: haplotypes = parsedXML["Locus"]["Haplotypes"]["Haplotype"]
    except: pass

    try: haplotypes = parsedXML["ProjectXml"]["Samples"]["Sample"]["Loci"]["Locus"]["Haplotypes"]["Haplotype"]
    except: pass

    haplotypeSeqs = []

    for haplotype in haplotypes:

        try: haplotype_id = haplotype["@id"]
        except: haplotype_id = haplotype["@ID"]

        if haplotype_id in haplotypeList:
            begin = int(haplotype["@begin"].split(":")[0]) # splitting on the : accounting for phase?descriptor in the XML
            end = int(haplotype["@end"].split(":")[0])
            sequence = haplotype["#text"].replace("-","")
            haplotypeSeqs.append((begin,end,sequence))

    haplotypeSeqs.sort()

    return "".join([usedHaplotype[-1] for usedHaplotype in haplotypeSeqs])

def get_allele_sequences(xmlFile):

    xmlData = parseXML(xmlFile)

    alleles = {}

    alleleNames = getAlleleNames(xmlData)
    for alleleName in alleleNames:

        alleles[alleleName] = sequenceFromHaplotype(xmlData, getHaplotypeIds(xmlData, alleleName))

    return alleles



if __name__ == '__main__':

    xmlData = parseXML(argv[1])

    alleleNames = getAlleleNames(xmlData)
    print(alleleNames)

    for alleleName in alleleNames:

        haplotypes = getHaplotypeIds(xmlData, alleleName)
        print(haplotypes)

        sequence = sequenceFromHaplotype(xmlData, haplotypes)
        print(sequence)
