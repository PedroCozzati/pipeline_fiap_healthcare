import py_compile
py_compile.compile('pipeline/ingest.py', doraise=True)
py_compile.compile('pipeline/start_api.py', doraise=True)
print('compiled ok')
