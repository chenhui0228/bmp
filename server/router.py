from routes import Mapper
from db.sqlalchemy import api as db_api
from cherrypy import HTTPError
from jsontools import json_out_decrator as json_out
import functools
import six
import jsontools
from auth.authorization import PolicyManager
from auth import  authentication
from auth import exception
from backup_controller import server as bkserver

import logging
logger = logging.getLogger('backup')


def action(name):
    def decorator(func):
        func.wsgi_action = name
        return func
    return decorator

_MEDIA_TYPE_MAP = {
    'application/json': 'json',
}



class Resource(object):
    def __init__(self, controller):
        self.controller = controller

    def __call__(self, reqargs, req):
        action = reqargs['action']
        del reqargs['action']
        username = reqargs['user']
        is_usperuser = False
        if username == authentication.superuser.name:
            user = authentication.superuser
            is_usperuser = True
        else:
            user = self.controller.\
                db.get_user_by_name(authentication.super_context,username, True, True)
        context = {
            'is_superuser': is_usperuser,
            'user_id': user.id,
            'role': user.role.name if not is_usperuser else authentication.superrole.name,
            'group_id': user.group.id if not is_usperuser else ''
        }
        reqargs['context'] = context
        logger.debug('context = %s' % context)
        return self._process_stack(req, action, reqargs)

    def _process_stack(self, request, action, action_args):
        content_type = action_args.get('CONTENT_TYPE')
        body = request.body
        try:
            method = self.get_method(action, content_type, body)
        except (AttributeError, TypeError):
            logger.error('method %s is not allowed .' % action)
            raise HTTPError(405, 'method %s is not allowed .' % action)
        action_result = self.dispatch(method, action_args)
        return action_result

    def dispatch(self, method,  action_args):
        return method(action_args)


    def get_method(self, action, content_type, body):
        try:
            if not self.controller:
                meth = getattr(self, action)
            else:
                meth = getattr(self.controller, action)
        except AttributeError:
                if (not self.controller.wsgi_actions or
                            action not in ['action', 'create', 'delete']):
                    # Propagate the error
                    logger.error('method %s is not implemented.' % action)
                    raise
        else:
            return meth

        action_name = 'unknown'
        body = body.read()
        if action == 'action':
            action_name = jsontools.action_peek_json(body)
            logger.debug("Action body: %s" % body)
        else:
            action_name = action

        logger.debug('Action method: %s' % action_name)
        return getattr(self.controller,
                       self.controller.wsgi_actions[action_name])

class ControllerMetaclass(type):
    def __new__(mcs, name, bases, cls_dict):
        actions = {}
        for base in bases:
            actions.update(getattr(base, 'wsgi_actions', {}))
        for key, value in cls_dict.items():
            if not callable(value):
                continue
            if getattr(value, 'wsgi_action', None):
                actions[value.wsgi_action] = key
        cls_dict['wsgi_actions'] = actions
        return super(ControllerMetaclass, mcs).__new__(mcs, name, bases, cls_dict)


@six.add_metaclass(ControllerMetaclass)
class Controller(Resource):

    def __init__(self, conf):
        self.db = db_api.get_database(conf)
        self.policy = PolicyManager(conf)

    @staticmethod
    def authorize(arg):

        action_name = None

        def decorator(f):
            @functools.wraps(f)
            def wrapper(self, action_args, *args, **kwargs):
                action = action_name or f.__name__
                context = action_args['context']
                try:
                    self.policy.check_policy(context, self.resource_name, action)
                except exception.PolicyNotAuthorized:
                    raise HTTPError(403)
                return f(self, action_args, *args, **kwargs)

            return wrapper

        if callable(arg):
            return decorator(arg)
        else:
            action_name = arg
            return decorator

