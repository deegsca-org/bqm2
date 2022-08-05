if __name__ == "__main__":
    import json
    import sys  
    data = json.loads(sys.stdin.read())
    
    for pid,v in data["mappings"].items():
        obj = {}
        obj['pid'] = pid

        if 'custom_segment' not in v and 'segment' not in v: continue

        try:
            obj['custom_segment'] = v['custom_segment']
        except KeyError:
            pass
        try:
            obj['segment'] = v['segment']
        except KeyError:
            pass
        print(json.dumps(obj))
