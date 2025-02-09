from os.path import dirname, basename, isfile, join
import glob
import importlib

# List all python (.py) files in the current folder and assign them to __all__
    # __all__ manages the "from package import *" feature - it's not strictly necessary in our
    # case because we're not importing them this way, but I've done it for good measure
modules = glob.glob(join(dirname(__file__), "*.py"))
__all__ = [basename(f)[:-3] for f in modules if isfile(f) and not f.endswith('__init__.py')]

from . import *

# What I really want is to import each module automatically, which I can do with their names
#   and the importlib library
def get_automation_routines():
    auto_routines_dict = {}
    for module_name in __all__:
        routine = importlib.import_module("."+module_name, package="automation_routines")
        auto_routines_dict.update({module_name:routine})

    return auto_routines_dict