import os.path
import pkg_resources

import appdirs
import yaml


appname = "binglide"


def get_default_cache_dir():
    a = appdirs.AppDirs(appname)
    return a.user_cache_dir


def get_default_config(filename="config.yaml", mode="r"):

    a = appdirs.AppDirs(appname)
    for loc in (a.user_config_dir, a.site_config_dir):
        try:
            filepath = os.path.join(a.user_config_dir, filename)
            return open(filepath, mode)
        except OSError:
            pass

    return pkg_resources.resource_stream(__name__, "config.yaml")


def load_config(stream=None, *args, **kwargs):

    if stream is not None:
        return yaml.load(stream)

    with get_default_config(*args, **kwargs) as cf:
        return yaml.load(cf)
