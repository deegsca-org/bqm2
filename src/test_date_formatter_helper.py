import datetime
import unittest

from dateutil.relativedelta import relativedelta

import date_formatter_helper


class Test(unittest.TestCase):

    def test_formatters_bad_date_throw_exception(self):
        try:
            date_formatter_helper.helpers.format_all_date_keys({"yyyymm": "aaa"})
        except ValueError:
            pass

    def test_formatters_show_new_keys(self):
        suffixes = ["yyyy",
                    "mm",
                    "mmm",
                    "MMM",
                    "Mmm",
                    "yy",
                    ]
        quarter = ["qm1_mm",
                   "qm2_mm",
                   "qm3_mm"]
        quarter_yyyy = ["qm1_yyyy",
                        "qm2_yyyy",
                        "qm3_yyyy"]
        quarter_dd = ["qm1_dd",
                        "qm2_dd",
                        "qm3_dd"]
        quarter_yy = ["qm1_yy",
                      "qm2_yy",
                      "qm3_yy"]
        quarter_MMM = ["qm1_MMM",
                      "qm2_MMM",
                      "qm3_MMM"]

        month_set = set(["yyyymm" + "_" + s for s in suffixes + quarter + quarter_yyyy + quarter_yy + quarter_MMM])
        foo_month_set = set(["foo_" + x for x in month_set])
        day_set = set(["yyyymmdd" + "_" + s  for s in suffixes + ["dd"] + quarter + quarter_yyyy + quarter_dd])
        foo_day_set = set(["foo_" + x for x in day_set])
        hour_set = set(["yyyymmddhh" + "_" + s for s in suffixes + ["dd", "hh"]])
        foo_hour_set = set(["foo_" + x for x in hour_set])

        self.assertEqual(month_set, date_formatter_helper.helpers.show_new_keys(["yyyymm"]))
        self.assertEqual(foo_month_set, date_formatter_helper.helpers.show_new_keys(["foo_yyyymm"]))
        self.assertEqual(day_set, date_formatter_helper.helpers.show_new_keys(["yyyymmdd"]))
        self.assertEqual(foo_day_set, date_formatter_helper.helpers.show_new_keys(["foo_yyyymmdd"]))
        self.assertEqual(hour_set, date_formatter_helper.helpers.show_new_keys(["yyyymmddhh"]))
        self.assertEqual(foo_hour_set, date_formatter_helper.helpers.show_new_keys(["foo_yyyymmddhh"]))

    def test_formatters_format_all_keys(self):
        inp = {
            "yyyy": "2022",
            "yyyymm": "202212",
            "yyyymmdd": "20221231",
            "yyyymmddhh": "2022123101",
            "foo_yyyy": "2022",
            "foo_yyyymm": "202212",
            "foo_yyyymmdd": "20221231",
            "foo_yyyymmddhh": "2022123101",
        }

        expected = {
          "yyyy": "2022",
          "yyyymm": "202212",
          "yyyymmdd": "20221231",
          "yyyymmddhh": "2022123101",
          "foo_yyyy": "2022",
          "foo_yyyymm": "202212",
          "foo_yyyymmdd": "20221231",
          "foo_yyyymmddhh": "2022123101",
          "yyyymmddhh_yyyy": "2022",
          "yyyymmddhh_mm": "12",
          "yyyymmddhh_dd": "31",
          "yyyymmddhh_hh": "01",
          "yyyymmddhh_mmm": "dec",
          "yyyymmddhh_MMM": "DEC",
          "yyyymmddhh_Mmm": "Dec",
          "yyyymmddhh_yy": "22",
          "foo_yyyymmddhh_yyyy": "2022",
          "foo_yyyymmddhh_mm": "12",
          "foo_yyyymmddhh_dd": "31",
          "foo_yyyymmddhh_hh": "01",
          "foo_yyyymmddhh_mmm": "dec",
          "foo_yyyymmddhh_MMM": "DEC",
          "foo_yyyymmddhh_Mmm": "Dec",
          "foo_yyyymmddhh_yy": "22",
          "yyyymmdd_yyyy": "2022",
          "yyyymmdd_yy": "22",
          "yyyymmdd_mm": "12",
          "yyyymmdd_dd": "31",
          "yyyymmdd_mmm": "dec",
          "yyyymmdd_MMM": "DEC",
          "yyyymmdd_Mmm": "Dec",
          "yyyymmdd_qm1_mm": "10",
          "yyyymmdd_qm2_mm": "11",
          "yyyymmdd_qm3_mm": "12",
          "yyyymmdd_qm1_dd": "31",
          "yyyymmdd_qm2_dd": "30",
          "yyyymmdd_qm3_dd": "31",
          "yyyymmdd_qm1_yyyy": "2022",
          "yyyymmdd_qm2_yyyy": "2022",
          "yyyymmdd_qm3_yyyy": "2022",
          "foo_yyyymmdd_yy": "22",
          "foo_yyyymmdd_yyyy": "2022",
          "foo_yyyymmdd_mm": "12",
          "foo_yyyymmdd_dd": "31",
          "foo_yyyymmdd_mmm": "dec",
          "foo_yyyymmdd_MMM": "DEC",
          "foo_yyyymmdd_Mmm": "Dec",
          "foo_yyyymmdd_qm1_mm": "10",
          "foo_yyyymmdd_qm2_mm": "11",
          "foo_yyyymmdd_qm3_mm": "12",
          "foo_yyyymmdd_qm1_dd": "31",
          "foo_yyyymmdd_qm2_dd": "30",
          "foo_yyyymmdd_qm3_dd": "31",
          "foo_yyyymmdd_qm1_yyyy": "2022",
          "foo_yyyymmdd_qm2_yyyy": "2022",
          "foo_yyyymmdd_qm3_yyyy": "2022",
          "yyyymm_yyyy": "2022",
          "yyyymm_mm": "12",
          "yyyymm_mmm": "dec",
          "yyyymm_MMM": "DEC",
          "yyyymm_Mmm": "Dec",
          "yyyymm_qm1_mm": "10",
          "yyyymm_qm2_mm": "11",
          "yyyymm_qm3_mm": "12",
          "yyyymm_qm1_yyyy": "2022",
          "yyyymm_qm2_yyyy": "2022",
          "yyyymm_qm3_yyyy": "2022",
          "yyyymm_qm1_yy": "22",
          "yyyymm_qm2_yy": "22",
          "yyyymm_qm3_yy": "22",
          "yyyymm_qm1_MMM": "OCT",
          "yyyymm_qm2_MMM": "NOV",
          "yyyymm_qm3_MMM": "DEC",
          "yyyymm_yy": "22",
          "foo_yyyymm_yyyy": "2022",
          "foo_yyyymm_mm": "12",
          "foo_yyyymm_mmm": "dec",
          "foo_yyyymm_MMM": "DEC",
          "foo_yyyymm_Mmm": "Dec",
          "foo_yyyymm_qm1_mm": "10",
          "foo_yyyymm_qm2_mm": "11",
          "foo_yyyymm_qm3_mm": "12",
          "foo_yyyymm_qm1_yyyy": "2022",
          "foo_yyyymm_qm2_yyyy": "2022",
          "foo_yyyymm_qm3_yyyy": "2022",
          "foo_yyyymm_qm1_yy": "22",
          "foo_yyyymm_qm2_yy": "22",
          "foo_yyyymm_qm3_yy": "22",
          "foo_yyyymm_qm1_MMM": "OCT",
          "foo_yyyymm_qm2_MMM": "NOV",
          "foo_yyyymm_qm3_MMM": "DEC",
          "foo_yyyymm_yy": "22"
        }

        date_formatter_helper.helpers.format_all_date_keys(inp)
        self.assertEqual(expected, inp)


    def test_quarter(self):
        d = datetime.datetime.strptime("20120101", "%Y%m%d")
        months = [d + relativedelta(months=x) for x in range(12)]
        firsts = [date_formatter_helper.quarter(da, 1).month for da in months]
        seconds = [date_formatter_helper.quarter(da, 2).month for da in months]
        thirds = [date_formatter_helper.quarter(da, 3).month for da in months]

        ef = [1, 1, 1, 4, 4, 4, 7, 7, 7, 10, 10, 10]
        es = [11, 2, 2, 2, 5, 5, 5, 8, 8, 8, 11, 11]
        et = [12, 12, 3, 3, 3, 6, 6, 6, 9, 9, 9, 12]

        assert firsts == ef
        assert seconds == es
        assert thirds == et
