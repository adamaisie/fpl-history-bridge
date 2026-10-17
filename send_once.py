from app import report

# Emit one verified live snapshot at service startup for report validation.
try:
    report(gw=6)
except Exception as exc:
    print('FPL_STARTUP_REPORT_ERROR=' + repr(exc), flush=True)

import runpy
runpy.run_module('app', run_name='__main__')
