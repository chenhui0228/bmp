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
from oplog import EventManager
from controller import server as bkserver
from cherrypy import NotFound
import logging
logger = logging.getLogger('backup')
from backup_exception import Duplicated, MalformedRequestBody

def action(name):
    def decorator(func):
        func.wsgi_action = name
        return func
    return decorator

_MEDIA_TYPE_MAP = {
    'application/json': 'json',
}

class JSONDeserializer(object):

    def _from_json(self, datastring):
        try:
            return jsontools.loads(datastring)
        except ValueError:
            msg = "cannot understand JSON"
            raise MalformedRequestBody(reason=msg)

    def deserialize(self, datastring):
        return {'body': self._from_json(datastring)}


class Resource(object):
    def __init__(self, controller):
        self.controller = controller
        self.deserialize = JSONDeserializer()

    def __call__(self, reqargs, req):
        action = reqargs['action']
        del reqargs['action']
        username = reqargs['user']
        if isinstance(username, list):
            username = username[0]
        is_usperuser = False
        if username == authentication.superuser.name:
            user = authentication.superuser
            is_usperuser = True
        else:
            user = self.controller.\
                db.get_user_by_name(authentication.super_context, username, with_role=True, with_group=True)

        admin_role = self.controller.admin_role
        context = {
            'is_superuser': is_usperuser,
            'user_id': user.id,
            'username': username,
            'role': user.role.name if not is_usperuser else authentication.superrole.name,
            'group_id': user.group.id if not is_usperuser else 'super_group',
            'group_name': user.group.name if not is_usperuser else 'super_group'
        }
        context['is_admin'] = context.get('role') == admin_role
        reqargs['context'] = context
        logger.debug('context = %s' % context)
        return self._process_stack(req, action, reqargs)

    def _process_stack(self, request, action, action_args):
        content_type = action_args.get('CONTENT_TYPE')
        body = request.body
        if action == 'action':
            body = body.read()
            try:
                contents = self.deserialize.deserialize(body)
            except MalformedRequestBody:
                logger.error('Malformed request body')
                raise HTTPError(400, 'Malformed request body')
            action_args.update(contents)
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
        logger.debug('body : %s' % body)
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
        self.conf = conf
        self.oplogger = EventManager(conf)
        self.admin_role = self.policy.get_admin_role()

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
        tasks, total = self.db.get_tasks(**action_args)
        result = list()
        for p in tasks:
            result.append(p.to_dict())
        return {'total': total, 'tasks': result}


    @Controller.authorize
    @json_out
    def detail(self, action_args):
        logger.info('list tasks with detail ')
        logger.debug('action_args :  %s'% action_args)
        tasks, total = self.db.get_tasks_all(**action_args)
        result = list()

        for t in tasks:
            task = {}
            policy = t.policy
            worker = t.worker
            user = t.user
            task['task'] = t.to_dict()
            if policy:
                task['policy'] = policy.to_dict()
            if worker:
                task['worker'] = worker.to_dict()
            state = self.db.bk_get_latest(t.id)
            if state:
                task['state'] = state.to_dict()
            if user:
                task['user'] = user.name
            result.append(task)
        return {'total': total, 'tasks': result}

    @Controller.authorize
    @json_out
    def show(self, action_args):
        logger.info('get tast  ')
        logger.debug('action_args :  %s'%action_args)
        id = action_args.get('id')
        deleted = action_args.get('deleted')
        context = action_args.get('context')
        msg = 'get a task '
        self.oplogger.log_event(context, msg)
        task = self.db.get_task(context, id, True, deleted)
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
        context = action_args.get('context')
        info = {}
        try:
            name = action_args.get('name')
            task = self.db.task_get_by_name(context, name)
            info['exist'] = 'True'
        except NotFound:
            if not action_args.get('type'):
                action_args['type'] = 'backup'
            context = action_args['context']
            task = self.db.create_task(context, action_args)
            info['exist'] = 'False'
            if task.type == 'backup':
                self.conf['bkserver'].backup(task.id)
            elif task.type == 'recover':
                self.conf['bkserver'].recover(task.id)
            msg = 'create  a {0} task {1} [ {2} ]'.format(task.type, task.name, task.id )
            self.oplogger.log_event(context, msg)
        info['task'] = task.to_dict()
        return info

    @Controller.authorize
    def delete(self, action_args):
        id = action_args.get('id')
        context = action_args['context']
        old =  self.db.delete_task(context, id)
        self.conf['bkserver'].delete(id)
        msg = 'delete the task {0} [ {1} ]'.format(old['name'], old['id'])
        self.oplogger.log_event(context, msg)
        return old

    @Controller.authorize
    def update(self, action_args):
        self._validate_prams(action_args)
        context = action_args['context']
        info = {}
        try:
            task = self.db.update_task(context, action_args)
            self.conf['bkserver'].update_task(task.id)
            info['task'] = task.to_dict()
            info['exist'] = 'False'
            msg = 'update the task {0} [ {1} ]'.format(task.name, task.id)
            self.oplogger.log_event(context, msg)
        except Duplicated:
            info['exist'] = 'True'
        return info

    @Controller.authorize
    @action('start')
    def start(self, action_args):
        context = action_args['context']
        task_id = action_args['id']
        self.conf['bkserver'].backup(task_id, True)
        msg = 'start  the task %s' % action_args['id']
        self.oplogger.log_event(context, msg)
        return 'success'

    @Controller.authorize
    @action('stop')
    def stop(self, action_args):
        context = action_args['context']
        task_id = action_args['id']
        self.conf['bkserver'].stop(task_id)
        msg = 'stop  the task %s' % task_id
        self.oplogger.log_event(context, msg)

    @action('pause')
    @Controller.authorize
    def pause(self, action_args):
        context = action_args['context']
        task_id = action_args['id']
        self.conf['bkserver'].pause(task_id)
        msg = 'pause  the task %s' % task_id
        self.oplogger.log_event(context, msg)

    @Controller.authorize
    @action('resume')
    def resume(self, action_args):
        context = action_args['context']
        task_id = action_args['id']
        self.conf['bkserver'].resume(task_id)
        msg = 'resume the task %s' % task_id
        self.oplogger.log_event(context, msg)


