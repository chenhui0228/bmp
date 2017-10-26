from routes import Mapper
from db.sqlalchemy import api as db_api
from cherrypy import HTTPError

import logging
logger = logging.getLogger('backup')

class Resource(object):
    def __init__(self, controller):
        self.controller = controller

    def __call__(self, reqargs, req):
        action = reqargs['action']
        del reqargs['action']
        return self._process_stack(action, reqargs)

    def _process_stack(self, action, action_args):
        try:
            method = self.get_method(action)
        except (AttributeError, TypeError):
            raise
        action_result = self.dispatch(method, action_args)
        return action_result

    def dispatch(self, method,  action_args):
        return method(action_args)


    def get_method(self, action):
        try:
            if not self.controller:
                meth = getattr(self, action)
            else:
                meth = getattr(self.controller, action)
        except AttributeError:
                raise
        return meth

class Controller(Resource):
    def __init__(self, conf):
        self.db = db_api.get_database(conf)

class TasksController(Controller):
    def index(self, action_args):
        logger.info('list tasks')
        tasks , total= self.db.get_tasks(**action_args)
        result = list()
        for p in tasks:
            result.append(p.to_dict())
        return {'total': total, 'tasks': result}

    def detail(self, action_args):
        logger.info('list tasks with detail ')
        logger.debug('action_args :  %s'%action_args)
        tasks , total=  self.db.get_tasks_all(**action_args)
        result = list()
        for t in tasks:
            task = {}
            policy = t.policy
            worker = t.worker
            state = t.state
            task['task'] = t.to_dict()
            if policy:
                task['policy'] = policy.to_dict()
            if worker:
                task['worker'] = worker.to_dict()
            if state :
                task['state'] = state[0].to_dict()
            result.append(task)
        return {'total': total, 'tasks': result}

    def show(self, action_args):
        logger.info('get tast  ')
        logger.debug('action_args :  %s'%action_args)
        task = self.db.get_task(**action_args)
        task_detail = {}
        policy = task.policy
        worker = task.worker
        state = task.state
        task_detail['task'] = task.to_dict()
        if policy:
            task_detail['policy'] = policy.to_dict()
        if worker:
            task_detail['worker'] = worker.to_dict()
        if state:
            task_detail['state'] = state[0].to_dict()
        return task_detail

    def _validate_prams(self, prams):
        pass

    def create(self, action_args):
        logger.info('create a task ')
        logger.debug('task params :  %s'%action_args)
        self._validate_prams(action_args)
        task = self.db.create_task(action_args)
        return {'task': task.to_dict()}

    def delete(self, action_args):
        id = action_args.get('id')
        return self.db.delete_task(id)

    def update(self, action_args):
        self._validate_prams(action_args)
        task = self.db.update_task(action_args)
        if not task:
            return
        return {'task': task.to_dict()}


class PoliciesController(Controller):
    def index(self, action_args):
        policies , total = self.db.get_policies(**action_args)
        result = list()
        for p in policies:
            result.append(p.to_dict())
        return {'total': total, 'policies': result}

    def show(self, action_args):
        id = action_args.get('id')
        policy = self.db.get_policy(id)
        return {'policy':policy.to_dict()}

    def detail(self, action_args):
        return self.index(action_args)

    def create(self, action_args):
        policy = self.db.create_policy(action_args)
        return {'policy': policy.to_dict()}

    def delete(self, action_args):
        id =  action_args['id']
        logger.info('trying to delete policy id = %s'%id)
        tasks = self.db.delete_policy(id)
        result = {
            'message': 'success',
            'tasks': []
        }
        if tasks:
            logger.debug('policy is not delete due to related tasks')
            result['message'] = 'you should delete tasks first'
            for t in tasks:
                result['tasks'].append(t.to_dict())
            raise HTTPError(403, str(result))
        return result

    def update(self, action_args):
        policy = self.db.update_policy(action_args)
        return {'policy': policy.to_dict()}


