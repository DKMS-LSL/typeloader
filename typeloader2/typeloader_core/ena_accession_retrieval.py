#!/usr/bin/env python3
"""
Created on 2023-01-13.

This file contains functionality to retrieve accession numbers directly from ENA via their API.

@author: Bianca Schoene
"""

# import modules:
import logging
import requests
from typing import Tuple, List


# ===========================================================
# functions:

def _download_json_file(study_nr: str, log) -> Tuple[bool, List[dict] | str]:
    """Download json file from ENA and read it.

    Returns:
        - success (bool)
        - result:
            - list of dicts, one per allele, if success == True
            - error message if success == False
    """
    log.info(f"Downloading accession numbers for {study_nr}...")
    url = f"https://www.ebi.ac.uk/ena/portal/api/filereport?accession={study_nr}&format=json&result=sequence"

    try:
        response = requests.get(url=url)
        if response.status_code == 204:
            msg = f"Could not find any accession numbers for this project on ENA's server.\n\n" \
                  f"Please check https://www.ebi.ac.uk/ena/browser/view/{study_nr}?show=related-records \n" \
                  f"to see if any sequences are listed as Related ENA Records.\n\n" \
                  f"If not but you got a confirmation email from ENA, please contact ENA support about " \
                  f"the stage of this study ({study_nr})."
            return False, msg
        elif response.status_code != 200:
            msg = f"Could not retrieve the accession numbers for this project from ENA's server.\n({response.status_code}: {response.reason})"
            return False, msg
    except requests.exceptions.JSONDecodeError:
        msg = "No data found for this study on ENA's server!"
        return False, msg

    content = response.json()

    if not content:
        msg = f"Found this project on ENA's server, but no alleles with accessions!"
        msg += f"\nYou can check https://www.ebi.ac.uk/ena/browser/view/{study_nr} manually, if you'd like."
        return False, msg

    return True, content


def _parse_description(desc: str) -> Tuple[str, str]:
    """Get the gene and cell_line from the allele description from ENA.
    """
    gene = desc.split("Homo sapiens,")[1].split('gene')[0].strip()
    cell_line = desc.split("cell line")[1].split(",")[0].strip()

    return gene, cell_line


def _parse_json_file(content: List[dict], log) -> Tuple[dict, dict]:
    """Parse the relevant info from the json file returned by ENA.

    Returns:
         - info_dict[cell_line] = accession
         - gene_dict[cell_line] = gene
    """
    info_dict = {}
    gene_dict = {}
    log.info("Parsing content of ENA file...")
    for mydic in content:
        acc = mydic["accession"]
        desc = mydic["description"]
        gene, cell_line = _parse_description(desc)

        info_dict[cell_line] = acc
        gene_dict[cell_line] = gene
    log.info(f"\t=> found data for {len(info_dict)} alleles")

    return info_dict, gene_dict


def get_ENA_results(study: str, log) -> Tuple[dict | bool, dict | str]:
    """Retrieve the accession numbers of a project from ENA.

    Returns 2 values:
        - if successfull:
            - info_dict[cell_line] = accession
            - gene_dict[cell_line] = gene
        - if not successfull:
            - success = False
            - error message
    """
    success, content = _download_json_file(study, log)
    if success:
        info_dict, gene_dict = _parse_json_file(content, log)
        return info_dict, gene_dict
    else:
        msg = content
        return success, msg


# ===========================================================
# main:

def main(log):
    good = "PRJEB42349"
    bad = "PRJEB55283"

    result = get_ENA_results(bad, log)


if __name__ == "__main__":
    logger = logging.getLogger()
    logger.info("<Start>")
    main(logger)
    logger.info("<End>")