class PoliciesController(Controller):

    resource_name = 'policy'

    @Controller.authorize
    @json_out
    def index(self, action_args):
        context = action_args['context']
        policies , total = self.db.get_policies(**action_args)
        result = list()
        for policy in policies:
            policy_dict = policy.to_dict()
            policy_dict['group'] = context.get('group_name')
            result.append(policy_dict)
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
        policy_name = action_args.get('name')
        policy_info = {}
        try:
            policy = self.db.get_policy_by_name(context, policy_name)
            policy_info['exist']='True'
        except (NotFound, HTTPError):
            policy = self.db.create_policy(context, action_args)
            self.oplogger.log_event(context, 'create a   policy : {0} [ {1} ] '.format(
                policy.name, policy.id))
            policy_info['exist'] = 'False'
        policy_info['policy'] = policy.to_dict()
        return policy_info

    @Controller.authorize
    def delete(self, action_args):
        id =  action_args['id']
        context = action_args['context']
        logger.info('trying to delete policy id = %s'%id)
        tasks, old = self.db.delete_policy(context, id)
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
        msg = 'delete the   policy :  {0} [ {1} ] '.format(
            old['name'], old['id'])
        self.oplogger.log_event(context, msg)

    def update(self, action_args):
        context = action_args['context']
        policy_info = {}
        try:
            policy = self.db.update_policy(context, action_args)
            self.conf['bkserver'].update_policy(policy.id)
            msg = 'update  the   policy : {0} [ {1} ] '.format(
                policy.name, policy.id)
            self.oplogger.log_event(context, msg)
            policy_info['exist'] = 'False'
            policy_info['policy'] = policy.to_dict()
        except Duplicated:
            policy_info['exist'] = 'True'

        return policy_info






