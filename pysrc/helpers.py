
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

