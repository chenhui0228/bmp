import sys
import six
import os
from exception import *
sys.path.append('../')

from pattern import Singleton
import logging
logger = logging.getLogger('backup')
import warnings
import yaml
import jsontools as jsonutils

import _cache_handler
import _checks
import _parser

from db.sqlalchemy import copy

register = _checks.register
"""Register a function or :class:`.Check` class as a policy check.

:param name: Gives the name of the check type, e.g., "rule",
             "role", etc.  If name is ``None``, a default check type
             will be registered.
:param func: If given, provides the function or class to register.
             If not given, returns a function taking one argument
             to specify the function or class to register,
             allowing use as a decorator.
"""

Check = _checks.Check
"""A base class to allow for user-defined policy checks.

:param kind: The kind of the check, i.e., the field before the ``:``.
:param match: The match of the check, i.e., the field after the ``:``.

"""

AndCheck = _checks.AndCheck
"""Implements the "and" logical operator.

A policy check that requires that a list of other checks all return True.

:param list rules: rules that will be tested.

"""

NotCheck = _checks.NotCheck
"""Implements the "not" logical operator.

A policy check that inverts the result of another policy check.

:param rule: The rule to negate.

"""

OrCheck = _checks.OrCheck
"""Implements the "or" operator.

A policy check that requires that at least one of a list of other
checks returns ``True``.

:param rules: A list of rules that will be tested.

"""

RuleCheck = _checks.RuleCheck
"""Recursively checks credentials based on the defined rules."""


def parse_file_contents(data):
    """Parse the raw contents of a policy file.

    Parses the contents of a policy file which currently can be in either
    yaml or json format. Both can be parsed as yaml.

    :param data: A string containing the contents of a policy file.
    :returns: A dict of the form {'policy_name1': 'policy1',
                                  'policy_name2': 'policy2,...}
    """
    try:
        # NOTE(snikitin): jsonutils.loads() is much faster than
        # yaml.safe_load(). However jsonutils.loads() parses only JSON while
        # yaml.safe_load() parses JSON and YAML. So here we try to parse data
        # by jsonutils.loads() first. In case of failure yaml.safe_load()
        # will be used instead.
        parsed = jsonutils.loads(data)
    except ValueError:
        try:
            parsed = yaml.safe_load(data)
        except yaml.YAMLError as e:
            # For backwards-compatibility, convert yaml error to ValueError,
            # which is what JSON loader raised.
            raise ValueError(six.text_type(e))
    return parsed or {}


class Rules(dict):
    """A store for rules. Handles the default_rule setting directly."""

    @classmethod
    def load(cls, data, default_rule=None):
        """Allow loading of YAML/JSON rule data.

        .. versionadded:: 1.5.0

        """
        parsed_file = parse_file_contents(data)

        # Parse the rules
        rules = {k: _parser.parse_rule(v) for k, v in parsed_file.items()}

        return cls(rules, default_rule)

    @classmethod
    def load_json(cls, data, default_rule=None):
        """Allow loading of YAML/JSON rule data.

        .. warning::
            This method is deprecated as of the 1.5.0 release in favor of
            :meth:`load` and may be removed in the 2.0 release.

        """
        warnings.warn(
            'The load_json() method is deprecated as of the 1.5.0 release in '
            'favor of load() and may be removed in the 2.0 release.',
            DeprecationWarning)
        return cls.load(data, default_rule)

    @classmethod
    def from_dict(cls, rules_dict, default_rule=None):
        """Allow loading of rule data from a dictionary."""

        # Parse the rules stored in the dictionary
        rules = {k: _parser.parse_rule(v) for k, v in rules_dict.items()}

        return cls(rules, default_rule)

    def __init__(self, rules=None, default_rule=None):
        """Initialize the Rules store."""

        super(Rules, self).__init__(rules or {})
        self.default_rule = default_rule

    def __missing__(self, key):
        """Implements the default rule handling."""

        if isinstance(self.default_rule, dict):
            raise KeyError(key)

        # If the default rule isn't actually defined, do something
        # reasonably intelligent
        if not self.default_rule:
            raise KeyError(key)

        if isinstance(self.default_rule, _checks.BaseCheck):
            return self.default_rule

        # We need to check this or we can get infinite recursion
        if self.default_rule not in self:
            raise KeyError(key)

        elif isinstance(self.default_rule, six.string_types):
            return self[self.default_rule]

    def __str__(self):
        """Dumps a string representation of the rules."""

        # Start by building the canonical strings for the rules
        out_rules = {}
        for key, value in self.items():
            # Use empty string for singleton TrueCheck instances
            if isinstance(value, _checks.TrueCheck):
                out_rules[key] = ''
            else:
                out_rules[key] = str(value)

        # Dump a pretty-printed JSON representation
        return jsonutils.dumps(out_rules, indent=4)




