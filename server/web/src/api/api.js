/**
 * Created by 01107267 on 2017/10/31.
 */
import axios from 'axios'
import Qs from 'qs'

let base = 'https://10.202.127.11:443';
let ansible_url = 'http://10.202.235.198:8083';

function get_base_url() {
  base = localStorage.getItem('ApiUrl');
  ansible_url = localStorage.getItem('AnsibleApiUrl');
}

axios.defaults.headers.post['Content-Type'] = 'application/x-www-form-urlencoded;charset=UTF-8';
axios.defaults.headers.put['Content-Type'] = 'application/x-www-form-urlencoded;charset=UTF-8';
//请求时的拦截
axios.interceptors.request.use((config) => {
  let url = config.url;
  if (config.method === 'post' || config.method === 'put') {
    if (typeof (config.data) != "string") {
      config.data = Qs.stringify(config.data);
    }
  }
  if (url.indexOf("login") < 0) {
    // console.log(config.method);
    let accessInfo = sessionStorage.getItem('access-user');
    if (accessInfo) {
      accessInfo = JSON.parse(accessInfo);
      const token = accessInfo.token || '';
      config.headers.Authorization = `Bearer ${token}`
    }
  }
  // console.log(config);
  return config;
}, error => {
  alert("error");
});

export const requestLogin = params => {
  get_base_url()
  return axios.post(`${base}/login`, params)
}

//获取用户列表
export const reqGetUserList = params => {
  get_base_url()
  return axios.get(`${base}/backup/users/detail`, {params: params})
}

//添加用户
export const reqPostUser = (params, data) => {
  get_base_url()
  return axios.post(`${base}/backup/users`, data, {params: params})
}

//修改用户
export const reqPutUser = (params, data) => {
  get_base_url()
  return axios.put(`${base}/backup/users/${data.id}`, data, {params: params})
}

//删除用户
export const reqDelUser = (params, id) => {
  get_base_url()
  return axios.delete(`${base}/backup/users/${id}`, {params: params})
}

//个人信息获取
export const reqGetUserProfile = (params, uid) => {
  get_base_url()
  return axios.get(`${base}/backup/users/${uid}`, {params: params})
}

//个人信息修改
export const reqUpdateUserProfile = (params, data) => {
  get_base_url()
  return axios.put(`${base}/backup/users/${data.id}`, data, {params: params})
}

//获取角色列表
export const reqGetRoleList = params => {
  get_base_url()
  return axios.get(`${base}/backup/roles`, {params: params})
}

//policy
export const reqGetPolicyList = params => {
  get_base_url()
  return axios.get(`${base}/backup/policies/detail`, {params: params})
}
export const reqPostPolicy = (params, data) => {
  get_base_url()
  return axios.post(`${base}/backup/policies`, data, {params: params})
}
export const reqPutPolicy = (params, data) => {
  get_base_url()
  return axios.put(`${base}/backup/policies/${data.id}`, data, {params: params})
}
export const reqDelPolicy = (params, id) => {
  get_base_url()
  return axios.delete(`${base}/backup/policies/${id}`, {params: params})
}


//组列表相关API开始
export const reqGetGroupList = params => {
  get_base_url()
  return axios.get(`${base}/backup/groups`, {params: params})
}

export const reqGetGroupDetail = (group_id, params) => {
  get_base_url()
  return axios.get(`${base}/backup/groups/${group_id}`, {params: params})
}

export const reqEditGroup = (group_id, user, params) => {
  get_base_url()
  return axios.put(`${base}/backup/groups/${group_id}`, params, {params: user})
}

export const reqAddGroup = (user, params) => {
  get_base_url()
  return axios.post(`${base}/backup/groups`, params, {params: user})
}

export const reqDelGroup = (group_id, params) => {
  get_base_url()
  return axios.delete(`${base}/backup/groups/${group_id}`, {params: params})
}
//组列表相关API结束

//主机管理相关
export const reqGetWorkerList = params => {
  get_base_url()
  return axios.get(`${base}/backup/workers/detail`, {params: params})
}

export const reqEditWorker = (worker_id, user, params) => {
  get_base_url()
  return axios.put(`${base}/backup/workers/${worker_id}`, params, {params: user})
}

export const reqAddWorker = (user, params) => {
  get_base_url()
  return axios.post(`${base}/backup/workers`, params, {params: user})
}

export const reqDelWorker = (worker_id, params) => {
  get_base_url()
  return axios.delete(`${base}/backup/workers/${worker_id}`, {params: params})
}
//主机管理相关结束

//卷管理相关开始
export const reqGetVolumeList = params => {
  get_base_url()
  return axios.get(`${base}/backup/volumes`, {params: params})
}

export const reqEditVolume = (volume_id, user, params) => {
  get_base_url()
  return axios.put(`${base}/backup/volumes/${volume_id}`, params, {params: user})
}

export const reqAddVolume = (user, params) => {
  get_base_url()
  return axios.post(`${base}/backup/volumes`, params, {params: user})
}

export const reqDelVolume = (volume_id, params) => {
  get_base_url()
  return axios.delete(`${base}/backup/volumes/${volume_id}`, {params: params})
}
//卷管理相关结束

//任务管理相关
export const reqGetTaskDetailList = params => {
  get_base_url()
  return axios.get(`${base}/backup/tasks/detail`, {params: params})
};

export const reqGetTaskList = params => {
  get_base_url()
  return axios.get(`${base}/backup/tasks`, {params: params})
};

export const reqEditTask = (task_id, user, params) => {
  get_base_url()
  return axios.put(`${base}/backup/tasks/${task_id}`, params, {params: user})
};

export const reqAddTask = (user, params) => {
  get_base_url()
  return axios.post(`${base}/backup/tasks`, params, {params: user})
};

export const reqDelTask = (task_id, params) => {
  get_base_url()
  return axios.delete(`${base}/backup/tasks/${task_id}`, {params: params})
};

export const reqTaskAction = (task_id, data, params, headers) => {
  get_base_url()
  return axios.post(`${base}/backup/tasks/${task_id}/action`, data, {params: params, headers: headers})
};

//任务管理相关结束

//任务状态
export const reqBackupStates = params => {
  get_base_url()
  return axios.get(`${base}/backup/backupstates`, {params: params})
};

export const reqBackupStatesDetail = params => {
  get_base_url()
  return axios.get(`${base}/backup/backupstates/detail`, {params: params})
};

//日志管理
export const reqGetOplogList = params => {
  get_base_url()
  return axios.get(`${base}/backup/oplogs`, {params: params})
};

export const reqGetSummaries = params => {
  get_base_url()
  return axios.get(`${base}/backup/summaries`, {params: params})
};


//TODO: 标签管理接口
export const reqGetTags = params => {
  get_base_url()
  return axios.get(`${base}/backup/tags/detail`, {params: params})
};

export const reqNewTags = (params, data) => {
  get_base_url()
  return axios.post(`${base}/backup/tags`, data, {params: params})
};

export const reqEditTags = (id, params, data) => {
  get_base_url()
  return axios.put(`${base}/backup/tags/${id}`, data, {params: params})
};

export const reqDeleteTags = (id, params) => {
  get_base_url()
  return axios.delete(`${base}/backup/tags/${id}`, {params: params})
};

export const reqAnsible = params => {
  get_base_url()
  return axios.post(`${ansible_url}/vishnu/task_execute`, params)
};
