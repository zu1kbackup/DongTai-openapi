from AgentServer.settings import BASE_DIR
from os import walk, chdir, getcwd
from os.path import join
from importlib import import_module
from inspect import getmembers,isclass
from functools import wraps
PLUGIN_DICT = {}


class DongTaiPlugin:
    appname = 'appserver'
    target_class_name = 'SaasMethodPoolHandler'
    target_func_name = 'save_method_call'
    target_module_name = 'apiserver.report.handler.saas_method_pool_handler'

    def before_patch_function(self, func_args, func_kwargs):
        pass

    def after_patch_function(self, func_args, func_kwargs, func_res):
        pass

    def _monkey_patch(self):
        module = import_module(self.target_module_name)
        target_class = getattr(module, self.target_class_name)
        origin_func = getattr(target_class, self.target_func_name)
        setattr(target_class, f'_origin_{self.target_func_name}', origin_func)
        self.target_class = target_class

        @wraps(origin_func)
        def patched_function(*args, **kwargs):
            self.before_patch_function(args, kwargs)
            res = origin_func(*args, **kwargs)
            final_res = self.after_patch_function(args, kwargs, res)
            return final_res

        setattr(target_class, self.target_func_name,
                patched_function)

    def monkey_patch(self, appname):
        if self.appname == appname:
            self._monkey_patch()


def monkey_patch(appname):
    plugin_dict = get_plugin_dict()
    for plugin in plugin_dict.get(appname, []):
        plugin().monkey_patch(appname)


def get_plugin_dict():
    if PLUGIN_DICT:
        return PLUGIN_DICT
    previous_path = getcwd()
    PLUGIN_ROOT_PATH = join(BASE_DIR, 'plugin')
    for root, directories, files in walk(top=getcwd(), topdown=False):
        for file_ in files:
            if file_.startswith('plug_') and file_.endswith('.py'):
                packname = '.'.join([root.replace(BASE_DIR+'/', '').replace('/',
                                                       '.'),file_.replace('.py','')])
                mod = import_module(packname)
                plugin_classes = filter(lambda x: _plug_class_filter(x),
                                        getmembers(mod))
                for name, plug_class in plugin_classes:
                    if PLUGIN_DICT.get(plug_class.appname):
                        PLUGIN_DICT[plug_class.appname] += [plug_class]
                    else:
                        PLUGIN_DICT[plug_class.appname] = [plug_class]
    chdir(previous_path)
    return PLUGIN_DICT

def _plug_class_filter(tup):
    return tup[0].startswith('Plug') and isclass(
        tup[1]) and issubclass(tup[1], DongTaiPlugin)
