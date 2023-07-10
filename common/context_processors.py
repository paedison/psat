import inspect
from common.constants import (
    icon as common_icon,
    psat as common_psat,
    urls as common_urls
)


def get_constants(module):
    constants = {}
    for name, value in inspect.getmembers(module):
        if name.isupper():  # Check if the name is all uppercase (convention for constants)
            constants[name] = value
    return constants


icon_constants = get_constants(common_icon)
psat_constants = get_constants(common_psat)
urls_constants = get_constants(common_urls)


def global_settings(request):
    if request:
        global_constants = {**icon_constants, **psat_constants, **urls_constants}
        return global_constants
