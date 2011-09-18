from pymongo import Connection
from Services import config

class Instance:
    """ A python singleton """

    class __impl:
        """ Implementation of the singleton interface """

        def exceptions(self):
            return Connection(config.MONGODB_HOST, config.MONGODB_PORT)[config.MONGODB_NAME]['exception']
        
        def exception_groups(self):
            return Connection(config.MONGODB_HOST, config.MONGODB_PORT)[config.MONGODB_NAME]['exception_group']

        def applications(self):
            return Connection(config.MONGODB_HOST, config.MONGODB_PORT)[config.MONGODB_NAME]['applications']

        def accounts(self):
            return Connection(config.MONGODB_HOST, config.MONGODB_PORT)[config.MONGODB_NAME]['accounts']

        def statistics(self):
            return Connection(config.MONGODB_HOST, config.MONGODB_PORT)[config.MONGODB_NAME]['statistics']

        def db(self):
            return Connection(config.MONGODB_HOST, config.MONGODB_PORT)[config.MONGODB_NAME]

    # storage for the instance reference
    __instance = None

    def __init__(self):
        """ Create singleton instance """
        # Check whether we already have an instance
        if Instance.__instance is None:
            # Create and remember instance
            Instance.__instance = Instance.__impl()

        # Store instance reference as the only member in the handle
        self.__dict__['_Instance__instance'] = Instance.__instance

    def __getattr__(self, attr):
        """ Delegate access to implementation """
        return getattr(self.__instance, attr)

    def __setattr__(self, attr, value):
        """ Delegate access to implementation """
        return setattr(self.__instance, attr, value)