@six.add_metaclass(Singleton)
class PolicyManager(object):

    def __init__(self, conf, policy_file=None, rules=None,
                 default_rule=None, use_conf=True, overwrite=True):
        self.conf = conf
        policy = self.conf.get('policy')
        self.default_rule = (default_rule or
                             policy.get('policy_default_rule', {})
                             if policy else {})

        self.rules = Rules(rules, self.default_rule)
        self.registered_rules = {}
        self.file_rules = {}
        self.policy_dirs = policy.get('policy_dirs', {}) if policy else {}
        self.policy_path = policy.get('policy_path', {}) if policy else '.'
        self.policy_file = policy_file or policy.get('policy_file')
        self._loaded_files = []
        self._file_cache = {}
        self.use_conf = use_conf
        self.overwrite = overwrite
        self.init()

    def init(self):
        self.load_rules()

    def set_rules(self, rules, overwrite=True, use_conf=False):
        """Create a new :class:`Rules` based on the provided dict of rules.

        :param dict rules: New rules to use.
        :param overwrite: Whether to overwrite current rules or update them
                          with the new rules.
        :param use_conf: Whether to reload rules from cache or config file.
        """

        if not isinstance(rules, dict):
            raise TypeError(('Rules must be an instance of dict or Rules, '
                            'got %s instead') % type(rules))
        self.use_conf = use_conf
        if overwrite:
            self.rules = Rules(rules, self.default_rule)
        else:
            self.rules.update(rules)

    def clear(self):
        """Clears :class:`Enforcer` contents.

        This will clear this instances rules, policy's cache, file cache
        and policy's path.
        """
        self.set_rules({})
        self.default_rule = None
        self.policy_path = None
        self._loaded_files = []
        self._file_cache.clear()
        self.registered_rules = {}
        self.file_rules = {}

    def _record_file_rules(self, data, overwrite=False):
        """Store a copy of rules loaded from a file.

        It is useful to be able to distinguish between rules loaded from a file
        and those registered by a consuming service. In order to do so we keep
        a record of rules loaded from a file.

        :param data: The raw contents of a policy file.
        :param overwrite: If True clear out previously loaded rules.
        """
        if overwrite:
            self.file_rules = {}
        parsed_file = parse_file_contents(data)
        for name, check_str in parsed_file.items():
            self.file_rules[name] = RuleDefault(name, check_str)

    def _load_policy_file(self, path, force_reload, overwrite=True):
        reloaded, data = _cache_handler.read_cached_file(
            self._file_cache, path, force_reload=force_reload)
        if reloaded or not self.rules:
            rules = Rules.load(data, self.default_rule)
            self.set_rules(rules, overwrite=overwrite, use_conf=True)
            self._record_file_rules(data, overwrite)
            self._loaded_files.append(path)
            logger.debug('Reloaded policy file: %(path)s', {'path': path})

    @staticmethod
    def _walk_through_policy_directory(path, func, *args):
        if not os.path.isdir(path):
            raise ValueError('%s is not a directory' % path)
        # We do not iterate over sub-directories.
        policy_files = next(os.walk(path))[2]
        policy_files.sort()
        for policy_file in [p for p in policy_files if not p.startswith('.')]:
            func(os.path.join(path, policy_file), *args)


    @staticmethod
    def _is_directory_updated(cache, path):
        # Get the current modified time and compare it to what is in
        # the cache and check if the new mtime is greater than what
        # is in the cache
        mtime = 0
        if os.path.exists(path):
            # Make a list of all the files
            files = [path] + [os.path.join(path, file) for file in
                              os.listdir(path)]
            # Pick the newest one, let's use its time.
            mtime = os.path.getmtime(max(files, key=os.path.getmtime))
        cache_info = cache.setdefault(path, {})
        if mtime > cache_info.get('mtime', 0):
            cache_info['mtime'] = mtime
            return True
        return False


    def load_rules(self, force_reload=False):
        if force_reload:
            self.use_conf = force_reload
        if self.use_conf:
            if not self.policy_path:
                logger.debug('The policy file %s could not be found.',
                          self.policy_file)

        if self.policy_path:
            self._load_policy_file(self.policy_path, force_reload,
                                   overwrite=self.overwrite)
        for path in self.policy_dirs:
            if (force_reload or self._is_directory_updated(
                    self._policy_dir_mtimes, path)):
                self._walk_through_policy_directory(path,
                                                    self._load_policy_file,
                                                    force_reload, False)

        for default in self.registered_rules.values():
            if default.name not in self.rules:
                self.rules[default.name] = default.check

        # Detect and log obvious incorrect rule definitions
        self.check_rules()


    def enforce(self, rule, target, creds, do_raise=False,
                exc=None, *args, **kwargs):
        """Checks authorization of a rule against the target and credentials.

        :param rule: The rule to evaluate.
        :type rule: string or :class:`BaseCheck`
        :param dict target: As much information about the object being operated
                            on as possible.
        :param dict creds: As much information about the user performing the
                           action as possible.
        :param do_raise: Whether to raise an exception or not if check
                        fails.
        :param exc: Class of the exception to raise if the check fails.
                    Any remaining arguments passed to :meth:`enforce` (both
                    positional and keyword arguments) will be passed to
                    the exception class. If not specified,
                    :class:`PolicyNotAuthorized` will be used.

        :return: ``False`` if the policy does not allow the action and `exc` is
                 not provided; otherwise, returns a value that evaluates to
                 ``True``.  Note: for rules using the "case" expression, this
                 ``True`` value will be the specified string from the
                 expression.
        """

        self.load_rules()

        # Allow the rule to be a Check tree
        if isinstance(rule, _checks.BaseCheck):
            result = rule(target, creds, self)
        elif not self.rules:
            # No rules to reference means we're going to fail closed
            result = False
        else:
            try:
                # Evaluate the rule
                result = self.rules[rule](target, creds, self)
            except KeyError:
                logger.debug('Rule [%s] does not exist', rule)
                # If the rule doesn't exist, fail closed
                result = False

        # If it is False, raise the exception if requested
        if do_raise and not result:
            if exc:
                raise exc(*args, **kwargs)

            raise PolicyNotAuthorized(rule, target, creds)

        return result

    def check_rules(self, raise_on_violation=False):
        """Look for rule definitions that are obviously incorrect."""
        undefined_checks = []
        cyclic_checks = []
        violation = False
        for name, check in self.rules.items():
            if self._undefined_check(check):
                undefined_checks.append(name)
                violation = True
            if self._cycle_check(check):
                cyclic_checks.append(name)
                violation = True

        if undefined_checks:
            logger.warning('Policies %(names)s reference a rule that is not '
                        'defined.', {'names': undefined_checks})
        if cyclic_checks:
            logger.warning('Policies %(names)s are part of a cyclical '
                        'reference.', {'names': cyclic_checks})

        if raise_on_violation and violation:
            raise InvalidDefinitionError(undefined_checks + cyclic_checks)

        return not violation


    def _undefined_check(self, check):
        '''Check if a RuleCheck references an undefined rule.'''
        if isinstance(check, RuleCheck):
            if check.match not in self.rules:
                # Undefined rule
                return True

        # An AndCheck or OrCheck is composed of multiple rules so check
        # each of those.
        rules = getattr(check, 'rules', None)
        if rules:
            for rule in rules:
                if self._undefined_check(rule):
                    return True
        return False


    def _cycle_check(self, check, seen=None):
        '''Check if RuleChecks cycle.

        Looking for something like:
        "foo": "rule:bar"
        "bar": "rule:foo"
        '''
        if seen is None:
            seen = set()

        if isinstance(check, RuleCheck):
            if check.match in seen:
                # Cycle found
                return True
            seen.add(check.match)
            if check.match in self.rules:
                # There can only be a cycle if the referenced rule is defined.
                if self._cycle_check(self.rules[check.match], seen):
                    return True

        # An AndCheck or OrCheck is composed of multiple rules so check
        # each of those.
        rules = getattr(check, 'rules', None)
        if rules:
            for rule in rules:
                # As there being an OrCheck or AndCheck, a copy of the father's
                # seen should be called here. In order that the checks in
                # different branchs are seperated.
                if self._cycle_check(rule, seen.copy()):
                    return True
        return False

    def check_policy(self, context, resource_name, action, target_obj=None):
        logger.debug('{0}, {1}, {2}'.format(context, resource_name, action))
        if context.get('is_superuser'):
            return True
        target = {
            'group_id': context.get('group_id'),
            'user_id': context.get('user_id'),
        }
        target.update(target_obj or {})
        _action = '%s:%s' % (resource_name.lower(), action.lower())
        return self.enforce(_action, target, context, do_raise=True)

