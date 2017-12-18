import os
import sys
from sqlalchemy import MetaData
from sqlalchemy import or_
from sqlalchemy.orm import joinedload, contains_eager, outerjoin
from sqlalchemy.sql.expression import true
from sqlalchemy.sql import func
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import and_
from sqlalchemy import exc
import models

from cherrypy import NotFound
from cherrypy import HTTPError
from models import Base
import uuidutils
import copy
sys.path.append('../../')

from auth import auth_basic

def model_query(session, model):
    return session.query(model)

from config import SUPERROLE
import logging
logger = logging.getLogger('backup')
from pattern import Singleton
import six
from backup_exception import Duplicated

@six.add_metaclass(Singleton)
class Database(object):
    def __init__(self, conf):
        autocommit = True
        type, path = self.init(conf)
        self.db_path = path
        self.type = type
        self.engine = create_engine(path)
        Base.metadata.bind = self.engine
        self.DBSession = sessionmaker(bind=self.engine, autocommit=autocommit,)
        self.create()
        self.api = API(self)

    def init(self, conf):
        driver = None
        path = None
        database_conf = {}
        if isinstance(conf.get('database'), dict):
            database_conf = conf['database']
            logger.info('database config %s' % database_conf)
        else:
            database_conf = conf
        driver = database_conf.get('driver', 'sqlite')
        if driver == 'sqlite':
            path = database_conf.get('path', '/var/backup/backup.db')
            path = 'sqlite:///%s' % path
            db = Database(driver, path)
        elif driver == 'mysql' or driver == 'mariadb':
            user = database_conf.get('user')
            password = database_conf.get('password')
            host = database_conf.get('host')
            port = database_conf.get('port', 3306)
            database = database_conf.get('database')
            if user and password and host and port and database:
                if database_conf.get('create'):
                    url = 'mysql+mysqldb://{0}:{1}@{2}:{3}'. \
                        format(user, password, host, port)
                    engine = create_engine(url)
                    engine.connect()
                    engine.execute("CREATE DATABASE IF NOT EXISTS {0} CHARSET=utf8".format(database))
                    engine.execute("USE {0}".format(database))
                    Base.metadata.create_all(engine)

                path = 'mysql+mysqldb://{0}:{1}@{2}:{3}/{4}?charset=utf8'. \
                    format(user, password, host, port, database)

        else:
            logger.error('database type is not supported , should be sqlite or mysql')
            raise TypeError()
        return driver, path


    def get_session(self):
        return self.DBSession()

    def __getattr__(self, item):
        try:
            meth = getattr(self.api, item)
            return meth
        except AttributeError:
            raise

    @staticmethod
    def sort(model, query, sort_key, sort_dir):
        '''

        :param model:
        :param query:
        :param sort_key:
        :param sort_dir: desc or asc
        :return:
        '''
        if sort_dir.lower() not in ('desc', 'asc'):
            return
        sort_attr = getattr(model, sort_key)
        sort_method = getattr(sort_attr, sort_dir.lower())
        return query.order_by(sort_method())

    def create(self, force=False):
        if self.type == 'sqlite':
            if not os.path.exists(self.db_path) or force:
                Base.metadata.create_all(self.engine)

    def add(self, session, obj):
        session.add(obj)
        self.flush(session)

    def commit(self, session):
        session.commit()

    def flush(self, session):
        session.flush(session)

    def soft_delete(self, session, obj):
        obj.soft_delete(session)
        self.flush(session)

    def delete(self, session, obj):
        obj.delete(synchronize_session=False)
        self.flush(session)

    def get_type(self):
        return self.type