class TasksController(Controller):
    resource_name = 'Task'

    @Controller.authorize
    @json_out
    def index(self, action_args):
        logger.info('list tasks')
        tasks , total= self.db.get_tasks(**action_args)
        result = list()
        for p in tasks:
            result.append(p.to_dict())
        return {'total': total, 'tasks': result}

    @Controller.authorize
    @json_out
    def detail(self, action_args):
        logger.info('list tasks with detail ')
        logger.debug('action_args :  %s'%action_args)
        tasks , total=  self.db.get_tasks_all(**action_args)
        result = list()
        for t in tasks:
            task = {}
            policy = t.policy
            worker = t.worker
            states = t.states
            task['task'] = t.to_dict()
            if policy:
                task['policy'] = policy.to_dict()
            if worker:
                task['worker'] = worker.to_dict()
            if states:
                task['state'] = states[0].to_dict()
            result.append(task)
        return {'total': total, 'tasks': result}

    @Controller.authorize
    @json_out
    def show(self, action_args):
        logger.info('get tast  ')
        logger.debug('action_args :  %s'%action_args)
        id = action_args.get('id')
        context = action_args.get('context')
        task = self.db.get_task(context, id)
        task_detail = {}
        policy = task.policy
        worker = task.worker
        states = task.states
        task_detail['task'] = task.to_dict()
        if policy:
            task_detail['policy'] = policy.to_dict()
        if worker:
            task_detail['worker'] = worker.to_dict()
        if states:
            task_detail['state'] = states[0].to_dict()
        return task_detail

    def _validate_prams(self, prams):
        pass

    @Controller.authorize
    def create(self, action_args):
        logger.info('create a task ')
        logger.debug('task params :  %s' % action_args)
        self._validate_prams(action_args)
        context = action_args['context']
        task = self.db.create_task(context, action_args)
        bkctl = bkserver.Server()
        bkctl.backup(task.id)
        return {'task': task.to_dict()}

    @Controller.authorize
    def delete(self, action_args):
        id = action_args.get('id')
        context = action_args['context']
        return self.db.delete_task(context, id)

    @Controller.authorize
    def update(self, action_args):
        self._validate_prams(action_args)
        context = action_args['context']
        task = self.db.update_task(context, action_args)
        if not task:
            return
        return {'task': task.to_dict()}

    @Controller.authorize
    @action('start')
    def start(self, action_args):
        bkctl = bkserver.Server()
        bkctl.backup(action_args['id'], True)

    @Controller.authorize
    @action('stop')
    def stop(self, action_args):
        pass

    @action('pause')
    @Controller.authorize
    def pause(self, **action_args):
        pass

    @Controller.authorize
    @action('resume')
    def resume(self, **action_args):
        pass

class PoliciesController(Controller):

    resource_name = 'policy'

    @Controller.authorize
    @json_out
    def index(self, action_args):
        policies , total = self.db.get_policies(**action_args)
        result = list()
        for p in policies:
            result.append(p.to_dict())
        return {'total': total, 'policies': result}

    @Controller.authorize
    @json_out
    def show(self, action_args):
        id = action_args.get('id')
        context = action_args.get('context')
        p = self.db.get_policy(context, id)
        policy = p.to_dict()
        policy['user'] = p.user.name if p.user else ''
        return {'policy': policy}

    @Controller.authorize
    @json_out
    def detail(self, action_args):
        policies , total = self.db.get_policies(detail=True, **action_args)
        result = list()
        for p in policies:
            u = p.user
            policy = p.to_dict()
            policy['user'] = u.name if u else ''
            result.append(policy)
        return {'total': total, 'policies': result}

    @Controller.authorize
    def create(self, action_args):
        context = action_args['context']
        policy = self.db.create_policy(context, action_args)
        return {'policy': policy.to_dict()}

    @Controller.authorize
    def delete(self, action_args):
        id =  action_args['id']
        context = action_args['context']
        logger.info('trying to delete policy id = %s'%id)
        tasks = self.db.delete_policy(context, id)
        if tasks:
            logger.debug('policy is not delete due to related tasks')
            result = {"tasks": []}
            result["message"] = "you should delete tasks first"
            for t in tasks:
                result["tasks"].append(t.name)
            result['code'] = '403'
            msg = jsontools.json_out(result, None)
            out = ""
            for m in msg:
                out += m
            raise HTTPError(403, out)

    def update(self, action_args):
        context = action_args['context']
        policy = self.db.update_policy(context, action_args)
        return {'policy': policy.to_dict()}


class WorkersController(Controller):
    resource_name = 'worker'

    @Controller.authorize
    @json_out
    def index(self, action_args):
        workers , total=  self.db.get_workers(**action_args)
        result = list()
        for p in workers:
            result.append(p.to_dict())
        return {'total': total, 'workers': result}


    @Controller.authorize
    @json_out
    def detail(self, action_args):
        workers , total= self.db.get_workers(detail=True, **action_args)
        result = list()
        for w in workers:
            u = w.user
            worker = w.to_dict()
            worker['user'] = u.to_dict() if u else ''
            result.append(worker)
        return {'total': total, 'workers': result}

    @Controller.authorize
    @json_out
    def show(self, action_args):
        id = action_args.get('id')
        context = action_args.get('context')
        action_args.pop('id')
        worker = self.db.get_worker(context, id)
        user = worker.user
        worker_info = worker.to_dict()
        worker_info['user'] = user.name
        return {'worker':worker_info}

    @Controller.authorize
    def create(self, action_args):
        context = action_args['context']
        worker = self.db.create_worker(context, action_args)
        return {'worker': worker.to_dict()}

    @Controller.authorize
    def delete(self, action_args):
        id =  action_args['id']
        context = action_args['context']
        tasks = self.db.delete_worker(context, id)
        result = {}
        if tasks:
            result['code'] = 403
            result['message'] = 'you should delete tasks first'
            for t in tasks:
                result['tasks'] = []
                result['tasks'].append(t.to_dict())
            msg = jsontools.json_out(result, None)
            out = ""
            for m in msg:
                out += m
            raise HTTPError(403, out)

    @Controller.authorize
    def update(self, action_args):
        context = action_args['context']
        worker = self.db.update_worker(context, action_args)
        return {'worker':worker.to_dict()}


