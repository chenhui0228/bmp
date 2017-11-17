
class PolicyNotAuthorized(Exception):
    """Default exception raised for policy enforcement failure."""

    def __init__(self, rule, target, creds):
        msg = ("%(rule)s is disallowed by policy") % {'rule': rule}
        super(PolicyNotAuthorized, self).__init__(msg)


class DuplicatePolicyError(Exception):
    def __init__(self, name):
        msg = ('Policy %(name)s is already registered') % {'name': name}
        super(DuplicatePolicyError, self).__init__(msg)


class PolicyNotRegistered(Exception):
    def __init__(self, name):
        msg = ('Policy %(name)s has not been registered') % {'name': name}
        super(PolicyNotRegistered, self).__init__(msg)


class InvalidDefinitionError(Exception):
    def __init__(self, names):
        msg = ('Policies %(names)s are not well defined. Check logs for '
                'more details.') % {'names': names}
        super(InvalidDefinitionError, self).__init__(msg)


class InvalidRuleDefault(Exception):
    def __init__(self, error):
        msg = (('Invalid policy rule default: '
                 '%(error)s.') % {'error': error})
        super(InvalidRuleDefault, self).__init__(msg)

class ConfigFilesNotFoundError(Exception):
    def __init__(self, error):
        msg = (('confile file is not found: '
                 '%(error)s.') % {'error': error})
        super(ConfigFilesNotFoundError, self).__init__(msg)
