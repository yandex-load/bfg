class CliArgumentError(Exception):
    '''
    Raised when error in CLI found.
    '''


class ConfigurationError(Exception):
    '''
    Raised when error in configuration found.
    '''


class AmmoFileError(Exception):
    '''
    Raised when failed to read ammo file properly.
    '''


class StpdFileError(Exception):
    '''
    Raised when failed to read stpd file properly.
    '''