class RuleDefault(object):
    """A class for holding policy definitions.

    It is required to supply a name and value at creation time. It is
    encouraged to also supply a description to assist operators.

    :param name: The name of the policy. This is used when referencing it
                 from another rule or during policy enforcement.
    :param check_str: The policy. This is a string  defining a policy that
                      conforms to the policy language outlined at the top of
                      the file.
    :param description: A plain text description of the policy. This will be
                        used to comment sample policy files for use by
                        deployers.
    :param deprecated_rule: :class:`.DeprecatedRule`
    :param deprecated_for_removal: indicates whether the policy is planned for
                                   removal in a future release.
    :param deprecated_reason: indicates why this policy is planned for removal
                              in a future release. Silently ignored if
                              deprecated_for_removal is False.
    :param deprecated_since: indicates which release this policy was deprecated
                             in. Accepts any string, though valid version
                             strings are encouraged. Silently ignored if
                             deprecated_for_removal is False.

    .. versionchanged 1.29
       Added *deprecated_rule* parameter.

    .. versionchanged 1.29
       Added *deprecated_for_removal* parameter.

    .. versionchanged 1.29
       Added *deprecated_reason* parameter.

    .. versionchanged 1.29
       Added *deprecated_since* parameter.
    """
    def __init__(self, name, check_str, description=None,
                 deprecated_rule=None, deprecated_for_removal=False,
                 deprecated_reason=None, deprecated_since=None):
        self.name = name
        self.check_str = check_str
        self.check = _parser.parse_rule(check_str)
        self.description = description
        self.deprecated_rule = copy.deepcopy(deprecated_rule) or []
        self.deprecated_for_removal = deprecated_for_removal
        self.deprecated_reason = deprecated_reason
        self.deprecated_since = deprecated_since

        if self.deprecated_rule:
            if not isinstance(self.deprecated_rule, DeprecatedRule):
                raise ValueError(
                    'deprecated_rule must be a DeprecatedRule object.'
                )

        if (deprecated_for_removal or deprecated_rule) and (
                deprecated_reason is None or deprecated_since is None):
            raise ValueError(
                '%(name)s deprecated without deprecated_reason or '
                'deprecated_since. Both must be supplied if deprecating a '
                'policy' % {'name': self.name}
            )

    def __str__(self):
        return '"%(name)s": "%(check_str)s"' % {'name': self.name,
                                                'check_str': self.check_str}

    def __eq__(self, other):
        """Equality operator.

        All check objects have a stable string representation. It is used for
        comparison rather than check_str because multiple check_str's may parse
        to the same check object. For instance '' and '@' are equivalent and
        the parsed rule string representation for both is '@'.

        The description does not play a role in the meaning of the check so it
        is not considered for equality.
        """
        # Name should match, check should match, and class should be equivalent
        # or one should be a subclass of the other.
        if (self.name == other.name and
                str(self.check) == str(other.check) and
                (isinstance(self, other.__class__) or
                 isinstance(other, self.__class__))):
            return True
        return False



