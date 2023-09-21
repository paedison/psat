import inspect
from common.constants import icon


def get_constants(module):
    constants = {}
    for name, value in inspect.getmembers(module):
        if name.isupper():  # Check if the name is all uppercase (convention for constants)
            constants[name] = value
    return constants


icon_constants = get_constants(icon)


def global_settings(request):
    if request:
        global_constants = {
            **icon_constants,
        }
        return global_constants
