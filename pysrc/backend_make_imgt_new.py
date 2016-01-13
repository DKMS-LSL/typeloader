from backend_imgtformat import *
import textwrap

def make_globaldata(submission_id="",allele_counter=1,sequence="",cell_line="",ena_id="",related_allele="", \
                    other_alleles={},features=[],coords=[],differences={}):


    todaystr = datetime.now().strftime('%d/%m/%Y')
    
    return {"submission_id":submission_id,"allele_counter":allele_counter,"sequence":sequence,"cell_line":cell_line,"ena_id":ena_id, \
            "closest_allele":related_allele,"others":other_alleles,"differences":differences, \
            "submission_date":todaystr, "release_date":todaystr}






