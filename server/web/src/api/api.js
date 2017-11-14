/**
 * Created by 01107267 on 2017/10/31.
 */
import axios from 'axios'
import Qs from 'qs'

let base = 'https://10.202.127.11:443'

axios.defaults.headers.post['Content-Type'] = 'application/x-www-form-urlencoded;charset=UTF-8';
axios.defaults.headers.put['Content-Type'] = 'application/x-www-form-urlencoded;charset=UTF-8';
//请求时的拦截
axios.interceptors.request.use((config) => {
  // console.log('config:');
  // console.log(config);
  let url = config.url;
  if(config.method  === 'post' || config.method  === 'put'){
    config.data = Qs.stringify(config.data);
  }
  if (url.indexOf("login") < 0 ){
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
},error => {
  alert("error");
});

export const requestLogin = params => { return axios.post(`${base}/login`, params).then(res => res) }

export const reqGetUserProfile = params => { return axios.get(`${base}/backup/users`, { params: params }).then(res => res) }

export const reqUpdateUserProfile = params => { return axios.put(`${base}/backup/users/${params.id}`, params, {params: {user: params.name}}).then(res => res) }

export const reqGetRoleList = params => { return axios.get(`${base}/backup/roles`, { params: params }) }

//policy
export const reqGetPolicyList = params => { return axios.get(`${base}/backup/policies`, { params: params }) }


//组列表相关API开始
export const reqGetGroupList = params => { return axios.get(`${base}/backup/groups`, { params: params }) }

export const reqGetGroupDetail = (group_id,params) =>{ return axios.get(`${base}/backup/groups/${group_id}`, { params: params }) }

export const reqEditGroup = (group_id,user,params) => { return axios.put(`${base}/backup/groups/${group_id}`, params, { params: user}) }

export const reqAddGroup = (user,params) => { return axios.post(`${base}/backup/groups`,  params, { params: user}) }

export const reqDelGroup = (group_id,params) => { return axios.delete(`${base}/backup/groups/${group_id}`, { params: params }) }
//组列表相关API结束

//主机管理相关
export const reqGetWorkerList = params => { return axios.get(`${base}/backup/workers`, { params: params }) }

export const reqEditWorker = (worker_id,user,params) => { return axios.put(`${base}/backup/workers/${worker_id}`,params,{params: user}) }

export const reqAddWorker = (user,params) => { return axios.post(`${base}/backup/workers`, params, {params: user}) }

export const reqDelWorker = (worker_id,params) => { return axios.delete(`${base}/backup/workers/${worker_id}`, { params: params }) }
//主机管理相关结束

export const reqGetBookListPage = params => { return axios.get(`${base}/book/list`, { params: params }) }

export const reqDeleteBook = params => { return axios.get(`${base}/book/delete`, { params: params }) }

export const reqEditBook = params => { return axios.get(`${base}/book/edit`, { params: params }) }

export const reqBatchDeleteBook = params => { return axios.get(`${base}/book/batchdelete`, { params: params }) }

export const reqAddBook = params => { return axios.get(`${base}/book/add`, { params: params }) }
