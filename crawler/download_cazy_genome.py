import sys, re
import requests
from threading import Thread
import queue
import pyphy
import json

from threading import Semaphore
writeLock = Semaphore(value=1)

rx = re.compile(r'<td class="classe" id="navigationtab2"><a href="http://www\.cazy\.org/(\w+)\.html" class="nav2"><div class="famille">\w+</div></a><div class="nombre_de">(\d+)</div></td>')


roots = {
    "bacteria": "http://www.cazy.org/b",
    "eukaryote": "http://www.cazy.org/e",
    "archaea": "http://www.cazy.org/a",
    "virus": "http://www.cazy.org/v"
}

#scheme
#organism, tax_id, superkingdom, phylum, class, order, family, genus, species, orf, cazy
desired_ranks = ["superkingdom", "phylum", "class", "order", "family", "genus", "species"]

in_queue = queue.Queue()


def work():
    while True:
        url = in_queue.get()

        
        
        content = requests.get(url).content.decode('iso8859-1')
        
        container = {}
        container["cazy"] = {}
        container["taxonomy"] = {}
        
        try:
            container["name"] = re.findall(r'id="font_org">(.+)</font>', content)[0]
            
                    #container["organism"] = re.findall(r'id="font_org">(.+)</font>', content)[0]
            cazy_page_taxon_name = re.findall(r'<font class="titre_cazome" id="font_org">(.+)<\/font>', content)[0]
            #print (cazy_page_taxon_name)
            taxonomy_id = -1
            if cazy_page_taxon_name:
                taxonomy_id = int(pyphy.getTaxidByName(cazy_page_taxon_name.strip())[0])

            if taxonomy_id == -1:
                taxonomy_id = re.findall(r'http://www\.ncbi\.nlm\.nih\.gov/Taxonomy/Browser/wwwtax\.cgi\?id=(\d+)', content)[0]
            
            container["taxid"] = int(taxonomy_id)
        #lineage = re.findall(r'<b>Lineage</b>\:(.+)<br><br />', content)[0].strip()
        
            current_id = int(taxonomy_id)
            while current_id != 1 and current_id != -1:
                current_id = int(pyphy.getParentByTaxid(current_id))
                if pyphy.getRankByTaxid(current_id) in desired_ranks:
                    container["taxonomy"][pyphy.getRankByTaxid(current_id)] = [pyphy.getNameByTaxid(current_id), current_id]
        
            #container["total_gi"] = len(pyphy.getGiByTaxid(taxonomy_id))
            cazies = re.findall(rx,content)
        #print cazy
            for cazy in cazies:
                container["cazy"][cazy[0]] = int(cazy[1])
            
            if len(container["cazy"]) != 0:
                writeLock.acquire()
                container["column"] = "genome"
                print (json.dumps(container))
                writeLock.release()
            
        except Exception:
            pass

        
        in_queue.task_done()

for i in range(7):
    t = Thread(target=work)
    t.daemon = True
    t.start()
    
for root in roots.keys():
    root_initials = [x for x in re.findall(roots[root] + "\\w.html", requests.get(roots[root] + ".html").content.decode('iso8859-1'))]
    for root_initial in root_initials:
        genomes = [y for y in re.findall(roots[root] + "\\d+.html", requests.get(root_initial).content.decode('iso8859-1'))]
        for genome in genomes:
            in_queue.put(genome)
            
in_queue.join()