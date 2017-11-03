/**
 * Created by 01107267 on 2017/10/31.
 */
import axios from 'axios'

let base = ''

export const requestLogin = params => { return axios.post(`${base}/login`, params).then(res => res.data) }

export const reqSaveUserProfile = params => { return axios.post(`${base}/selfinfo/profile`, params).then(res => res.data) }

export const reqGetUserList = params => { return axios.get(`${base}/user/list`, { params: params }) }

export const reqGetGroupList = params => { return axios.get(`${base}/user/group`, { params: params }) }

//主机管理相关
export const reqGetWorkerList = params => { return axios.get(`${base}/worker/list`, { params: params }) }

export const reqEditWorker = params => { return axios.get(`${base}/worker/edit`, { params: params }) }

export const reqAddWorker = params => { return axios.get(`${base}/worker/add`, { params: params }) }

export const reqDelWorker = params => { return axios.get(`${base}/worker/delete`, { params: params }) }

export const reqBatchDelWorker = params => { return axios.get(`${base}/worker/batchdelete`, { params: params }) }
//主机管理相关结束
export const reqGetBookListPage = params => { return axios.get(`${base}/book/list`, { params: params }) }

export const reqDeleteBook = params => { return axios.get(`${base}/book/delete`, { params: params }) }

export const reqEditBook = params => { return axios.get(`${base}/book/edit`, { params: params }) }

export const reqBatchDeleteBook = params => { return axios.get(`${base}/book/batchdelete`, { params: params }) }

export const reqAddBook = params => { return axios.get(`${base}/book/add`, { params: params }) }