class WorkersController(Controller):
    resource_name = 'worker'

    @Controller.authorize
    @json_out
    def index(self, action_args):
        context = action_args['context']
        workers , total = self.db.get_workers(**action_args)
        result = list()
        for worker in workers:
            worker_dict = worker.to_dict()
            worker_dict['group'] = context.get('group_name')
            result.append(worker_dict)
        return {'total': total, 'workers': result}


    @Controller.authorize
    @json_out
    def detail(self, action_args):
        workers , total = self.db.get_workers(detail=True, **action_args)
        result = list()
        for w in workers:
            worker = w.to_dict()
            result.append(worker)
        return {'total': total, 'workers': result}

    @Controller.authorize
    @json_out
    def show(self, action_args):
        id = action_args.get('id')
        context = action_args.get('context')
        action_args.pop('id')
        worker = self.db.get_worker(context, id)
        worker_info = worker.to_dict()
        worker_info['user'] = worker.owner
        task_list = []
        for t in worker.tasks:
            task_list.append(t.to_dict())
        worker_info['tasks'] = task_list
        msg = 'get  a  worker'
        self.oplogger.log_event(context, msg)
        return {'worker': worker_info}

    @Controller.authorize
    def create(self, action_args):
        context = action_args['context']
        worker_name = action_args.get('name')
        worker_info = {}
        try:
            worker = self.db.get_worker_by_name(context, worker_name)
            worker_info['exist']='True'
        except (NotFound, HTTPError):
            worker = self.db.create_worker(context, action_args)
            msg = 'create a  worker : {0} [ {1} ]'.format(
                worker.name, worker.id
            )
            self.oplogger.log_event(context, msg)
            worker_info['exist'] = 'False'
        worker_info['worker'] = worker.to_dict()
        return worker_info

    @Controller.authorize
    def delete(self, action_args):
        id =  action_args['id']
        context = action_args['context']
        tasks, old = self.db.delete_worker(context, id)
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
        msg = 'delete the  worker : {0} [ {1} ]'.format(
            old['name'], old['id']
        )
        self.oplogger.log_event(context, msg)

    @Controller.authorize
    def update(self, action_args):
        context = action_args['context']
        worker_info = {}
        try:
            worker = self.db.update_worker(context, action_args)
            msg = 'update  the   worker : {0} [ {1} ]'.format(
                worker.name, worker.id
            )
            self.oplogger.log_event(context, msg)
            worker_info['exist'] = 'False'
            worker_info['worker'] = worker.to_dict()
        except Duplicated:
            worker_info['exist'] = 'True'

        return worker_info


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
        user_info = {}
        user_name = action_args['name']
        try:
            user = self.db.get_user_by_name(context, user_name)
            user_info['exist'] = 'True'
        except (NotFound, HTTPError):
            user = self.db.create_user(context, action_args)
            msg = 'create  a   user : {0} [ {1} ]'.format(user.name,user.id)
            self.oplogger.log_event(context, msg)
            user_info['exist'] = 'False'
        user_info['user'] = user.to_dict()
        return user_info

    @Controller.authorize
    def delete(self, action_args):
        id = action_args['id']
        context = action_args['context']
        user = self.db.delete_user(context, id)
        if user:
            self.oplogger.log_event(context, 'delete the user {0} [ {1} ]'.format(
                user.get('name'), user.get('id')))


    def update(self, action_args):
        context = action_args['context']
        user_info = {}
        user = self.db.update_user(context, action_args)
        self.oplogger.log_event(context, 'update the user : {0} [ {1} ]'.format(user.name,user.id))
        user_info['user'] = user.to_dict()
        return user_info


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
        role_info = role.to_dict()
        users = role.users
        user_list = []
        for u in users:
            user_list.append(u.to_dict())
        role_info['users'] = user_list
        return role_info

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
        name = action_args.get('name')
        info = {}
        try:
            group = self.db.group_get_by_name(context, name)
            info['exist']='True'
        except (NotFound, HTTPError):
            group = self.db.group_create(context, action_args)
            self.oplogger.log_event(context, 'create a group %s ' % group.id )
            info['exist'] = 'False'
        info['group'] = group.to_dict()
        return info

    @Controller.authorize
    def update(self, action_args):
        context = action_args.get('context')
        info = {}
        try:
            group = self.db.group_update(context, action_args)
            self.oplogger.log_event(context, 'update the group %s ' % group.id)
            info['exist'] = 'False'
            info['group'] = group.to_dict()
        except Duplicated:
            info['exist'] = 'True'

        return info

    @Controller.authorize
    def delete(self, action_args):
        id = action_args.get('id')
        context = action_args.get('context')
        old =  self.db.group_delete(context, id)
        self.oplogger.log_event(context, 'delete the group %s ' % old['id'] )
        return  old


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
        name = action_args['name']
        info = {}
        try:
            volume = self.db.volume_get_by_name(context, name)
            info['exist'] = 'True'
        except (NotFound, HTTPError):
            volume = self.db.volume_create(context, action_args)
            self.oplogger.log_event(context, 'create a volume %s ' % volume.id)
            info['exist'] = 'False'
        info['volume'] = volume.to_dict()
        return info

    @Controller.authorize
    def update(self, action_args):
        context = action_args.get('context')
        name = action_args['name']
        info = {}
        try:
            volume = self.db.volume_update(context, action_args)
            self.oplogger.log_event(context, 'update the volume %s ' % volume.id )
            info['exist'] = 'False'
            info['volume'] = volume.to_dict()
        except Duplicated:
            info['exist'] = 'True'
        return info

    @Controller.authorize
    def delete(self, action_args):
        id = action_args.get('id')
        context = action_args.get('context')
        old = self.db.volume_delete(context, id)
        self.oplogger.log_event(context, 'delete the volume %s ' % old['id'] )
        return old


