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

                path = 'mysql+mysqldb://{0}:{1}@{2}:{3}/{4}'. \
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
        deleted = True
        query = model_query(session, models.Task)

        if detail:
            query = query.options(
                joinedload(models.Task.policy),
                joinedload(models.Task.worker),
                joinedload(models.Task.states),
            )

        query = query.filter(models.Task.type == type)

        if not context['is_superuser']:
            query = query.filter(models.Task.group_id == context.get('group_id'))

        if 'deleted' not in kwargs:
            deleted = False
            query = query.filter(models.Task.deleted == 'False')

        if worker_name:
            w = self.get_worker_by_name(session, worker_name, deleted)
            worker_id = w.id
        if policy_name:
            p = self.get_policy_by_name(session, policy_name, deleted)
            policy_id = p.id
        if worker_id :
            query = query.filter(models.Task.worker_id == worker_id)
        if policy_id:
            query = query.filter(models.Task.policy_id == policy_id)
        if task_name:
            query = query.filter(models.Task.name == task_name)
        query = Database.sort(models.Task, query, sort_key, sort_dir)
        total = query.count()
        if limit:
            query = query.limit(limit)
        if offset:
            query = query.offset(offset)
        return query.all(), total

    def get_tasks_all(self, context, **kwargs):
        return self.get_tasks(context, True, **kwargs)


    def _get_task(self, session=None, **kwargs):
        if not session:
            session = self.db.get_session()
        id = kwargs.get('id')
        name = kwargs.get('name')
        query = model_query(session, models.Task)
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

        task = query.first()
        return task


    def get_task(self, context, id, detail=True, session=None):
        logger.info('trying to get a task , id = %s'%id)
        task = self._get_task(session, id=id, detail=detail)
        if not task:
            logger.error('task not found, %s' % id)
            raise NotFound()
        return task

    def create_task(self, context, task_values):
        logger.info('create task : %s' % task_values)
        session = self.db.get_session()
        values = copy.deepcopy(task_values)
        values['id'] = uuidutils.generate_uuid()
        values['user_id'] = context.get('user_id')
        values['group_id'] = context.get('group_id')
        task = models.Task()
        params = task.generate_param(self.filter)
        for k, v in params.items():
            params[k] = values.get(k, params[k])
        task.update(params)
        self.db.add(session, task)
        return self._get_task(session, id=params['id'])

    def update_task(self, context, task_values):
        logger.info('update task : %s '%task_values)
        session = self.db.get_session()
        values = copy.deepcopy(task_values)
        id = task_values.get('id')
        try:
            task = self._get_task(session, id=id)
        except:
            raise
        filter = ('id', 'deleted', 'deleted_at','created_at', 'updated_at')
        params = task.generate_param(filter)
        for k, v in params.items():
            params[k] = values.get(k, params[k])
        task.update(params)
        self.db.flush(session)
        return self._get_task(session, id=id)

    def delete_task(self, context, id):
        session = self.db.get_session()
        task = self._get_task(session, id=id)
        self.db.soft_delete(session, task)

    def get_policies(self, context, detail=False, session=None, **kwargs):
        if not session:
            session = self.db.get_session()
        logger.info('list policies : %s '%kwargs)
        limit = kwargs.get('limit', 0)
        offset = kwargs.get('offset', 0)
        sort_key = kwargs.get('sort_key', 'created_at')
        sort_dir = kwargs.get('sort_dir', 'desc')
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

        if not context['is_superuser']:
            query = query.filter(models.Policy.group_id == context.get('group_id'))

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
        if name:
            query = query.filter(models.Policy.name == name)
        if id:
            query = query.filter(models.Policy.id == id)

        if 'with_user' in kwargs:
            query = query.options(joinedload(models.Policy.user))

        if 'with_tasks' in kwargs:
            query = query.outerjoin(
                models.Task, and_(models.Task.policy_id == models.Policy.id).
                    options(contains_eager(models.Policy.tasks)))

        if 'deleted' not in kwargs:
            query = query.filter(models.Policy.deleted == 'False').\
                filter(models.Task.deleted == 'False')

        policy = query.first()

        return policy


    def get_policy(self, context, id, session=None):
        logger.info('trying to get a policy %s'%id)
        policy = self._get_policy( session, id=id, with_user=True)
        if not policy:
            logger.error('policy not found, %s'%id)
            raise NotFound()
        return policy

    def get_policy_by_name(self, session, name, deleted=False):
        policy = self._get_policy(session, name=name, deleted=deleted )
        if not policy:
            raise NotFound()
        return policy

    def create_policy(self, context, policy_values):
        logger.info('create policy : %s ' % policy_values)
        session = self.db.get_session()
        values = copy.deepcopy(policy_values)
        values['id'] = uuidutils.generate_uuid()
        values['user_id'] = context.get('user_id')
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
        policy = self._get_policy(session, id=id)
        params = policy.generate_param(self.filter)
        for k, v in params.items():
            params[k] = values.get(k, params[k])
        policy.update(params)
        self.db.flush(session)
        return self._get_policy(session, id=id)

    def delete_policy(self, context, id):
        session = self.db.get_session()
        policy = self._get_policy(session, id=id)
        tasks = policy.tasks
        if not tasks:
            self.db.soft_delete(session, policy)
            return None
        else:
            return tasks

    def get_workers(self, context, detail=False, **kwargs):
        session = self.db.get_session()
        logger.info('list workers : %s '%kwargs)
        limit = kwargs.get('limit', 0)
        offset = kwargs.get('offset', 0)
        sort_key = kwargs.get('sort_key', 'created_at')
        sort_dir = kwargs.get('sort_dir', 'desc')
        name = kwargs.get('name', 'unkown')
        query = model_query(session, models.Worker)
        if detail:
            query = query.options(
                joinedload(models.Worker.user)
            )

        query = Database.sort(models.Worker, query, sort_key, sort_dir)
        if 'deleted' not in kwargs:
            query = query.filter(models.Worker.deleted == 'False')

        if not context['is_superuser']:
            query = query.filter(models.Worker.group_id == context.get('group_id'))

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
        query = model_query(session, models.Worker)
        if id:
            query = query.filter(models.Worker.id == id)
        if name:
            query = query.filter(models.Worker.name == name)

        if 'with_user' in kwargs:
            query = query.options(joinedload(models.Worker.user))

        if 'with_tasks'  in kwargs:
            query = query.outerjoin(
                models.Task, and_(models.Task.worker_id == models.Worker.id)).\
                options(contains_eager(models.Worker.tasks)
            )
        if 'deleted' not in kwargs:
            query = query.filter(models.Worker.deleted == 'False').\
                filter(models.Task.deleted == 'False')

        worker = query.first()
        return worker

    def get_worker(self, context, id, session=None):
        logger.info('trying to get a worker id=%s'%id)
        worker = self._get_worker(session, id=id, with_user=True, with_tasks=True)
        if not worker:
            logger.error('worker not found %s'%id)
            raise NotFound()
        return worker


    def get_worker_by_name(self, context ,worker_name, session=None, deleted=False):
        worker = self._get_worker(session, name=worker_name, deleted=deleted)
        if not worker:
            raise NotFound()
        return worker

    def create_worker(self, context,  worker_values):
        logger.info('create a worker : %s' % worker_values)
        session = self.db.get_session()
        values = copy.deepcopy(worker_values)
        values['id'] = uuidutils.generate_uuid()
        values['owner'] = context.get('user_id')
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
        try:
            worker = self._get_worker(session, id=id)
        except:
            raise
        filter = ('start_at', 'deleted', 'deleted_at','created_at', 'updated_at')
        params = worker.generate_param(filter)
        for k, v in params.items():
            params[k] = values.get(k, params[k])
        worker.update(params)
        self.db.flush(session)
        return self._get_worker(session, id=id)

    def delete_worker(self, context, id):
        logger.info('deleting a worker , id = %s'%id)
        session = self.db.get_session()
        worker = self._get_worker(session, id=id)
        tasks = worker.tasks
        if not tasks:
            self.db.soft_delete(session, worker)
            return None
        else:
            return tasks

    def get_users(self, context, **kwargs):
        session = self.db.get_session()
        limit = kwargs.get('limit', 0)
        offset = kwargs.get('offset', 0)
        sort_key = kwargs.get('sort_key', 'created_at')
        sort_dir = kwargs.get('sort_dir', 'desc')
        name = kwargs.get('name')
        query = model_query(session, models.User)
        query = query.options(joinedload(models.User.role))
        query = query.options(joinedload(models.User.group))
        query = Database.sort(models.User, query, sort_key, sort_dir)
        if name:
            query = query.filter(models.User.name == name)
        if 'deleted' not in kwargs:
            query = query.filter(models.User.deleted == 'False')
        if limit:
            query = query.limit(limit)

        if offset:
            query = query.offset(offset)

        if not context['is_superuser']:
            query = query.filter(models.User.group_id == context.get('group_id'))

        total = query.count()
        return query.all(),  total

    def _get_user(self, session=None, **kwargs):
        if not session:
            session = self.db.get_session()
        query = model_query(session, models.User)
        id = kwargs.get('id')
        name = kwargs.get('name')
        role_id = kwargs.get('role_id')
        if name:
            query = query.filter(models.User.name == name)
        if id:
            query = query.filter(models.User.id == id)
        if role_id:
            query = query.filter(models.User.role_id == role_id)

        if 'deleted' not in kwargs:
            if 'with_role' in kwargs:
                query = query.options(joinedload(models.User.role))
            if 'with_group' in kwargs:
                query = query.options(joinedload(models.User.group))
            if 'with_tasks' in kwargs:
                query = query.outerjoin(
                    models.Task, and_(models.Task.user_id == models.User.id,
                                      models.Task.deleted == 'False')). \
                    options(contains_eager(models.User.tasks)
                            )
            query = query.filter(models.User.deleted == 'False')
        else:
            if 'with_role' in kwargs:
                query = query.options(joinedload(models.User.role))
            if 'with_tasks' in kwargs:
                query = query.options(
                    joinedload(models.User.tasks)
                )
        user = query.first()
        return user

    def get_user(self, context, id, session=None, **kwargs):
        user = self._get_user( session, id=id, with_role=True, with_group=True, **kwargs)
        if not user:
            logger.error('user not found, %s'%kwargs)
            raise HTTPError(404, 'user : {0} is not found '.format(id))
        return user

    def get_user_by_name(self, context, username, with_role=True, with_group=False, session=None):
        user = self._get_user( session, name=username, with_role=with_role, with_group=with_group)
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
        session = self.db.get_session()
        values = copy.deepcopy(user_values)
        id = values['id']
        user = self._get_user(session, id=id)
        filter = ('id', 'deleted', 'deleted_at','created_at', 'updated_at', 'login_time')
        params = user.generate_param(filter)
        password = user_values.get('password')
        if password:
            values['key'] = uuidutils.generate_uuid(False)
            digest = auth_basic.calculate_digest(user.name, password, values['key'])
            values['password'] = digest
        for k, v in params.items():
            params[k] = values.get(k, params[k])
        user.update(params)
        self.db.flush(session)
        return self._get_user(session, id=id)


    def delete_user(self, context, id, session=None):
        if not session:
            session = self.db.get_session()
        user = self._get_user(session, id=id)
        tasks = user.tasks
        if not tasks:
            self.db.soft_delete(session, user)
            return None
        else:
            return tasks


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

    def bk_update(self, context, bk_values):
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
                t = self._get_task(session, name=task_name)
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

        if 'deleted' not in kwargs:
            query = query.filter(models.User.deleted == 'False')

        role = query.first()
        return role

    def role_get(self, context, id , session=None):
        role = self._role_get(session, id=id)
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
        if limit:
            query = query.limit(limit)
        if offset:
            query = query.offset(offset)
        total = query.count()
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
        if limit:
            query = query.limit(limit)
        if offset:
            query = query.offset(offset)
        total = query.count()
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

        if 'with_users':
            query = query.options(
                joinedload(models.Group.users)
            )

        if 'deleted' not in kwargs:
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
        try:
            group = self._group_get(session, id=id)
        except:
            raise
        params = group.generate_param(self.filter)
        for k, v in params.items():
            params[k] = values.get(k, params[k])
            group.update(params)
        self.db.flush(session)
        return self._group_get(session, id=id)

    def group_delete(self, context, group_id, session=None):
        if not session:
            session = self.db.get_session()
        group = self._group_get(session, id=group_id)
        self.db.soft_delete(session, group)


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
        if limit:
            query = query.limit(limit)
        if offset:
            query = query.offset(offset)
        total = query.count()
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

        if 'with_users' in kwargs:
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
            logger.error('volume not found, %s' % kwargs)
            raise HTTPError(404, 'volume  {0} is not found '.format(id))
        return volume

    def volume_create(self, context, volume_values):
        logger.info('create task : %s'%volume_values)
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
        volume = self._volume_get(session, id=id)
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
        self.db.soft_delete(session, volume)

def get_database(conf):
    '''
    :param conf:
    :return:
    '''
    return Database(conf)

