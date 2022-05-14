import json
import sys

phylum = "Bacteroidetes"

input_json = sys.argv[1]

for line in open(input_json):
    data = json.loads(line)
    #print (data)

    if "phylum" in data["taxonomy"] and data["taxonomy"]["phylum"][0] == phylum:
        print(json.dumps(data))