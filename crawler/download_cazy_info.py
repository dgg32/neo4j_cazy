# -*- coding: utf-8 -*-
import requests
import re
from threading import Thread
import queue
from threading import Semaphore
from lxml import etree
import json
import ssl

prefix = "http://www.cazy.org/"
fivefamilies = ["Glycoside-Hydrolases.html","GlycosylTransferases.html","Polysaccharide-Lyases.html","Carbohydrate-Esterases.html","Carbohydrate-Binding-Modules.html", "Auxiliary-Activities.html"]
#fivefamilies = ["Auxiliary-Activities.html"]
in_queue = queue.Queue()
writeLock = Semaphore(value = 1)

rx_cazypedia = re.compile(r'(http://www\.cazypedia\.org/index\.php/\w+)')
rx_prosite = re.compile(r'(http://prosite\.expasy\.org/\w+)')
re_taxon = re.compile(r'html">(\w+)</a> &#40;(\d+)&#41;</span>')

family_ec = {}

ctx = ssl.SSLContext(ssl.PROTOCOL_SSLv23)

def clean(text):
    text = re.sub('<[^<]+?>', '', text)
    text = text.replace("&#946;","beta")
    text = text.replace("\xce\xb2","beta")
    text = text.replace("&#945;","alpha")
    text = text.replace("&#954;","kappa")
    text = text.replace("\xce\xb1","alpha")
    text = text.replace("\xe2\x80\x98", "'")
    text = text.replace("\xe2\x80\x99", "'")
    text = text.replace("&#197;", "angstrom")
    text = text.replace("&#8594;", "->")
    text = text.replace("&#8805;;", ">=")
    text = text.replace("“", "\"")
    text = text.replace("”", "\"")
    text = text.replace("–", "-")
    text = text.replace("ß", "beta")
    return text.strip()


def work():
    while True:
        
        url = in_queue.get()
        #try:
        container = {}
        page = re.sub(r"\s+", " ", requests.get(url, verify=False).content.decode('iso8859-1').replace(r"\n", " "))
        #print (url)
        tree = etree.HTML(page)
        family_name =  re.findall(r"http://www\.cazy\.org/(\w+)\.html", url)[0]
        container["name"] = family_name
        
        if family_name in family_ec.keys():
            container["ec"] =list(family_ec[family_name])
        
        trs = tree.xpath("//tr")
        title = ""
        #print (trs)
        for tr in trs:
            headers = etree.HTML(etree.tostring(tr)).xpath("//th")
            
            for header in headers:

                inhalt = re.findall(r'>(.+?)</',etree.tostring(header).decode('iso8859-1'))
                #print (inhalt)
                if len(inhalt) > 0:
                    title = inhalt[0]
                #print etree.tostring(header)
            contents = etree.HTML(etree.tostring(tr).decode('iso8859-1')).xpath("//td")
            
            for content in contents:
                inhalts = re.findall(r'>(.+)</',etree.tostring(content).decode('iso8859-1'))
                if len(inhalts) > 0:
                    inhalt = clean(inhalts[0])
#                        inhalt = inhalt.replace("&#945;","alpha")
                    container[title] = inhalt
                #print etree.tostring(content)
        #print (container)
        #print "hello"
        container["distribution"] = {}
        for i in re_taxon.findall(page):
            taxon, number = i[0], int(i[1])
            container["distribution"][taxon] = int(number)
        
        cazypedia = re.findall(rx_cazypedia, page)
        if len(cazypedia) > 0:
            
            ####there is a bug in cazy webpage about GH117 cazypedia link address
            
            cazypedia_url = cazypedia[0]
            
            cazypedia_url = re.sub(r"_Family_GH(\d+)",r"_Family_\1",cazypedia_url)
            
            cazypedia_content = requests.get(cazypedia_url, verify=False).content.decode('iso8859-1').replace("\n"," ")
            search_substrate = re.search(r'<h2> <span class="mw-headline" id="Substrate_specificities">\s+Substrate specificities.+?<p>(.+?)</p> <h2>',cazypedia_content)
            #print cazypedia_content
            if search_substrate:
                inhalt = clean(search_substrate.group(1))
                container["substrate_specificity"] = inhalt
                #print container["substrate_specificity"]
            search_residue = re.search(r'<h2> <span class="mw-headline" id="Catalytic_Residues">\s+Catalytic Residues.+?<p>(.+?)</p> <h2>',cazypedia_content)
            #print cazypedia_content
            if search_residue:
                #print "OK"
                
                inhalt = clean(search_residue.group(1))

                container["catalytic_residues"] = inhalt
#                    print container["catalytic_residues"]
            #if len(inhalt) > 0:
            #    print inhalt[0]
                
        prosite = re.findall(rx_prosite, page)
        if len(prosite) > 0:
            prosite_content = requests.get(prosite[0], verify=False).content.decode('iso8859-1').replace("\n"," ")
            #print prosite_content
            search_pattern = re.search(r'<td><strong  style="letter-spacing\:3px">(\S+)</strong>', prosite_content)
            if search_pattern:
                container["prosite_pattern"] = search_pattern.group(1)
                regex_pattern = search_pattern.group(1).replace("-","").replace("x",r"\w")
                regex_pattern = re.sub(r"\((\d+)\)",r"{\1}",regex_pattern)
                regex_pattern = re.sub(r'\((\d+),(\d+)\)',r'{\1,\2}',regex_pattern)
                regex_pattern = re.sub(r'\((\d+)\)',r'{\1}',regex_pattern)
                #print container["family"]
                #print regex_pattern
                container["regex_pattern"] = regex_pattern
        writeLock.acquire()
        container["column"] = "cazy"
        print (json.dumps(container))
        writeLock.release()
        #except:
            #print "error " + url
        #   pass
        #finally:
        in_queue.task_done()

        
for i in range(7):
    t = Thread(target=work)
    t.daemon = True
    t.start()


rx_ec = re.compile(r'<a href="http://www.enzyme-database.org/query.php\?ec=(\S+?)">\S+</a></th><td class="ec">\s+(.+?)</table>')
rx_ec_family = re.compile(r'<a href=(\w+)\.html id="separ">\w+</a>')
for family in fivefamilies:
    address = prefix + family
    
    page = requests.get(address, verify=False).content.decode('iso8859-1')
    
    for ec in rx_ec.findall(page):
        for fa in rx_ec_family.findall(ec[1]):
            if fa not in family_ec:
                family_ec[fa] = set()
            family_ec[fa].add(ec[0])
    
    
    families = re.findall(r'<option value="(http://www\.cazy\.org/\w+?\.html)">\w+</option>', page)
    
    ###go into each family
    for family in families:
        in_queue.put(family)

#print family_ec
in_queue.join()