class API(object):
    def __init__(self, db):
        self.db = db
        self.filter = ('deleted', 'deleted_at','created_at', 'updated_at')

    def get_model_by_id(self, session, model, id):
        '''
        :param model:
        :param id:
        :return:
        '''
        query = model_query(session, model)
        query = query.filter(model.id == id)
        result = query.first()
        if not result:
            raise NotFound()
        return result

    def get_tasks(self, context, detail=False, **kwargs):
        '''

        :param detail:
        :param kwargs:
        :return:
        '''
        session = self.db.get_session()
        logger.info('get all tasks , params: %s'%kwargs)
        type = kwargs.get('type', 'backup')
        limit = kwargs.get('limit')
        offset = kwargs.get('offset')
        sort_key = kwargs.get('sort_key', 'created_at')
        sort_dir = kwargs.get('sort_dir', 'desc')
        worker_id = kwargs.get('worker_id')
        worker_name = kwargs.get('worker_name')
        task_name = kwargs.get('name')
        policy_id = kwargs.get('policy_id')
        policy_name = kwargs.get('policy_name')
        worker_ip = kwargs.get('worker_ip')
        task_id = kwargs.get('task_id')
        name_like = kwargs.get('name_like')
        group_id = kwargs.get('group_id')
        deleted = True
        query = model_query(session, models.Task)

        if detail:
            query = query.options(
                joinedload(models.Task.policy),
                joinedload(models.Task.worker),
                joinedload(models.Task.states),
                joinedload(models.Task.user)
            )

        query = query.filter(models.Task.type == type)

        if not context['is_superuser']:
            query = query.filter(models.Task.group_id == context.get('group_id'))
        elif group_id:
            query = query.filter(models.Task.group_id == group_id)

        if not context.get('is_admin') and not context['is_superuser']:
            query = query.filter(models.Task.user_id == context.get('user_id'))

        if 'deleted' not in kwargs:
            deleted = False
            query = query.filter(models.Task.deleted == 'False')

        if worker_name:
            w = self.get_worker_by_name(context,  worker_name, session, deleted)
            worker_id = w.id

        if worker_ip:
            w = self.get_worker_by_ip(context, worker_ip, session, deleted)
            worker_id = w.id

        if policy_name:
            p = self.get_policy_by_name(context,  policy_name, session, deleted)
            policy_id = p.id

        if worker_id :
            query = query.filter(models.Task.worker_id == worker_id)
        if policy_id:
            query = query.filter(models.Task.policy_id == policy_id)
        if task_name:
            query = query.filter(models.Task.name == task_name)
        if task_id:
            query = query.filter(models.Task.id == task_id)
        if name_like:
            like_str = '%{0}%'.format(name_like)
            query = query.filter(models.Task.name.like(like_str))

        query = Database.sort(models.Task, query, sort_key, sort_dir)
        total = query.count()
        if limit:
            query = query.limit(limit)
        if offset:
            query = query.offset(offset)
        return query.all(), total

    def get_tasks_all(self, context, **kwargs):
        return self.get_tasks(context, True, **kwargs)

    def task_list_by_ids(self, context, ids, session=None):
        if not session:
            session = self.db.get_session()
        query = model_query(session, models.Task)
        query = query.filter(models.Task.id.in_(ids))
        return query.all

    def _get_task(self, session=None, **kwargs):
        if not session:
            session = self.db.get_session()
        id = kwargs.get('id')
        name = kwargs.get('name')
        query = model_query(session, models.Task)
        group_id = kwargs.get('group_id')
        user_id = kwargs.get('user_id')

        if group_id != None:
            query = query.filter(models.Task.group_id == group_id)

        if user_id:
            query = query.filter(models.Task.user_id == user_id)

        if kwargs.get('detail') == True:
            query = query.options(
                joinedload(models.Task.policy),
                joinedload(models.Task.worker),
                joinedload(models.Task.states),
            )
        if id:
            query = query.filter(models.Task.id == id)
        if name:
            query = query.filter(models.Task.name == name)

        if not kwargs.get('deleted'):
            query = query.filter(models.Task.deleted == 'False')

        task = query.first()
        return task

    def get_task(self, context, id, detail=True, deleted=False,
                 group_id=None, user_id=None, session=None):
        logger.info('trying to get a task , id = %s'%id)
        if not context.get('is_superuser'):
            group_id = context.get('group_id')

        task = self._get_task(session, id=id, detail=detail,
                              group_id=group_id, user_id=user_id,
                              deleted=deleted)
        if not task:
            logger.error('task not found, %s' % id)
            raise NotFound()
        return task

    def task_get_by_name(self, context, name, group_id=None,
                         user_id=None, session=None):
        logger.info('trying to get a task , id = %s' % name)
        if not context.get('is_superuser'):
            group_id = context.get('group_id')
        else:
            group_id = group_id

        task = self._get_task(session, name=name, group_id=group_id)
        if not task:
            logger.error('task %s not found' % name)
            raise NotFound()
        return task

    def create_task(self, context, task_values):
        logger.info('create task : %s' % task_values)
        session = self.db.get_session()
        values = copy.deepcopy(task_values)
        values['id'] = uuidutils.generate_uuid()
        values['user_id'] = context.get('user_id')
        if not context.get('is_superuser'):
            values['group_id'] = context.get('group_id')
        task = models.Task()
        params = task.generate_param(self.filter)
        for k, v in params.items():
            params[k] = values.get(k, params[k])
        task.update(params)
        self.db.add(session, task)
        return self._get_task(session, id=params['id'])

    def update_task(self, context, task_values, session=None):
        logger.info('update task : %s '%task_values)
        if not session:
            session = self.db.get_session()
        if context.get('is_superuser'):
            group_id = context.get('group_id')
        values = copy.deepcopy(task_values)
        id = task_values.get('id')
        task = self._get_task(session, id=id)
        if not task:
            raise NotFound('task %s is not found ' % id)
        name = task_values.get('name')
        if name and task.name != name:
            try:
                self.db.task_get_by_name(context, name, session=session)
                raise Duplicated()
            except NotFound:
                pass
        filter = ('id', 'deleted', 'deleted_at','created_at', 'updated_at')
        params = task.generate_param(filter)
        for k, v in params.items():
            params[k] = values.get(k, params[k])
        task.update(params)
        self.db.flush(session)
        return self._get_task(session, id=id)

    def delete_task(self, context, task_id, session=None):
        if not session:
            session = self.db.get_session()
        task = self.get_task(context, task_id, False, session=session)
        if not context.get('is_admin') and not context['is_superuser']:
            user = context.get('user_id')
            if user != task.user_id:
                raise HTTPError(403, 'not permitted')
        task_dict = task.to_dict()
        self.db.soft_delete(session, task)
        return task_dict

    def get_policies(self, context, detail=False, session=None, **kwargs):
        if not session:
            session = self.db.get_session()
        logger.info('list policies : %s '%kwargs)
        limit = kwargs.get('limit', 0)
        offset = kwargs.get('offset', 0)
        sort_key = kwargs.get('sort_key', 'created_at')
        sort_dir = kwargs.get('sort_dir', 'desc')
        group_id = kwargs.get('group_id')
        name_like = kwargs.get('name_like')
        query = model_query(session, models.Policy)
        if detail:
            query = query.options(
                joinedload(models.Policy.user)
            )
        query = Database.sort(models.Policy, query, sort_key, sort_dir)
        name = kwargs.get('name', 'unkown')
        if name != 'unkown':
            query = query.filter(models.Policy.name == name)
        if 'deleted' not in kwargs:
            query = query.filter(models.Policy.deleted == 'False')

        if name_like:
            like_str = '%{0}%'.format(name_like)
            query = query.filter(models.Policy.name.like(like_str))

        if not context['is_superuser']:
            query = query.filter(models.Policy.group_id == context.get('group_id'))
        elif group_id:
            query = query.filter(models.Policy.group_id == group_id)

        total = query.count()
        if limit:
            query = query.limit(limit)
        if offset:
            query = query.offset(offset)
        return query.all(), total

    def _get_policy(self,  session=None, **kwargs):
        if not session:
            session = self.db.get_session()
        query = model_query(session, models.Policy)
        id = kwargs.get('id')
        name = kwargs.get('name')
        group_id = kwargs.get('group_id')
        if name:
            query = query.filter(models.Policy.name == name)
        if id:
            query = query.filter(models.Policy.id == id)
        if group_id:
            query = query.filter(models.Policy.group_id == group_id)

        if 'with_user' in kwargs:
            query = query.options(joinedload(models.Policy.user))

        if kwargs.get('with_tasks') and kwargs.get('deleted'):
            query = query.outerjoin(
                models.Task, and_(models.Task.policy_id == models.Policy.id)).\
                    options(contains_eager(models.Policy.tasks))
        elif kwargs.get('with_tasks'):
            query = query.options(joinedload(models.Policy.tasks))

        if not kwargs.get('deleted'):
            query = query.filter(models.Policy.deleted == 'False')

        policy = query.first()

        return policy


    def get_policy(self, context, id, session=None, with_tasks=False, group_id=None):
        logger.info('trying to get a policy %s'%id)
        policy = self._get_policy(session, id=id, with_user=True,
                                  with_tasks=with_tasks, group_id=group_id)
        if not policy:
            logger.error('policy not found, %s'%id)
            raise NotFound()
        return policy

    def get_policy_by_name(self, context,  name, group_id=None, session=None, deleted=False):
        if not context['is_superuser']:
            group_id = context['group_id']
        else:
            group_id = group_id if group_id else 'supergroup'
        policy = self._get_policy(session, name=name, group_id=group_id, deleted=deleted )
        if not policy:
            raise NotFound('policy %s is not found ' % name)
        return policy

    def create_policy(self, context, policy_values):
        logger.info('create policy : %s ' % policy_values)
        session = self.db.get_session()
        values = copy.deepcopy(policy_values)
        values['id'] = uuidutils.generate_uuid()
        values['user_id'] = context.get('user_id')
        if not context.get('is_superuser'):
            values['group_id'] = context.get('group_id')

        policy = models.Policy()
        params = policy.generate_param(self.filter)
        for k, v in params.items():
            params[k] = values.get(k, params[k])
        policy.update(params)
        self.db.add(session, policy)
        return self._get_policy(session, id=values['id'])

    def update_policy(self, context, policy_values):
        session = self.db.get_session()
        values = copy.deepcopy(policy_values)
        id = values['id']
        name = policy_values.get('name')
        policy = self._get_policy(session, id=id)
        if not policy:
            raise NotFound('policy %s is not found ' % id)
        if name and policy.name != name:
            try:
                self.get_policy_by_name(context, name, session=session)
                raise Duplicated()
            except NotFound:
                pass
        filter = ('id', 'deleted', 'deleted_at','created_at', 'updated_at')
        params = policy.generate_param(filter)
        logger.debug('update policy_values : %s ' % params)
        for k, v in params.items():
            if values.get(k):
                params[k] = values.get(k)
            else:
                continue
        policy.update(params)
        self.db.flush(session)
        return self._get_policy(session, id=id)

    def delete_policy(self, context, id):
        session = self.db.get_session()
        policy = self.get_policy(context, id, session, with_tasks=True)
        tasks = policy.tasks
        if not tasks:
            old = policy.to_dict()
            self.db.soft_delete(session, policy)
            return None, old
        else:
            return tasks, policy.to_dict()

    def get_workers(self, context, detail=False, **kwargs):
        session = self.db.get_session()
        logger.info('list workers : %s '%kwargs)
        limit = kwargs.get('limit', 0)
        offset = kwargs.get('offset', 0)
        sort_key = kwargs.get('sort_key', 'created_at')
        sort_dir = kwargs.get('sort_dir', 'desc')
        name = kwargs.get('name', 'unkown')
        name_like = kwargs.get('name_like')
        group_id = kwargs.get('group_id')
        query = model_query(session, models.Worker)

        query = Database.sort(models.Worker, query, sort_key, sort_dir)
        if 'deleted' not in kwargs:
            query = query.filter(models.Worker.deleted == 'False')

        if not context['is_superuser']:
            query = query.filter(models.Worker.group_id == context.get('group_id'))
        elif group_id:
            query = query.filter(models.Worker.group_id == group_id)


        if name_like:
            like_str = '%{0}%'.format(name_like)
            query = query.filter(models.Worker.name.like(like_str))

        total = query.count()
        if limit:
            query = query.limit(limit)
        if offset:
            query = query.offset(offset)
        if name != 'unkown':
            query = query.filter(models.Worker.name == name)
        return query.all(), total


    def _get_worker(self, session=None, **kwargs):
        if not session:
            session = self.db.get_session()

        id = kwargs.get('id')
        name = kwargs.get('name')
        ip = kwargs.get('ip')
        group_id = kwargs.get('group_id')
        group_name = kwargs.get('group_name')
        query = model_query(session, models.Worker)
        if id:
            query = query.filter(models.Worker.id == id)
        if name:
            query = query.filter(models.Worker.name == name)
        if ip:
            query = query.filter(models.Worker.ip == ip)
        if group_id:
            query = query.filter(models.Worker.group_id == group_id)
        if group_name:
            query = query.filter(models.Worker.owner == group_name)

        if kwargs.get('with_tasks') and kwargs.get('deleted'):
            query = query.outerjoin(
                models.Task, and_(models.Task.worker_id == models.Worker.id)).\
                options(contains_eager(models.Worker.tasks)
            )
        elif kwargs.get('with_tasks'):
            query = query.options(joinedload(models.Worker.tasks))

        if not kwargs.get('deleted'):
            query = query.filter(models.Worker.deleted == 'False')

        worker = query.first()
        return worker

    def get_worker(self, context, id, with_tasks=True, session=None):
        logger.info('trying to get a worker id=%s'%id)
        worker = self._get_worker(session, id=id,  with_tasks=with_tasks)
        if not worker:
            logger.error('worker not found %s'%id)
            raise NotFound()
        return worker


    def get_worker_by_name(self, context ,worker_name,
                           group_id=None, group_name=None,
                           session=None, deleted=False):
        if not context['is_superuser']:
            group_id = context['group_id']
        else:
            group_id = group_id if group_id else 'supergroup'
        worker = self._get_worker(session, name=worker_name,
                                  group_id=group_id,
                                  group_name=group_name,
                                  deleted=deleted)
        if not worker:
            raise NotFound('worker %s is not found' % worker_name)
        return worker

    def get_worker_by_ip(self, context ,ip, session=None, deleted=False):
        worker = self._get_worker(session, ip=ip, deleted=deleted)
        if not worker:
            raise NotFound()
        return worker

    def create_worker(self, context,  worker_values):
        logger.info('create a worker : %s' % worker_values)
        session = self.db.get_session()
        values = copy.deepcopy(worker_values)
        values['id'] = uuidutils.generate_uuid()
        values['owner'] = worker_values.get('group_name') if \
            worker_values.get('group_name') \
            else context.get('group_name')
        if context.get('group_id'):
            values['group_id'] = context.get('group_id')
        worker = models.Worker()
        params = worker.generate_param(self.filter)
        for k, v in params.items():
            params[k] = values.get(k, params[k])
        worker.update(params)
        self.db.add(session, worker)
        return self._get_worker(session, id=values['id'])


    def update_worker(self, context, worker_values):
        session = self.db.get_session()
        values = copy.deepcopy(worker_values)
        id = values['id']
        worker = self._get_worker(session, id=id)
        name = values.get('name')
        if not worker:
            raise NotFound('worker %s is not found ' % id)
        if name and name != worker.name:
            try:
                self.get_worker_by_name(context, name, session=session)
                raise Duplicated
            except NotFound:
                pass
        filter = ('start_at', 'deleted', 'deleted_at','created_at', 'updated_at')
        params = worker.generate_param(filter)
        for k, v in params.items():
            if values.get(k):
                params[k] = values.get(k)
            else:
                continue

        worker.update(params)
        self.db.flush(session)
        return self._get_worker(session, id=id)

    def delete_worker(self, context, id):
        logger.info('deleting a worker , id = %s'%id)
        session = self.db.get_session()
        worker = self._get_worker(session, id=id)
        tasks = worker.tasks
        if not tasks:
            old = worker.to_dict()
            self.db.soft_delete(session, worker)
            return None, old
        else:
            return tasks, worker.to_dict()

    def get_users(self, context, **kwargs):
        session = self.db.get_session()
        limit = kwargs.get('limit', 0)
        offset = kwargs.get('offset', 0)
        sort_key = kwargs.get('sort_key', 'created_at')
        sort_dir = kwargs.get('sort_dir', 'desc')
        name = kwargs.get('name')
        name_like = kwargs.get('name_like')
        query = model_query(session, models.User)
        query = query.options(joinedload(models.User.role))
        query = query.options(joinedload(models.User.group))
        query = Database.sort(models.User, query, sort_key, sort_dir)
        if name:
            query = query.filter(models.User.name == name)
        if 'deleted' not in kwargs:
            query = query.filter(models.User.deleted == 'False')
        if not context['is_superuser']:
            query = query.filter(models.User.group_id == context.get('group_id'))

        if name_like:
            like_str = '%{0}%'.format(name_like)
            query = query.filter(models.User.name.like(like_str))

        total = query.count()
        if limit:
            query = query.limit(limit)

        if offset:
            query = query.offset(offset)

        return query.all(),  total

    def _get_user(self, session=None, **kwargs):
        if not session:
            session = self.db.get_session()
        query = model_query(session, models.User)
        id = kwargs.get('id')
        name = kwargs.get('name')
        role_id = kwargs.get('role_id')
        group_id = kwargs.get('group_id')
        if name:
            query = query.filter(models.User.name == name)
        if id:
            query = query.filter(models.User.id == id)
        if role_id:
            query = query.filter(models.User.role_id == role_id)
        if group_id:
            query = query.filter(models.User.group_id == group_id)

        if 'with_role' in kwargs:
            query = query.options(joinedload(models.User.role))
        if 'with_group' in kwargs:
            query = query.options(joinedload(models.User.group))
        if kwargs.get('with_tasks') and kwargs.get('deleted'):
            query = query.outerjoin(
                models.Task, and_(models.Task.user_id == models.User.id)).\
                options(contains_eager(models.User.tasks))
        elif kwargs.get('with_tasks'):
            query = query.options(joinedload(models.User.tasks))

        if not kwargs.get('deleted'):
            query = query.filter(models.User.deleted == 'False')

        user = query.first()
        return user

    def get_user(self, context, id, session=None, **kwargs):
        user = self._get_user( session, id=id, with_role=True, with_group=True, **kwargs)
        if not user:
            logger.error('user not found, %s'%kwargs)
            raise HTTPError(404, 'user : {0} is not found '.format(id))
        return user

    def get_user_by_name(self, context, username, with_role=True, with_group=False, session=None):
        if not context['is_superuser']:
            group_id = context['group_id']
        else:
            group_id = None
        user = self._get_user(session, name=username, group_id=group_id, with_role=with_role, with_group=with_group)
        if not user:
            logger.error('user not found, %s' % username)
            raise HTTPError(404, 'user : {0} is not found '.format(username))
        return user

    def get_super_user(self, context,  superrole_id, session=None):
        user = self._get_user(role_id=superrole_id)
        return user

    def create_user(self, context, user_values, session=None):
        if not session:
            session = self.db.get_session()
        values = copy.deepcopy(user_values)
        values['id'] = uuidutils.generate_uuid()
        values['key'] = uuidutils.generate_uuid(False)
        if not values.get('group_id') or not context.get('is_superuser'):
            values['group_id'] = context.get('group_id')
        name = values.get('name')
        password = values.get('password')
        digest = auth_basic.calculate_digest(name, password, values['key'])
        values['password'] = digest
        user = models.User()
        filter = ('deleted', 'deleted_at','created_at', 'updated_at', 'login_time')
        params = user.generate_param(filter)
        for k, v in params.items():
            params[k] = values.get(k)
            user.update(params)
        self.db.add(session, user)
        return self._get_user(session, id=values['id'])

    def update_user(self, context, user_values):
        logger.debug('user values %s '%user_values)
        session = self.db.get_session()
        values = copy.deepcopy(user_values)
        id = values['id']
        name = values.get('name')
        user = self._get_user(session, id=id)
        if not user:
            raise NotFound('user %s is not found' % id)
        if name and name != user.name:
            raise HTTPError(403, " user name can not be changed")
        filter = ('id', 'deleted', 'deleted_at','created_at', 'updated_at', 'login_time')
        params = user.generate_param(filter)
        password = user_values.get('password')
        if password:
            values['key'] = uuidutils.generate_uuid(False)
            digest = auth_basic.calculate_digest(user.name, password, values['key'])
            values['password'] = digest
        for k, v in params.items():
            if values.get(k):
                params[k] = values.get(k)
        user.update(params)
        self.db.flush(session)
        return self._get_user(session, id=id)


    def delete_user(self, context, id, session=None):
        if context.get('user_id') == id:
            raise HTTPError(403, 'You can not delete your self')
        if not session:
            session = self.db.get_session()
        user = self._get_user(session, id=id)
        if user:
            user_dict = user.to_dict()
            self.db.soft_delete(session, user)
            return user_dict
        else:
            return None


    def bk_create(self, context, bk_values):
        '''
        :param bk_values:
        :return:
        '''
        logger.info('create a state : %s'%bk_values)
        session = self.db.get_session()
        values = copy.deepcopy(bk_values)
        logger.info('state info: %s'%values)
        task_id = values.get('task_id')
        if not task_id:
            logger.error('task_id is empty')
            raise HTTPError(400, 'task_id is empty')
        else:
            try:
                self.get_task(context, task_id, session=session)
            except NotFound:
                logger.error('task is not found')
                raise HTTPError(404, 'task %s is not found'%task_id)

        if not values.get('id'):
            values['id'] = uuidutils.generate_uuid()

        state = models.BackupState()
        params = state.generate_param(self.filter)
        for k, v in params.items():
            params[k] = values.get(k)
            state.update(params)
        self.db.add(session, state)
        return self._bk_get(session, id=values['id'])


    def _bk_get(self, session=None, **kwargs):
        if not session:
            session = self.db.get_session()
        query = model_query(session, models.BackupState)
        id = kwargs.get('id')
        query = query.filter(models.BackupState.id == id)
        if kwargs.get('detail'):
            query = query.options(
                joinedload(models.BackupState.task)
            )
        if 'deleted' not in kwargs:
            query = query.filter(models.BackupState.deleted == 'False')
        state = query.first()
        return state

    def get_bk_state(self, context, id, detail=False, session=None):
        state = self._bk_get(session, detail=detail, id=id)
        if not state:
            logger.error('state not found for id %s'%id)
            raise NotFound('state not found for id %s'%id)
        return state

    def bk_update(self, context, bk_values, session=None):
        if not session:
            session = self.db.get_session()
        values = copy.deepcopy(bk_values)
        id = values['id']
        state = self._bk_get(session, id=id)
        params = state.generate_param(self.filter)
        for k, v in params.items():
            params[k] = values.get(k, params[k])
        state.update(params)
        self.db.flush(session)
        return self._bk_get(session, id=id)

    def bk_delete(self, context, id, session=None):
        if not session:
            session = self.db.get_session()
        state = self._bk_get(session, id=id)
        old = state.to_dict()
        self.db.soft_delete(session, state)
        return old

    def bk_list(self, context, detail=False, **kwargs):
        '''
        :param detail:
        :param kwargs:
        :return:
        '''
        session = self.db.get_session()
        logger.info('list states %s'%kwargs)
        limit = kwargs.get('limit', 0)
        offset = kwargs.get('offset', 0)
        sort_key = kwargs.get('sort_key', 'updated_at')
        sort_dir = kwargs.get('sort_dir', 'desc')
        task_name = kwargs.get('task_name')
        task_id = kwargs.get('task_id')
        query = model_query(session, models.BackupState)
        if detail:
            query.options(
                joinedload(models.BackupState.task)
            )
        if 'deleted' not in kwargs:
            query = query.filter(models.BackupState.deleted == 'False')
        if task_name:
            try:
                t = self.task_get_by_name(context, name=task_name, session=session)
                task_id = t.id
            except NotFound:
                logger.error('task %s is not found'%task_name)
                raise HTTPError(404, 'task %s is not found'%task_name)
        if task_id:
            query = query.filter(models.BackupState.task_id == task_id)
        total = query.count()
        query = Database.sort(models.BackupState, query, sort_key, sort_dir)
        if limit:
            query = query.limit(limit)
        if offset:
            query = query.offset(offset)
        return query.all(), total


    def _role_get(self, session=None, **kwargs):
        if not session:
            session = self.db.get_session()
        role_id = kwargs.get('id')
        role_name = kwargs.get('name')
        query = model_query(session, models.Role)
        if role_id:
            query = query.filter(models.Role.id == role_id)

        if role_name:
            query = query.filter(models.Role.name == role_name)

        if kwargs.get('with_users') and kwargs.get('deleted'):
            query = query.outerjoin(
                models.Task, and_(models.User.role_id == models.Role.id)).\
                    options(contains_eager(models.Role.users))

        elif kwargs.get('with_users'):
            query = query.options(
                joinedload(models.Role.users)
            )

        if not kwargs.get('deleted'):
            query = query.filter(models.Role.deleted == 'False')

        role = query.first()
        return role

    def role_get(self, context, id , session=None):
        role = self._role_get(session, id=id, with_users=True)
        if not role:
            logger.error('role not found, %s'%id)
            raise HTTPError(404, 'role  {0} is not found '.format(id))
        return role

    def role_get_by_name(self, context, name, session=None):
        role = self._role_get(session, name=name)
        if not role:
            logger.error('role not found, %s'%id)
            raise HTTPError(404, 'role  {0} is not found '.format(name))
        return role

    def role_create(self, context, role_values, session=None):
        if not session:
            session = self.db.get_session()
        values = copy.deepcopy(role_values)
        values['id'] = uuidutils.generate_uuid()
        role = models.Role()
        params = role.generate_param(self.filter)
        for k, v in params.items():
            params[k] = values.get(k)
            role.update(params)
        self.db.add(session, role)
        return self._role_get(session, id=values['id'])

    def role_list(self, context, **kwargs):
        session = self.db.get_session()
        limit = kwargs.get('limit', 0)
        offset = kwargs.get('offset', 0)
        sort_key = kwargs.get('sort_key', 'created_at')
        sort_dir = kwargs.get('sort_dir', 'desc')
        name = kwargs.get('name')
        query = model_query(session, models.Role)
        query = Database.sort(models.Role, query, sort_key, sort_dir)
        if name:
            query = query.filter(models.Role.name == name)
        if 'deleted' not in kwargs:
            query = query.filter(models.Role.deleted == 'False')
        query = query.filter(models.Role.name != SUPERROLE)
        total = query.count()
        if limit:
            query = query.limit(limit)
        if offset:
            query = query.offset(offset)
        return query.all(),  total

    def role_update(self, context, role_values):
        session = self.db.get_session()
        values = copy.deepcopy(role_values)
        id = values['id']
        try:
            role = self._role_get(session, id=id)
        except:
            raise
        params = role.generate_param(self.filter)
        for k, v in params.items():
            params[k] = values.get(k, params[k])
            role.update(params)
        self.db.flush(session)
        return self._role_get(session, id=id)

    def role_delete(self, context, role_id, session=None):
        if not session:
            session = self.db.get_session()
        role = self._role_get(session, id=role_id)
        self.db.soft_delete(session, role)

    def group_list(self, context, detail=False, session=None, **kwargs):
        if not session:
            session = self.db.get_session()
        limit = kwargs.get('limit', 0)
        offset = kwargs.get('offset', 0)
        sort_key = kwargs.get('sort_key', 'created_at')
        sort_dir = kwargs.get('sort_dir', 'desc')
        name = kwargs.get('name')
        query = model_query(session, models.Group)
        query = Database.sort(models.Group, query, sort_key, sort_dir)
        if detail:
            query = query.options(
                joinedload(models.Group.users)
            )
        if name:
            query = query.filter(models.Group.name == name)
        if 'deleted' not in kwargs:
            query = query.filter(models.Group.deleted == 'False')
        total = query.count()
        if limit:
            query = query.limit(limit)
        if offset:
            query = query.offset(offset)
        return query.all(),  total

    def group_create(self, context, group_values, session=None):
        if not session:
            session = self.db.get_session()
        values = copy.deepcopy(group_values)
        values['id'] = uuidutils.generate_uuid()
        group = models.Group()
        params = group.generate_param(self.filter)
        for k, v in params.items():
            params[k] = values.get(k, params[k])
            group.update(params)
        self.db.add(session, group)
        return self.group_get(session, id=values['id'])

    def _group_get(self, session=None, **kwargs):
        if not session:
            session = self.db.get_session()
        query = model_query(session, models.Group)
        id = kwargs.get('id')
        name = kwargs.get('name')
        if id:
            query = query.filter(models.Group.id == id)

        if name:
            query = query.filter(models.Group.name == name)

        if kwargs.get('with_users') and kwargs.get('deleted'):
            query = query.outerjoin(
                models.Task, and_(models.User.group_id == models.Group.id)).\
                    options(contains_eager(models.Group.users))

        elif kwargs.get('with_users'):
            query = query.options(
                joinedload(models.Group.users)
            )

        if not kwargs.get('deleted'):
            query = query.filter(models.Group.deleted == 'False')

        group = query.first()
        return group

    def group_get(self, context, id, session=None):
        group = self._group_get(session, id=id, with_users=True)
        if not group:
            logger.error('group not found, %s' % id)
            raise HTTPError(404, 'group  {0} is not found '.format(id))
        return group

    def group_get_by_name(self, context, name, session=None):
        group = self._group_get(session, name=name)
        if not group:
            logger.error('group not found, %s' % id)
            raise HTTPError(404, 'group  {0} is not found '.format(id))
        return group

    def group_update(self, context, group_values):
        session = self.db.get_session()
        values = copy.deepcopy(group_values)
        id = values['id']
        name = values.get('name')
        group = self._group_get(session, id=id)
        if not group:
            raise NotFound('group  %s is not found ' % id)
        elif name and name != group.name:
            try:
                self.group_get_by_name(context, name)
                raise Duplicated()
            except NotFound:
                pass
        params = group.generate_param(self.filter)
        for k, v in params.items():
            params[k] = values.get(k, params[k])
            group.update(params)
        self.db.flush(session)
        return self._group_get(session, id=id)

    def group_delete(self, context, group_id, session=None):
        if not session:
            session = self.db.get_session()
        group = self._group_get(session, id=group_id, with_users=True)
        if group.users:
            raise HTTPError(403, 'there are users in group, delete them first')
        old = group.to_dict()
        self.db.soft_delete(session, group)
        return old


    def volume_list(self, context, detail=False, session=None, **kwargs):
        if not session:
            session = self.db.get_session()
        limit = kwargs.get('limit', 0)
        offset = kwargs.get('offset', 0)
        sort_key = kwargs.get('sort_key', 'created_at')
        sort_dir = kwargs.get('sort_dir', 'desc')
        name = kwargs.get('name')
        query = model_query(session, models.Volume)
        query = Database.sort(models.Volume, query, sort_key, sort_dir)
        if detail:
            query = query.options(
                joinedload(models.Volume.user)
            )
        if name:
            query = query.filter(models.Volume.name == name)
        if 'deleted' not in kwargs:
            query = query.filter(models.Volume.deleted == 'False')
        total = query.count()
        if limit:
            query = query.limit(limit)
        if offset:
            query = query.offset(offset)
        return query.all(),  total


    def _volume_get(self, session=None, **kwargs):
        if not session:
            session = self.db.get_session()
        query = model_query(session, models.Volume)
        id = kwargs.get('id')
        name = kwargs.get('name')

        if id:
            query = query.filter(models.Volume.id == id)
        if name:
            query = query.filter(models.Volume.name == name)

        if kwargs.get('with_users'):
            query = query.options(
                joinedload(models.Volume.user)
            )
        if 'deleted' not in kwargs:
            query = query.filter(models.Volume.deleted == 'False')


        volume = query.first()
        return volume

    def volume_get(self, context, id, session=None):
        volume = self._volume_get(session, id=id, with_users=True)
        if not volume:
            logger.error('volume not found, %s' % id)
            raise HTTPError(404, 'volume  {0} is not found '.format(id))
        return volume

    def volume_get_by_name(self, context, name, session=None):
        volume = self._volume_get(session, name=name)
        if not volume:
            logger.error('volume not found, %s' % id)
            raise NotFound('volume  {0} is not found '.format(id))
        return volume

    def volume_create(self, context, volume_values):
        logger.info('create volume : %s'%volume_values)
        session = self.db.get_session()
        values = copy.deepcopy(volume_values)
        values['id'] = uuidutils.generate_uuid()
        values['owner'] = context.get('user_id')
        volume = models.Volume()
        params = volume.generate_param(self.filter)
        for k, v in params.items():
            params[k] = values.get(k, params[k])
        logger.debug('volume params : %s ' % params)
        volume.update(params)
        self.db.add(session, volume)
        return self._volume_get(session, id=params['id'])

    def volume_update(self, context, volume_values):
        session = self.db.get_session()
        values = copy.deepcopy(volume_values)
        id = values['id']
        name = values.get('name')
        volume = self._volume_get(session, id=id)
        if not volume:
            raise NotFound('volume %s is not found ' % id)
        elif name and name != volume.name:
            try:
                self.volume_get_by_name(context, name)
                raise Duplicated()
            except NotFound:
                pass
        filter = ('id', 'deleted', 'deleted_at', 'created_at', 'updated_at', 'login_time')
        params = volume.generate_param(filter)
        for k, v in params.items():
            params[k] = values.get(k, params[k])
        volume.update(params)
        self.db.flush(session)
        return self._volume_get(session, id=id)

    def volume_delete(self, context, id, session=None):
        if not session:
            session = self.db.get_session()
        volume = self._volume_get(session, id=id)
        old = volume.to_dict()
        self.db.soft_delete(session, volume)
        return old

    def oplog_list(self, context, session=None, **kwargs):
        if not session:
            session = self.db.get_session()
        limit = kwargs.get('limit', 0)
        offset = kwargs.get('offset', 0)
        sort_key = kwargs.get('sort_key', 'created_at')
        sort_dir = kwargs.get('sort_dir', 'desc')

        username = kwargs.get('username')
        user_id = kwargs.get('user_id')

        time_start = kwargs.get('time_start')
        time_end = kwargs.get('time_end')

        query = model_query(session, models.OpLog)
        query = Database.sort(models.OpLog, query, sort_key, sort_dir)
        if not context['is_superuser']:
            query = query.filter(models.OpLog.group_id == context.get('group_id'))

        if username:
            query = query.filter(models.OpLog.username == username)

        if user_id:
            query = query.filter(models.OpLog.user_id == user_id)

        if time_start:
            query = query.filter(models.OpLog.created_at >= time_start)

        if time_end:
            query = query.filter(models.OpLog.created_at < time_end)


        total = query.count()
        if limit:
            query = query.limit(limit)
        if offset:
            query = query.offset(offset)
        return query.all(), total

    def oplog_create(self, context, oplog_values):
        session = self.db.get_session()
        values = copy.deepcopy(oplog_values)
        oplog = models.OpLog()
        params = oplog.generate_param(self.filter)
        for k, v in params.items():
            params[k] = values.get(k, params[k])
        oplog.update(params)
        self.db.add(session, oplog)

    def summary_list(self, context, **kwargs):
        session = self.db.get_session()
        task_time_start = kwargs.get('tast_time_start')
        task_time_end = kwargs.get('task_time_end')
        state_time_start = kwargs.get('state_time_start')
        state_time_end = kwargs.get('state_time_end')
        task_query = session.query(models.Task.type, models.Task.state, func.count())
        if not kwargs.get('deleted'):
            task_query = task_query.filter(models.Task.deleted == "False")
        if not context.get('is_superuser'):
            task_query = task_query.filter(models.Task.group_id == context.get('group_id'))
        task_query = task_query.group_by(models.Task.type, models.Task.state)
        tasks = task_query.all()
        summary = {}
        task_dict = summary['tasks'] = {}
        task_sum = 0
        for task in tasks:
            if not task_dict.get(task[0]):
                task_dict[task[0]] = {}
            type = task_dict[task[0]]
            type[task[1]] = task[2]
            task_sum = task_sum + task[2]
        task_dict['total'] = task_sum

        worker_query = session.query(models.Worker.status, func.count())

        if not kwargs.get('deleted'):
            worker_query = worker_query.filter(models.Worker.deleted == "False")
        if not context.get('is_superuser'):
            worker_query = worker_query.filter(models.Worker.group_id == context.get('group_id'))

        worker_query = worker_query.group_by(models.Worker.status)
        workers = worker_query.all()
        worker_dict = summary['workers'] = {}
        worker_sum = 0
        for worker in workers:
            worker_dict[worker[0]] = worker[1]
            worker_sum = worker_sum + worker[1]
        worker_dict['total'] = worker_sum

        group_query = session.query(models.Group)
        if not kwargs.get('deleted'):
            group_query = group_query.filter(models.Group.deleted == "False")
        group_sum = group_query.count()
        summary['groups'] = {'total': group_sum}

        user_query = session.query(models.User)
        if not kwargs.get('deleted'):
            user_query = user_query.filter(models.User.deleted == "False")
        if not context.get('is_superuser'):
            user_query = user_query.filter(models.User.group_id == context.get('group_id'))
        user_sum = user_query.count()
        summary['users'] = {'total': user_sum}

        bkstates_query = session.query(models.Task.id, models.Task.name,
                                       models.BackupState.state,
                                       func.count(models.BackupState.state)).\
            outerjoin(models.BackupState,
                      and_(models.Task.id == models.BackupState.task_id,
                           models.BackupState.deleted == "False"))

        if task_time_start:
            bkstates_query = bkstates_query.filter(models.Task.updated_at >= task_time_start)

        if task_time_end:
            bkstates_query = bkstates_query.filter(models.Task.updated_at < task_time_end)

        if state_time_start:
            bkstates_query = bkstates_query.filter(models.BackupState.updated_at >= state_time_start)

        if state_time_end:
            bkstates_query = bkstates_query.filter(models.BackupState.updated_at < state_time_end)


        if not context.get('is_superuser'):
            bkstates_query = bkstates_query.filter(models.Task.group_id == context.get('group_id'))

        if not kwargs.get('deleted'):
            bkstates_query = bkstates_query.filter(models.Task.deleted == 'False')

        bkstates_query = bkstates_query.group_by(models.Task.id,
                                                 models.BackupState.state)

        print bkstates_query
        logger.debug('bkstates_query : %s' % bkstates_query)
        bk_dict = summary['backupstates'] = {}
        bkststes = bkstates_query.all()
        bk_sum = 0
        for bk in bkststes:
            if not bk_dict.get(bk[0]):
                bk_dict[bk[0]] = {}
            b = bk_dict[bk[0]]
            b['name'] = bk[1]
            b[bk[2]] = bk[3]
            bk_sum = bk_sum + bk[3]
        bk_dict['total'] = bk_sum
        return summary


    def _tag_get(self, session=None, **kwargs):
        if not session:
            session = self.db.get_session()
        query = model_query(session, models.Tag)
        name = kwargs.get('name')
        tag_id = kwargs.get('id')
        group_id = kwargs.get('group_id')

        if name:
            query = query.filter(models.Tag.name == name)

        if tag_id:
            query = query.filter(models.Tag.id == tag_id)

        if kwargs.get('with_items'):
            query = query.options(joinedload(models.Tag.tag_items))

        if group_id:
            query = query.filter(models.Tag.group_id == group_id )

        return query

    def tag_get(self, context, tag_id, with_items=False, session=None):
        if not session:
            session = self.db.get_session()
        group_id = None
        if not context.get('is_superuser'):
            group_id = context.get('group_id')
        tag = self._tag_get(session, id=tag_id,
                            with_items=with_items,
                            group_id=group_id)
        if not tag:
            raise HTTPError(404, 'tag %s is not found' % tag_id)
        return tag.first()

    def tag_get_by_name(self, context, name, with_items=False, session=None):
        if not session:
            session = self.db.get_session()
        group_id = None
        if not context.get('is_superuser'):
            group_id = context.get('group_id')
        tag = self._tag_get(session, name=name,
                            with_items=with_items,
                            group_id=group_id).first()
        if not tag:
            raise NotFound('tag %s is not found' % name)
        return tag

    def tag_create(self, context, tag_values):
        logger.info('create tag : %s'%tag_values)
        session = self.db.get_session()
        values = copy.deepcopy(tag_values)
        values['id'] = uuidutils.generate_uuid()
        if not context.get('is_superuser'):
            values['group_id'] = context.get('group_id')
        tag = models.Tag()
        params = tag.generate_param(self.filter)
        for k, v in params.items():
            params[k] = values.get(k, params[k])
        logger.debug('volume params : %s ' % params)
        tag.update(params)
        self.db.add(session, tag)
        return self._tag_get(session, name=params['name']).first()

    def tag_update(self, context, tag_values, session=None):
        if not session:
            session = self.db.get_session()
        values = copy.deepcopy(tag_values)
        tag_id = values['id']
        name = values.get('name')
        tag = self.tag_get(context, tag_id, session=session)
        if not tag:
            raise NotFound('tag %s is not found ' % id)
        elif name and name != tag.name:
            try:
                self.tag_get_by_name(context, name)
                raise Duplicated()
            except NotFound:
                pass
        filter = ('id', 'deleted', 'deleted_at', 'created_at', 'updated_at', 'login_time')
        params = tag.generate_param(filter)
        for k, v in params.items():
            params[k] = values.get(k, params[k])
        tag.update(params)
        self.db.flush(session)
        return self.tag_get(context, tag_id, session=session)

    def _tag_item_get(self, session, **kwargs):
        pass

    def _tag_item_create(self, tag_item_values, session=None):
        if not session:
            session = self.db.get_session()
        tag_item = models.TagItem()
        params = tag_item.generate_param(self.filter)
        for k, v in params.items():
            params[k] = tag_item_values.get(k, params[k])
        tag_item.update(params)
        self.db.add(session, tag_item)

    def tag_list(self, context, detail=False, **kwargs):
        session = self.db.get_session()
        limit = kwargs.get('limit')
        offset = kwargs.get('offset')
        sort_key = kwargs.get('sort_key', 'created_at')
        sort_dir = kwargs.get('sort_dir', 'desc')
        query = model_query(session, models.Tag)

        if detail:
            query = query.options(joinedload(models.Tag.tag_items))

        if not context.get('is_superuser'):
            query = query.filter(models.Tag.group_id == context.get('group_id'))
        query = Database.sort(models.Tag, query, sort_key, sort_dir)
        total = query.count()
        if limit:
            query = query.limit(limit)
        if offset:
            query = query.offset(offset)
        tags = query.all()
        return tags, total

    def tag_detail_list(self, context, **kwargs):
        return self.tag_list(context, True, **kwargs)

    def tag_delete(self, context, tag_id, session=None):
        if not session:
            session = self.db.get_session()
        group_id = None
        if not context.get('is_superuser'):
            group_id = context.get('group_id')
        tag = self._tag_get(session=session, id=tag_id, group_id=group_id)
        old = tag.first()
        if old:
            items = self._tag_item_list(old.id)
            self.db.delete(session, items)
            self.db.delete(session, tag)
        else:
            raise HTTPError(404, 'tag %s is not found' % tag_id)
        return old.to_dict()

    def tag_add(self, context, tag_id, items, session=None):
        logger.debug('add items [ {0} ] to tag [ {1} ]'.format(
            items, tag_id
        ))
        if not session:
            session = self.db.get_session()
        tag = self.tag_get(context, tag_id)
        if not tag:
            logger.error('tag %s is not found ' % tag_id)
            raise HTTPError(404, 'tag %s is not found ' % tag_id)
        if isinstance(items, list):
            for item in items:
                try:
                    item['tag_id'] = tag.id
                    self._tag_item_create(item, session)
                except KeyError:
                    logger.error('lack of params')
                    raise HTTPError(400, 'bad body')


    def _tag_item_list(self, tag_id, session=None):
        if not session:
            session = self.db.get_session()
        query = model_query(session, models.TagItem)
        query = query.filter(models.TagItem.tag_id == tag_id)
        return query

def get_database(conf):
    '''
    :param conf:
    :return:
    '''
    return Database(conf)

def sync(conf):
    if isinstance(conf.get('database'), dict):
        database_conf = conf['database']
        logger.info('database config %s' % database_conf)
    else:
        database_conf = conf
    driver = database_conf.get('driver')
    if driver == 'sqlite':
        path = database_conf.get('path')
        path = 'sqlite:///%s' % path
        engine = create_engine(path)
        Base.metadata.bind = engine
        path = database_conf.get('path', '/var/backup/backup.db')
        Base.metadata.create_all(engine)
    elif driver == 'mysql' or driver == 'mariadb':
        user = database_conf.get('user')
        password = database_conf.get('password')
        host = database_conf.get('host')
        port = database_conf.get('port', 3306)
        database = database_conf.get('database')
        if user and password and host and port and database:
            url = 'mysql+mysqldb://{0}:{1}@{2}:{3}'. \
                format(user, password, host, port)
            engine = create_engine(url)
            engine.connect()
            engine.execute("CREATE DATABASE IF NOT EXISTS {0} CHARSET=utf8".format(database))
            engine.execute("USE {0}".format(database))
            Base.metadata.create_all(engine)

