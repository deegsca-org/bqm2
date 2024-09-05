import calendar
from datetime import datetime
from dateutil.relativedelta import relativedelta


def quarter(d: datetime, monthofquarter):
    assert monthofquarter >= 1 and monthofquarter <= 3
    return d - relativedelta(months=(d.month - monthofquarter) % 3)


class DateFormatHelper:
    def __init__(self, formats: list, formats_suffixes: list):
        """
        :param formats: datetime formats
        :param formats_suffixes: template key suffixes or endings
        """
        self.formats = formats
        self.formats_suffixes = formats_suffixes
        self.cache = {}

        assert len(formats)
        assert len(formats) == len(formats_suffixes)

    def format_date_key(self, k: str, v: str, m: dict):
        if k.endswith(f"_{self.formats_suffixes[0]}") \
                or k == self.formats_suffixes[0]:
            # given k, v, there's only one set of new k, v which should
            # go into m.  So we cache them
            toset = {}
            if f"{k}:{v}" in self.cache:
                toset = self.cache[f"{k}:{v}"]
            else:
                for i in range(1, len(self.formats_suffixes)):
                    newkey = k.replace(self.formats_suffixes[0],
                                       self.formats_suffixes[i])

                    toformat = datetime.strptime(v, self.formats[0])

                    if "_qm1" in self.formats_suffixes[i]:
                        toformat = quarter(toformat, 1)
                    elif "_qm2" in self.formats_suffixes[i]:
                        toformat = quarter(toformat, 2)
                    elif "_qm3" in self.formats_suffixes[i]:
                        toformat = quarter(toformat, 3)
                    newval = toformat.strftime(self.formats[i])
                    toset[newkey] = (newval, self.formats_suffixes[i])

            for k, vals in toset.items():
                v, suffix = vals
                if suffix.endswith("_MMM"):
                    v = v.upper()
                elif suffix.endswith("_mmm"):
                    v = v.lower()
                if k in m:
                    continue
                m[k] = v
            self.cache[f"{k}:{v}"] = toset

    def show_new_keys(self, keys: list):
        m = set()
        for k in keys:
            if k == self.formats_suffixes[0] \
                    or k.endswith(f"_{self.formats_suffixes[0]}"):
                for i in range(1, len(self.formats)):
                    m.add(k.replace(self.formats_suffixes[0],
                                    self.formats_suffixes[i]))
        return m


class DateFormatHelpers:
    def __init__(self, formatters):
        self.formatters = formatters
        assert len(formatters)

    def show_new_keys(self, keys: list):
        assert isinstance(keys, list)
        ret = set()
        for f in self.formatters:
            ret.update(f.show_new_keys(keys))
        return ret

    def format_date_keys(self, k: str, v: str, m: dict):
        for f in self.formatters:
            f.format_date_key(k, v, m)

    def format_all_date_keys(self, m: dict):
        for f in self.formatters:
            kv = [x for x in m.items()]
            for x in kv:
                try:
                    f.format_date_key(x[0], x[1], m)
                except ValueError as e:
                    raise ValueError(f"Unable to format "
                                     f"key/value "
                                     f"{x[0]}/{x[1]}: {e}")


helpers = DateFormatHelpers(
    [
        DateFormatHelper(["%Y%m%d%H", "%Y", "%m", "%d", "%H", "%b", "%b", "%b", "%y"],
                         ["yyyymmddhh", "yyyymmddhh_yyyy",
                          "yyyymmddhh_mm", "yyyymmddhh_dd",
                          "yyyymmddhh_hh", "yyyymmddhh_mmm",
                          "yyyymmddhh_MMM", "yyyymmddhh_Mmm", "yyyymmddhh_yy"]),

        DateFormatHelper(["%Y%m%d", "%Y", "%m", "%d", '%y', "%b", "%b", "%b", "%m", "%m", "%m",
                          "%Y", "%Y", "%Y", "%d", "%d", "%d"],
                         ["yyyymmdd", "yyyymmdd_yyyy",
                          "yyyymmdd_mm", "yyyymmdd_dd",
                          "yyyymmdd_yy", "yyyymmdd_mmm",
                          "yyyymmdd_MMM", "yyyymmdd_Mmm",
                          "yyyymmdd_qm1_mm", "yyyymmdd_qm2_mm", "yyyymmdd_qm3_mm",
                          "yyyymmdd_qm1_yyyy", "yyyymmdd_qm2_yyyy", "yyyymmdd_qm3_yyyy",
                          "yyyymmdd_qm1_dd", "yyyymmdd_qm2_dd", "yyyymmdd_qm3_dd",
                          ]),

        DateFormatHelper(["%Y%m", "%Y", "%m", "%b", "%b", "%b", "%y",
                          "%m", "%m", "%m", "%Y", "%Y", "%Y",
                          "%y", "%y", "%y", "%b", "%b", "%b",
                          ],
                         ["yyyymm", "yyyymm_yyyy",
                          "yyyymm_mm", "yyyymm_mmm",
                          "yyyymm_MMM", "yyyymm_Mmm",
                          "yyyymm_yy",
                          "yyyymm_qm1_mm", "yyyymm_qm2_mm", "yyyymm_qm3_mm",
                          "yyyymm_qm1_yyyy", "yyyymm_qm2_yyyy", "yyyymm_qm3_yyyy",
                          "yyyymm_qm1_yy", "yyyymm_qm2_yy", "yyyymm_qm3_yy",
                          "yyyymm_qm1_MMM", "yyyymm_qm2_MMM", "yyyymm_qm3_MMM"
                          ]),
        ]
)
