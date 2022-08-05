import pstats
import sys
p = pstats.Stats(sys.argv[1])
p.strip_dirs().sort_stats('cumtime').print_callers('io.open').print_callers('processTemplateVar').print_stats()
