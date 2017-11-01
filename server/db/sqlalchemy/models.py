from sqlalchemy import Column, Integer, String, BIGINT
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import orm
from sqlalchemy import ForeignKey, DateTime
from sqlalchemy.types import TypeDecorator


Base = declarative_base()
import six

from sqlalchemy.orm import object_mapper
import timeutils

STATUS_DELETED = 'deleted'


class SoftDeleteInteger(TypeDecorator):


    impl = Integer

    def process_bind_param(self, value, dialect):
        """Return the binding parameter."""
        if value is None:
            return None
        else:
            return int(value)

class ModelBase(six.Iterator):
    """Base class for models."""
    __table_initialized__ = False

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __getitem__(self, key):
        return getattr(self, key)

    def __contains__(self, key):
        # Don't use hasattr() because hasattr() catches any exception, not only
        # AttributeError. We want to passthrough SQLAlchemy exceptions
        # (ex: sqlalchemy.orm.exc.DetachedInstanceError).
        try:
            getattr(self, key)
        except AttributeError:
            return False
        else:
            return True

    def get(self, key, default=None):
        return getattr(self, key, default)

    @property
    def _extra_keys(self):
        """Specifies custom fields
        Subclasses can override this property to return a list
        of custom fields that should be included in their dict
        representation.
        For reference check tests/db/sqlalchemy/test_models.py
        """
        return []

    def __iter__(self):
        columns = list(dict(object_mapper(self).columns).keys())
        # NOTE(russellb): Allow models to specify other keys that can be looked
        # up, beyond the actual db columns.  An example would be the 'name'
        # property for an Instance.
        columns.extend(self._extra_keys)

        return ModelIterator(self, iter(columns))

    def update(self, values):
        """Make the model object behave like a dict."""
        for k, v in six.iteritems(values):
            setattr(self, k, v)

    def _as_dict(self):
        """Make the model object behave like a dict.
        Includes attributes from joins.
        """
        local = dict((key, value) for key, value in self)

        #joined = dict([(k, v) for k, v in six.iteritems(self.__dict__)
        #              if not k[0] == '_'])
        #local.update(joined)
        return local

    def generate_param(self):
        param = dict([(key, value) for key, value in self
                      if key not in ('id', 'deleted',
                                     'deleted_at', 'created_at', 'updated_at')])
        return param
    def iteritems(self):
        """Make the model object behave like a dict."""
        return six.iteritems(self._as_dict())

    def items(self):
        """Make the model object behave like a dict."""
        return self._as_dict().items()

    def keys(self):
        """Make the model object behave like a dict."""
        return [key for key, value in self.iteritems()]


class TimestampMixin(object):
    created_at = Column(Integer, default=lambda: timeutils.utcnow_ts())
    updated_at = Column(Integer, default=lambda: timeutils.utcnow_ts(), onupdate=lambda: timeutils.utcnow_ts())


class SoftDeleteMixin(object):
    deleted_at = Column(Integer, default=0)
    deleted = Column(String(36), default='False')

    def soft_delete(self, session):
        """Mark this object as deleted."""
        self.deleted = STATUS_DELETED
        self.deleted_at = timeutils.utcnow_ts()


class ModelIterator(six.Iterator):

    def __init__(self, model, columns):
        self.model = model
        self.i = columns

    def __iter__(self):
        return self

    # In Python 3, __next__() has replaced next().
    def __next__(self):
        n = six.advance_iterator(self.i)
        return n, getattr(self.model, n)


class BackupBase(ModelBase,
                 TimestampMixin,
                 SoftDeleteMixin):
    metadata = None

    def to_dict(self):
        model_dict = {}
        for k, v in self.items():
            if not issubclass(type(v), BackupBase):
                model_dict[k] = v
        return model_dict


