if __name__ == "__main__":
    import json
    import sys  
    data = json.loads(sys.stdin.read())
    
    for row in data:
        obj = {}
        if len(row) == 0: continue
        if len(row) > 1: raise Exception()
        key = [x for x in row.keys()][0]
        for subrow in row[key][0]:
            print(json.dumps({ 'sid': key, 'compound_sid': subrow, 'campaigns': row[key][0][subrow]}))