class DocumentedRuleDefault(RuleDefault):
    """A class for holding policy-in-code policy objects definitions

    This class provides the same functionality as the RuleDefault class, but it
    also requires additional data about the policy rule being registered. This
    is necessary so that proper documentation can be rendered based on the
    attributes of this class. Eventually, all usage of RuleDefault should be
    converted to use DocumentedRuleDefault.

    :param operations: List of dicts containing each api url and
        corresponding http request method.

        Example::

            operations=[{'path': '/foo', 'method': 'GET'},
                        {'path': '/some', 'method': 'POST'}]
    """
    def __init__(self, name, check_str, description, operations,
                 deprecated_rule=None, deprecated_for_removal=False,
                 deprecated_reason=None, deprecated_since=None):
        super(DocumentedRuleDefault, self).__init__(
            name, check_str, description,
            deprecated_rule=deprecated_rule,
            deprecated_for_removal=deprecated_for_removal,
            deprecated_reason=deprecated_reason,
            deprecated_since=deprecated_since
        )
        self.operations = operations

    @property
    def description(self):
        return self._description

    @description.setter
    def description(self, value):
        # Validates description isn't empty.
        if not value:
            raise InvalidRuleDefault('Description is required')
        self._description = value

    @property
    def operations(self):
        return self._operations

    @operations.setter
    def operations(self, ops):
        if not isinstance(ops, list):
            raise InvalidRuleDefault('Operations must be a list')
        if not ops:
            raise InvalidRuleDefault('Operations list must not be empty')

        for op in ops:
            if 'path' not in op:
                raise InvalidRuleDefault('Operation must contain a path')
            if 'method' not in op:
                raise InvalidRuleDefault('Operation must contain a method')
            if len(op.keys()) > 2:
                raise InvalidRuleDefault('Operation contains > 2 keys')
        self._operations = ops


