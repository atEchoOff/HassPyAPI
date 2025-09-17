import inspect

def script(func):
    '''
    Decorator that marks a class method as a script, to be run when calling start_scripts() in __init__
    '''
    func._is_script = True
    return func

def start_scripts(self):
    '''
    Run all methods in self which are decorated with @script
    Helpful for initializing various hass scripts
    '''
    for _, method in inspect.getmembers(self, predicate=inspect.ismethod):
        if getattr(method, "_is_script", False):
            method()