class Policy(Base, BackupBase):
    __tablename__ = 'policy'
    id = Column(String(36), primary_key=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(String(255), nullable=True)
    start_time = Column(Integer)
    interval =Column(Integer, default=0)


    tasks = orm.relationship(
        'Task',
        primaryjoin=(
            'and_('
            'Policy.id == Task.policy_id)'
        ),
        back_populates='policy'
    )


class Role(Base, BackupBase):
    __tablename__ = 'role'
    id = Column(String(36), primary_key=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(String(255), nullable=True)

class Group(Base, BackupBase):
    __tablename__ = 'group'
    id = Column(String(36), primary_key=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(String(255), nullable=True)

    users = orm.relationship(
        'User',
        primaryjoin=(
            'and_('
            'Group.id == User.group_id)'
        ),
        back_populates='group'
    )

class User(Base, BackupBase):
    __tablename__ = 'user'
    id = Column(String(36),primary_key=True, nullable=False)
    name = Column(String(255), nullable=False)
    password = Column(String(255))
    role_id = Column(String(36), ForeignKey('role.id'), nullable=False)
    group_id = Column(String(36), ForeignKey('group.id'), nullable=False)

    tasks = orm.relationship(
        'Task',
        primaryjoin=(
            'and_('
            'User.id == Task.user_id)'
        ),
        back_populates='user'
    )

    group = orm.relationship(
        'Group',
        primaryjoin=(
            'and_('
            'User.group_id == Group.id )'
        ),
        back_populates='users'
    )
class Worker(Base, BackupBase):
    __tablename__ = 'workers'
    id = Column(String(36), primary_key=True, nullable=False)
    ip = Column(String(255), nullable=False)
    port = Column(Integer, nullable=False)
    name = Column(String(255), nullable=True)


    tasks = orm.relationship(
        'Task',
        primaryjoin=(
            'and_('
            'Worker.id == Task.worker_id)'
        ),
        back_populates='worker'
    )


class Task(Base, BackupBase):
    __tablename__ = 'task'
    id = Column(String(36), primary_key=True, nullable=False)
    name = Column(String(255), nullable=True)
    description = Column(String(255), nullable=True)
    user_id = Column(String(36), ForeignKey('user.id'), nullable=False)
    policy_id = Column(String(36), ForeignKey('policy.id'), nullable=False)
    worker_id = Column(String(36), ForeignKey('workers.id'), nullable=False)
    source = Column(String(1024), nullable=False)
    destination = Column(String(1024), nullable=False)
    start_time = Column(Integer, default=0)
    interval = Column(Integer, default=0)
    duration = Column(Integer, default=0)
    script_path = Column(String(4096))
    volume = Column(String(255))

    policy = orm.relationship(
        'Policy',
        lazy='immediate',
        viewonly=True,
        primaryjoin=(
            'and_('
            'Task.policy_id == Policy.id)'
        ),
        back_populates='tasks'
    )

    worker = orm.relationship(
        'Worker',
        lazy='immediate',
        viewonly=True,
        primaryjoin=(
            'and_('
            'Task.worker_id == Worker.id)'
        ),
        back_populates='tasks'
    )

    user = orm.relationship(
        'User',
        lazy='immediate',
        viewonly=True,
        primaryjoin=(
            'and_('
            'Task.user_id == User.id)'
        ),
        back_populates='tasks'
    )

    state = orm.relationship(
        'BackupState',
        primaryjoin=(
            'and_('
            'Task.id == BackupState.task_id)'
        ),
        order_by="desc(BackupState.updated_at)",
        back_populates='task'
    )


class BackupState(Base, BackupBase):
    __tablename__ = 'backupstates'
    id = Column(String(36), primary_key=True, nullable=False)
    task_id = Column(String(36), ForeignKey('task.id'), nullable=False)
    total_size = Column(Integer, default=0)
    current_size = Column(Integer, default=0)
    start_time = Column(Integer, nullable=True, default=0)
    end_time = Column(Integer, nullable=True, default=0)
    state = Column(String(255), nullable=True, default=0)

    task = orm.relationship(
        'Task',
        lazy='immediate',
        viewonly=True,
        primaryjoin=(
            'and_('
            'BackupState.task_id == Task.id)'
        ),
        back_populates='state'
    )


class Volume(Base, BackupBase):
    __tablename__ = 'volume'
    id = Column(String(36), primary_key=True, nullable=False)
    name = Column(String(255), nullable=True)
    description = Column(String(255), nullable=True)

class oplog(Base, BackupBase):
    __tablename__ = 'oplog'
    id = Column(BIGINT, primary_key=True, nullable=False)
    message =  Column(String(2048))