class UserController(Controller):
    resource_name = 'user'

    @Controller.authorize
    @json_out
    def index(self, action_args):
        users , total=  self.db.get_users(**action_args)
        result = list()
        for p in users:
            u = p.to_dict()
            result.append(u)
        return {'total': total, 'users': result}

    @Controller.authorize
    @json_out
    def detail(self, action_args):
        users , total = self.db.get_users(**action_args)
        result = list()
        for p in users:
            u = p.to_dict()
            u['role'] = p.role.name if p.role else ''
            u['group'] = p.group.name if p.group else ''
            result.append(u)
        return {'total': total, 'users': result}

    @Controller.authorize
    @json_out
    def show(self, action_args):
        id =  action_args['id']
        context = action_args['context']
        user = self.db.get_user(context, id)
        role = user.role
        group = user.group
        result = user.to_dict()
        result['role'] = role.name if role else ''
        result['group'] = group.name if group else ''
        return {'user': result}

    @Controller.authorize
    def create(self, action_args):
        context = action_args['context']
        del action_args['context']
        user = self.db.create_user(context, action_args)
        return {'user': user.to_dict()}

    @Controller.authorize
    def delete(self, action_args):
        id =  action_args['id']
        context = action_args['context']
        self.db.delete_user(context, id)

    def update(self, action_args):
        context = action_args['context']
        user = self.db.update_user(context, action_args)
        return {'user': user.to_dict()}


class BackupStateController(Controller):
    resource_name = 'backupstate'

    @Controller.authorize
    @json_out
    def index(self, action_args):
        states, total = self.db.bk_list(**action_args)
        result = list()
        for s in states:
            result.append(s.to_dict())
        return {'total': total, 'states': result}

    @Controller.authorize
    @json_out
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

    @Controller.authorize
    @json_out
    def show(self, action_args):
        id = action_args.get('id')
        context = action_args.get('context')
        state = self.db.get_bk_state(context, id, True)
        return {
            'state': state.to_dict(),
            'task': state.task.to_dict()
        }

    @Controller.authorize
    def create(self, action_args):
        context = action_args['context']
        del action_args['context']
        state = self.db.bk_create(context, action_args)
        return {'state': state.to_dict()}

    @Controller.authorize
    def delete(self, action_args):
        logger.info('state delete is not supported')
        raise HTTPError(405, 'delete state is not supported ')

    @Controller.authorize
    def update(self, action_args):
        context = action_args.get('context')
        state = self.db.bk_update(context, action_args)
        return {'state':state.to_dict()}

import os
import cherrypy
class ReportController(Controller):
    def generate(self, action_args):
        filename = '/home/python/hello.py'
        basename = os.path.dirname(filename)
        mime = 'application/octet-stream'
        return cherrypy.lib.static.serve_file(filename, mime, basename)

    @json_out
    def tasks(self, action_args):
        return action_args


class RoleController(Controller):
    resource_name = 'role'

    @Controller.authorize
    @json_out
    def index(self, action_args):
        roles , total=  self.db.role_list(**action_args)
        result = list()
        for role in roles:
            result.append(role.to_dict())
        return {'total': total, 'roles': result}

    @Controller.authorize
    @json_out
    def show(self, action_args):
        role_id = action_args.get('id')
        context = action_args.get('context')
        role = self.db.role_get(context, role_id)
        return {'role': role.to_dict()}

    @Controller.authorize
    def create(self, action_args):
        context = action_args['context']
        del action_args['context']
        role = self.db.role_create(context, action_args)
        return {'role': role.to_dict()}

    @Controller.authorize
    def update(self, action_args):
        context = action_args.get('context')
        role = self.db.role_update(context, action_args)
        return {'role': role.to_dict()}

    @Controller.authorize
    def delete(self, action_args):
        id = action_args.get('id')
        context = action_args.get('context')
        return self.db.role_delete(context, id)


