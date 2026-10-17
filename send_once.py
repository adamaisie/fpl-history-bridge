import runpy

# Keep the existing Render start command working as a persistent web service.
# Email delivery is handled separately by the scheduled review.
runpy.run_module('app', run_name='__main__')
