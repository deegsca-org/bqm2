import string
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


class DateFormatHelper:
    def __init__(self, formats: list, formats_suffixes: list):
        """
        :param formats: datetime formats
        :param formats_suffixes: template key suffixes or endings
        """
        self.formats = formats
        self.format_suffixes = formats_suffixes

        assert len(formats)
        assert len(formats) == len(formats_suffixes)

    def format_date_key(self, k: str, v: str, m: dict):
        if k.endswith(f"_{self.format_suffixes[0]}") or k == self.format_suffixes[0]:
            for i in range(1, len(self.format_suffixes)):
                newkey = k.replace(self.format_suffixes[0], self.format_suffixes[i])
                if newkey in m:
                    continue
                newval = datetime.strptime(v, self.formats[0]).strftime(self.formats[i])
                m[newkey] = newval

    def show_new_keys(self, keys: list):
        m = set()
        for k in keys:
            if k.endswith(f"_{self.suffix}" or k == self.format_suffixes[0]):
                for i in range(1, len(self.suffixes)):
                    m.add(k.replace(self.suffix, self.format_suffixes[i]))
        return m


class DateFormatHelpers:
    def __init__(self, formatters):
        self.formatters = formatters
        assert len(formatters)

    def show_new_keys(self, keys: list):
        ret = set()
        for f in self.formatters:
            ret += f.show_new_keys(keys)
        return ret

    def format_date_keys(self, k: str, v: str, m: dict):
        for f in self.formatters:
            f.format_date_key(k, v, m)


dateformat_helpers = DateFormatHelpers(
    [
        DateFormatHelper(["%Y%m%d", "%Y-%m-%d"], ["yyyymmdd", "yyyy-mm-dd"]),
        DateFormatHelper(["%Y%m", "%Y-%m"], ["yyyymm", "yyyy-mm"])
    ]
)


def evalTmplRecurse(templateKeys: dict):
    """
    We need to potentially format each of the value with some of the
    other values.  So some sort of recursion must happen i.e. we first
    find the k,v which are not templates and use them to format the
    unformatted values that we can.

    :param templateKeys: The values of the dict may be a template.
    :return: dict with same keys as templateKeys but fully formatted values
    """
    templateKeysCopy = templateKeys.copy()
    keysNeeded = {}
    usableKeys = {}

    for (k, v) in templateKeys.items():
        dateformat_helpers.format_date_keys(k, v, templateKeysCopy)

    for (k, v) in templateKeysCopy.items():
        keys = keysOfTemplate(v)
        if len(keys):
            keysNeeded[k] = keys
        else:
            usableKeys[k] = templateKeysCopy[k]

    while len(keysNeeded):
        remaining = len(keysNeeded)
        for (k, v) in templateKeysCopy.items():
            if k in usableKeys:
                continue

            needed = keysNeeded[k]
            if needed.issubset(usableKeys.keys()):
                templateKeysCopy[k] = templateKeysCopy[k].format(
                    **usableKeys)
                usableKeys[k] = templateKeysCopy[k]
                del keysNeeded[k]
        if remaining == len(keysNeeded):
            raise Exception("template vars: " + str(templateKeys) +
                            " contains a circular reference")

    for k, v in templateKeysCopy.items():
        if k.endswith("_dash2uscore"):
            templateKeysCopy[k] = templateKeysCopy[k].replace("-", "_")

    return templateKeysCopy


def keysOfTemplate(strr):
    if not isinstance(strr, str):
        return set()
    return set([x[1] for x in string.Formatter().parse(strr) if x[1]])


def handleDateField(dt: datetime, val, key) -> str:
    """
    val can be a string in which case we return it
    it can be an int in which case we evaluate it as a date that
    many years/months/days/hours in the future or ago

    We may get more complicated in the future to support ranges, etc

    :return:
    """

    if not isinstance(dt, datetime):
        raise Exception("dt must be an intance of datetime")

    if key.endswith("yyyy"):
        func = relativedelta
        param = "years"
        format = "%Y"
    elif key.endswith("yyyymm"):
        func = relativedelta
        param = "months"
        format = "%Y%m"
    elif key.endswith("yyyymmdd"):
        func = timedelta
        param = "days"
        format = "%Y%m%d"
    elif key.endswith("yyyymmddhh"):
        func = timedelta
        param = "hours"
        format = "%Y%m%d%H"
    else:
        return None

    toFormat = []
    if isinstance(val, int):
        params = {param: val}
        newdate = dt + func(**params)
        toFormat.append(newdate)
    elif isinstance(val, list) and len(val) == 2:
        val = sorted([int(x) for x in val])
        for v in range(int(val[0]), int(val[1]) + 1):
            params = {param: v}
            newdate = dt + func(**params)
            toFormat.append(newdate)
    elif isinstance(val, str):
        return [val]
    else:
        raise Exception("Invalid datetime values to fill out.  Must "
                        "be int, 2 element array of ints, or string")

    return sorted([dt.strftime(format) for dt in toFormat])


def explodeTemplate(templateVars: dict):
    """
    Goal of this method is simply to replace
    any array elements with simple string expansions

    :return:
    """

    # check for key with yyyymm, yyyymmdd, or yyyymmddhh
    # and handle it specially
    for (k, v) in templateVars.items():
        date_vals = handleDateField(datetime.now(), v, k)
        if date_vals is not None:
            templateVars[k] = date_vals

    topremute = []
    for (k, v) in templateVars.items():
        items = []
        if isinstance(v, list):
            for vv in v:
                items.append((k, vv))
        else:
            items.append((k, v))
        topremute.append(items)

    collect = []
    out = []
    makeCombinations(topremute, out, collect)
    # now make maps
    maps = []
    for s in collect:
        maps.append(dict(s))
    return maps


def makeCombinations(lists: list, out: list, collect: list):
    """
        given a list of lists, generate a list of lists which
        has all combinations of each element as a a member

        Example:
            [[a,b], [c,d]] becomes

            [
             [a,c],
             [a,d],
             [b,c],
             [b,d]
            ]
    """
    if not len(lists):
        collect.append(out)
        return

    listsCopy = lists.copy()
    first = listsCopy.pop(0)
    for m in first:
        outCopy = out.copy()
        outCopy.append(m)
        makeCombinations(listsCopy, outCopy, collect)