class OpLogController(Controller):

    resource_name = 'oplog'
    @json_out
    def index(self, action_args):
        logs , total = self.db.oplog_list(**action_args)
        result = list()
        for log in logs:
            result.append(log.to_dict())
        return {'total': total, 'oplogs': result}


class SummaryController(Controller):
    resource_name = 'summary'

    @json_out
    def index(self, action_args):
        context = action_args['context']
        del action_args['context']
        return self.db.summary_list(context, **action_args)


class TagController(Controller):
    resource_name = 'tag'

    @Controller.authorize
    @json_out
    def index(self, action_args):
        tags, total = self.db.tag_list(**action_args)
        tag_list = []
        for tag in tags:
            tag_list.append(tag.to_dict())
        return {'total': total, 'tags': tag_list}


    @Controller.authorize
    @json_out
    def detail(self, action_args):
        tags, total= self.db.tag_detail_list(**action_args)
        tag_list = []
        for tag in tags:
            t = tag.to_dict()
            item_list = t['items'] = []
            for item in tag.tag_items:
                item_list.append(item.to_dict())
            tag_list.append(t)
        return {'total': total, 'tags': tag_list}


    @Controller.authorize
    @json_out
    def show(self, action_args):
        tag_id = action_args.get('id')
        context = action_args.get('context')
        tag = self.db.tag_get(context, tag_id, with_items=True)
        if not tag:
            raise HTTPError(404, 'tag %s is not found ' % tag_id)
        items = tag.tag_items
        tag_dict = tag.to_dict()
        ids = []
        if items:
            item_list = []
            for item in items:
                item_list.append(item.to_dict())
                ids.append(item.item_id)
            tag_dict['items'] = item_list
        task_detail = action_args.get('task_detail')
        if task_detail:
            tasks = self.db.task_list_by_ids(context, ids)
            tasks_by_id = {}
            for task in tasks:
                tasks_by_id[task.id] = task.to_dict()
            for item in item_list:
                item['task'] = tasks_by_id[item['item_id']]
        return tag_dict

    @Controller.authorize
    def create(self, action_args):
        context = action_args.pop('context')
        name = action_args.get('name')
        tag_info = {}
        try:
            tag = self.db.tag_get_by_name(context, name)
            tag_info['exist'] = True
        except (NotFound, HTTPError):
            tag = self.db.tag_create(context, action_args)
            tag_info['exist'] = 'False'
        tag_info['tag'] = tag.to_dict()
        msg = 'create a  tag : {0} [ {1} ] in group {2}'.format(
            tag.name, tag.id, tag.group_id
        )
        self.oplogger.log_event(context, msg)
        return tag_info

    @Controller.authorize
    def update(self, action_args):
        context = action_args.pop('context')
        info = {}
        try:
            tag = self.db.tag_update(context, action_args)
            self.oplogger.log_event(context, 'update the tag %s ' % tag.id)
            info['exist'] = 'False'
            info['volume'] = tag.to_dict()
        except Duplicated:
            info['exist'] = 'True'
        return info

    @Controller.authorize
    @action('add')
    def add(self, action_args):
        context = action_args['context']
        body = action_args['body']
        items = body.get('add')
        tag_id = action_args['id']
        self.db.tag_add(context, tag_id, items)

    @Controller.authorize
    def delete(self, action_args):
        context = action_args.get('context')
        tag_id = action_args.get('id')
        return self.db.tag_delete(context, tag_id)

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

        self.resources['summaries'] = Resource(SummaryController(self.conf))
        self.mapper.resource('summary', 'summaries',
                             controller=self.resources['summaries'])


        self.resources['tags'] = Resource(TagController(self.conf))
        self.mapper.resource('tag', 'tags',
                             controller=self.resources['tags'],
                             collection={'detail': 'GET'},
                             member={"action": "POST"})

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