class DeprecatedRule(object):

    """Represents a Deprecated policy or rule.

    Here's how you can use it to change a policy's default role or rule. Assume
    the following policy exists in code::

        from oslo_policy import policy

        policy.DocumentedRuleDefault(
            name='foo:create_bar',
            check_str='role:fizz',
            description='Create a bar.',
            operations=[{'path': '/v1/bars', 'method': 'POST'}]
        )

    The next snippet will maintain the deprecated option, but allow
    ``foo:create_bar`` to default to ``role:bang`` instead of ``role:fizz``::

        deprecated_rule = policy.DeprecatedRule(
            name='foo:create_bar',
            check_str='role:fizz'
        )

        policy.DocumentedRuleDefault(
            name='foo:create_bar',
            check_str='role:bang',
            description='Create a bar.',
            operations=[{'path': '/v1/bars', 'method': 'POST'}],
            deprecated_rule=deprecated_rule,
            deprecated_reason='role:bang is a better default',
            deprecated_since='N'
        )

    DeprecatedRule can be used to change the policy name itself. Assume the
    following policy exists in code::

        from oslo_policy import policy

        policy.DocumentedRuleDefault(
            name='foo:post_bar',
            check_str='role:fizz',
            description='Create a bar.',
            operations=[{'path': '/v1/bars', 'method': 'POST'}]
        )

    For the sake of consistency, let's say we want to replace ``foo:post_bar``
    with ``foo:create_bar``, but keep the same ``check_str`` as the default. We
    can accomplish this by doing::

        deprecated_rule = policy.DeprecatedRule(
            name='foo:post_bar',
            check_str='role:fizz'
        )

        policy.DocumentedRuleDefault(
            name='foo:create_bar',
            check_str='role:fizz',
            description='Create a bar.',
            operations=[{'path': '/v1/bars', 'method': 'POST'}],
            deprecated_rule=deprecated_rule,
            deprecated_reason='foo:create_bar is more consistent',
            deprecated_since='N'
        )

    Finally, let's use DeprecatedRule to break a policy into more granular
    policies. Let's assume the following policy exists in code::

        policy.DocumentedRuleDefault(
            name='foo:bar',
            check_str='role:bazz',
            description='Create, read, update, or delete a bar.',
            operations=[
                {
                    'path': '/v1/bars',
                    'method': 'POST'
                },
                {
                    'path': '/v1/bars',
                    'method': 'GET'
                },
                {
                    'path': '/v1/bars/{bar_id}',
                    'method': 'GET'
                },
                {
                    'path': '/v1/bars/{bar_id}',
                    'method': 'PATCH'
                },
                {
                    'path': '/v1/bars/{bar_id}',
                    'method': 'DELETE'
                }
            ]
        )

    Here we can see the same policy is used to protect multiple operations on
    bars. This prevents operators from being able to assign different roles to
    different actions that can be taken on bar. For example, what if an
    operator wanted to require a less restrictive role or rule to list bars but
    a more restrictive rule to delete them? The following will introduce a
    policy that helps achieve that and deprecate the original, overly-broad
    policy::

        deprecated_rule = policy.DeprecatedRule(
            name='foo:bar',
            check_str='role:bazz'
        )

        policy.DocumentedRuleDefault(
            name='foo:create_bar',
            check_str='role:bang',
            description='Create a bar.',
            operations=[{'path': '/v1/bars', 'method': 'POST'}],
            deprecated_rule=deprecated_rule,
            deprecated_reason='foo:create_bar is more granular than foo:bar',
            deprecated_since='N'
        )
        policy.DocumentedRuleDefault(
            name='foo:list_bars',
            check_str='role:bazz',
            description='List bars.',
            operations=[{'path': '/v1/bars', 'method': 'GET'}],
            deprecated_rule=deprecated_rule,
            deprecated_reason='foo:list_bars is more granular than foo:bar',
            deprecated_since='N'
        )
        policy.DocumentedRuleDefault(
            name='foo:get_bar',
            check_str='role:bazz',
            description='Get a bar.',
            operations=[{'path': '/v1/bars/{bar_id}', 'method': 'GET'}],
            deprecated_rule=deprecated_rule,
            deprecated_reason='foo:get_bar is more granular than foo:bar',
            deprecated_since='N'
        )
        policy.DocumentedRuleDefault(
            name='foo:update_bar',
            check_str='role:bang',
            description='Update a bar.',
            operations=[{'path': '/v1/bars/{bar_id}', 'method': 'PATCH'}],
            deprecated_rule=deprecated_rule,
            deprecated_reason='foo:update_bar is more granular than foo:bar',
            deprecated_since='N'
        )
        policy.DocumentedRuleDefault(
            name='foo:delete_bar',
            check_str='role:bang',
            description='Delete a bar.',
            operations=[{'path': '/v1/bars/{bar_id}', 'method': 'DELETE'}],
            deprecated_rule=deprecated_rule,
            deprecated_reason='foo:delete_bar is more granular than foo:bar',
            deprecated_since='N'
        )

    .. versionchanged 1.29
       Added *DeprecatedRule* object.
    """

    def __init__(self, name, check_str):
        """Construct a DeprecatedRule object.

        :param name: the policy name
        :param check_str: the value of the policy's check string
        """
        self.name = name
        self.check_str = check_str