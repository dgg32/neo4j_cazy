import requests
import json

def esearch(db, term):
    url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db={db}&term={term}&sort=relevance&format=json"

    content = json.loads(requests.get(url).content.decode('iso8859-1'))

    
    return content["esearchresult"]["idlist"]

def efecth(db, id):
    url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db={db}&id={id}"

    content = requests.get(url).content.decode('iso8859-1').split("\n")

    for line in content:
        if len(line) != 0 and line.startswith("1:"):
            content = line.replace("1:", "").strip()

            return content

def name_disambiguation(name):
    idList = esearch("mesh", name)
    if len(idList) > 0:
        best_name = efecth("mesh", idList[0])
        return best_name

if __name__ == "__main__":
    print(name_disambiguation("vitamin c"))