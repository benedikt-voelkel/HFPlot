import sys
import importlib
from glob import glob

EXAMPLES_PATH="examples"

def test_examples():

    passed = True

    example_scripts = glob(f"{EXAMPLES_PATH}/example_*.py")
    for es in example_scripts:
        # Make some effort to import all potential example scripts
        name = es.rstrip(".py")
        name = name.replace("/", ".")
        mod = importlib.import_module(name)
        try:
            passed = passed and mod.run_example(False)
        except Exception as e:
            # if that cannot be executed for any reason, fail test
            print(e)
            passed = False
    assert passed