class GroupController(Controller):
    resource_name = 'group'

    @Controller.authorize
    @json_out
    def index(self, action_args):
        groups , total=  self.db.group_list(**action_args)
        result = list()
        for group in groups:
            result.append(group.to_dict())
        return {'total': total, 'groups': result}

    @Controller.authorize
    @json_out
    def detail(self, action_args):
        groups, total = self.db.group_list(detail=True, **action_args)
        result = list()
        for g in groups:
            users = g.users
            ul = list()
            if users:
                for u in users:
                    uu = u.to_dict()
                    ul.append(uu)
            group_detail = g.to_dict()
            group_detail['users'] = ul
            result.append(group_detail)
        return {'total': total, 'groups': result}

    @Controller.authorize
    @json_out
    def show(self, action_args):
        id = action_args.get('id')
        context = action_args.get('context')
        group = self.db.group_get(context, id)
        users = group.users
        ul = list()
        if users:
            for u in users:
                uu = u.to_dict()
                ul.append(uu)
        group_detail = group.to_dict()
        group_detail['users'] = ul
        return group_detail

    @Controller.authorize
    def create(self, action_args):
        context = action_args['context']
        del action_args['context']
        group = self.db.group_create(context, action_args)
        return {'group': group.to_dict()}

    @Controller.authorize
    def update(self, action_args):
        context = action_args.get('context')
        group = self.db.group_update(context, action_args)
        return {'group': group.to_dict()}

    @Controller.authorize
    def delete(self, action_args):
        id = action_args.get('id')
        context = action_args.get('context')
        return self.db.group_delete(context, id)

class VolumeController(Controller):

    resource_name = 'volume'

    @Controller.authorize
    @json_out
    def index(self, action_args):
        volumes , total = self.db.volume_list(**action_args)
        result = list()
        for v in volumes:
            result.append(v.to_dict())
        return {'total': total, 'volumes': result}

    @Controller.authorize
    @json_out
    def detail(self, action_args):
        volumes, total = self.db.volume_list(detail=True, **action_args)
        result = list()
        for v in volumes:
            user = v.user
            vloume_detail = v.to_dict()
            vloume_detail['users'] = user.to_dict() if user else ''
            result.append(vloume_detail)
        return {'total': total, 'volumes': result}

    @Controller.authorize
    @json_out
    def show(self, action_args):
        id = action_args.get('id')
        context = action_args.get('context')
        v = self.db.volume_get(context, id)
        user = v.user
        volume = v.to_dict()
        volume['user'] = user.to_dict if user else ''
        return volume

    @Controller.authorize
    def create(self, action_args):
        context = action_args['context']
        del action_args['context']
        volume = self.db.volume_create(context, action_args)
        return {'group': volume.to_dict()}

    @Controller.authorize
    def update(self, action_args):
        context = action_args.get('context')
        volume = self.db.volume_update(context, action_args)
        return {'group': volume.to_dict()}

    @Controller.authorize
    def delete(self, action_args):
        id = action_args.get('id')
        context = action_args.get('context')
        return self.db.volume_delete(context, id)


class OpLogController(Controller):

    resource_name = 'oplog'

    def index(self, action_args):
        pass

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
        self.resources['reports'] = Resource(ReportController(self.conf))
        self.resources['roles'] = Resource(RoleController(self.conf))
        self.resources['groups'] = Resource(GroupController(self.conf))
        self.resources['oplogs'] = Resource(OpLogController(self.conf))

        self.mapper.resource('task','tasks',
                             controller=self.resources['tasks'],
                             collection={'detail': 'GET'},
                             member={"action": "POST"}
                            )

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

        self.mapper.resource('report', 'reports',
                             controller=self.resources['reports'],
                             member={'generate': 'GET'},
                             collection={'tasks': 'GET'}
                             )

        self.mapper.resource('role', 'roles',
                             controller=self.resources['roles'],
                             collection={'detail': 'GET'})

        self.mapper.resource('group', 'groups',
                             controller=self.resources['groups'],
                             collection={'detail': 'GET'})

        self.resources['volumes'] = Resource(VolumeController(self.conf))
        self.mapper.resource('volume', 'volumes',
                             controller=self.resources['volumes'],
                             collection={'detail': 'GET'})
        self.mapper.resource('oplog', 'oplogs',
                             controller=self.resources['oplogs'])


    def dispatch(self, req):
        environ = req.wsgi_environ
        url = req.path_info
        reqargs = self.mapper.match(url, environ)
        if reqargs:
            controller = reqargs['controller']
            del reqargs['controller']
            reqargs.update(req.params)
            reqargs['CONTENT_TYPE'] = environ.get('CONTENT_TYPE')
            return controller(reqargs, req)
        else:
            logger.error('method is not allowed, %s, %s' % (url, reqargs))
            raise HTTPError(405, 'the url %s  method is not allowed' % url)