class WorkersController(Controller):
    def index(self, action_args):
        workers , total=  self.db.get_workers(**action_args)
        result = list()
        for p in workers:
            result.append(p.to_dict())
        return {'total': total, 'workers': result}

    def detail(self, action_args):
        return self.index(action_args)

    def show(self, action_args):
        id = action_args.get('id')
        action_args.pop('id')
        worker = self.db.get_worker(id, **action_args)
        return {'worker':worker.to_dict()}

    def create(self, action_args):
        worker = self.db.create_worker(action_args)
        return {'worker':worker.to_dict()}

    def delete(self, action_args):
        id =  action_args['id']
        tasks =  self.db.delete_worker(id)
        result = {
            'code':200,
            'message':'success',
            'tasks':[]
        }
        if tasks:
            result['code'] = 405
            result['message'] = 'you should delete tasks first'
            for t in tasks:
                result['tasks'].append(t.to_dict())
            #raise HTTPError(403, str(result))

        return result

    def update(self, action_args):
        worker = self.db.update_worker(action_args)
        return {'worker':worker.to_dict()}


class UserController(Controller):
    def index(self, action_args):
        users , total=  self.db.get_users(**action_args)
        result = list()
        for p in users:
            result.append(p.to_dict())
        return {'total': total, 'users': result}

    def detail(self, action_args):
        self.index(action_args)

    def show(self, action_args):
        id = action_args.get('id')
        user = self.db.get_user(id)
        return {'user': user.to_dict()}

    def create(self, action_args):
        user = self.db.create_user(action_args)
        return {'user': user.to_dict()}

    def delete(self, action_args):
        id =  action_args['id']
        tasks = self.db.delete_worker(id)
        result = {
            'message': 'success',
            'tasks': []
        }

        if tasks:
            result['message'] = 'you should delete tasks first'
            for t in tasks:
                result['tasks'].append(t.to_dict())
            raise HTTPError(403, str(result))
        return result

    def update(self, action_args):
        user = self.db.update_user(action_args)
        return {'user': user.to_dict()}


class BackupStateController(Controller):
    def index(self, action_args):
        states, total = self.db.bk_list(**action_args)
        result = list()
        for s in states:
            result.append(s.to_dict())
        return {'total': total, 'states': result}

    def detail(self, action_args):
        states, total = self.db.bk_list(True, **action_args)
        result = list()
        for s in states:
            task = s.task
            result.append({
                'task': task.to_dict(),
                'state': s.to_dict()
            })
        return {'total': total, 'states': result}

    def show(self, action_args):
        id = action_args.get('id')
        state = self.db.get_bk_state(id, True)
        return {
            'state': state.to_dict(),
            'task': state.task.to_dict()
        }

    def create(self, action_args):
        state = self.db.bk_create(action_args)
        return {'state': state.to_dict()}

    def delete(self, action_args):
        logger.info('state is not supposed to be deleted')
        raise HTTPError(403, 'delete state is not permitted ')

    def update(self, action_args):
        state = self.db.bk_update(action_args)
        return {'state':state.to_dict()}


class BackupMapper(Mapper):
    def resource(self, member_name, collection_name, **kwargs):
        kwargs['path_prefix'] = 'backup'
        Mapper.resource(self,member_name,collection_name,**kwargs)


class APIRouter(object):
    def __init__(self, conf):
        self.conf = conf
        self.mapper = BackupMapper()
        self.resources = {}
        self._setup_routes()

    def _setup_routes(self):
        self.resources['tasks'] = Resource(TasksController(self.conf))
        self.resources['policies'] = Resource(PoliciesController(self.conf))
        self.resources['workers'] = Resource(WorkersController(self.conf))
        self.resources['users'] = Resource(UserController(self.conf))
        self.resources['backupstates'] = Resource(BackupStateController(self.conf))
        self.mapper.resource('task','tasks',
                             controller=self.resources['tasks'],
                             collection={'detail': 'GET'})

        self.mapper.resource('policie', 'policies',
                             controller=self.resources['policies'],
                             collection={'detail': 'GET'})

        self.mapper.resource('worker', 'workers',
                             controller=self.resources['workers'],
                             collection={'detail': 'GET'})

        self.mapper.resource('user', 'users',
                             controller=self.resources['users'],
                             collection={'detail': 'GET'})

        self.mapper.resource('backupstate', 'backupstates',
                             controller=self.resources['backupstates'],
                             collection={'detail': 'GET'})

    def dispatch(self, req):
        environ = req.wsgi_environ
        url = req.path_info
        reqargs = self.mapper.match(url, environ)
        if reqargs:
            controller = reqargs['controller']
            del reqargs['controller']
            reqargs.update(req.params)
            return controller(reqargs, req)
        else:
            logger.error('method is not allowed, %s'%url)
            raise HTTPError(405, 'the url %s  method is not allowed'%url)


