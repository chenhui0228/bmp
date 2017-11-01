import Vue from 'vue'
import Router from 'vue-router'
import Home from '@/components/Home'
import Dashboard from '@/components/Dashboard'

import BookList from '@/components/book/list'
import BookCategoryList from '@/components/bookcategory/list'

import UserList from '@/components/user/list'
// import User from '@/components/user/user'
import Group from '@/components/user/group'

import UserChangePwd from '@/components/selfinfo/changepwd'
import UserProfile from '@/components/selfinfo/profile'

import Task from '@/components/task/task'

import Policy from '@/components/policy/policy'

import Volume from '@/components/volume/volume'

import Worker from '@/components/worker/worker'

// 懒加载方式，当路由被访问的时候才加载对应组件
const Login = resolve => require(['@/components/Login'], resolve)

Vue.use(Router)

let router = new Router({
// mode: 'history',
  routes: [
    {
      path: '/login',
      name: '登录',
      component: Login
    },
    {
      path: '/',
      name: 'home',
      component: Home,
      redirect: '/dashboard',
      leaf: true, // 只有一个节点
      menuShow: true,
      iconCls: 'iconfont icon-home', // 图标样式class
      children: [
        {path: '/dashboard', component: Dashboard, name: '首页', menuShow: true}
      ]
    },
    {
      path: '/',
      component: Home,
      name: '任务管理',
      menuShow: true,
      leaf: true, // 只有一个节点
      iconCls: 'iconfont icon-task', // 图标样式class
      children: [
        {path: '/task', component: Task, name: '任务管理', menuShow: true}
      ]
    },
    {
      path: '/',
      component: Home,
      name: '策略管理',
      menuShow: true,
      leaf: true, // 只有一个节点
      iconCls: 'iconfont icon-policy', // 图标样式class
      children: [
        {path: '/policy', component: Policy, name: '策略列表', menuShow: true}
      ]
    },
    {
      path: '/',
      component: Home,
      name: '主机管理',
      menuShow: true,
      leaf: true, // 只有一个节点
      iconCls: 'iconfont icon-host', // 图标样式class
      children: [
        {path: '/worker', component: Worker, name: '主机列表', menuShow: true}
      ]
    },
    {
      path: '/',
      component: Home,
      name: '卷管理',
      menuShow: true,
      leaf: true, // 只有一个节点
      iconCls: 'iconfont icon-volume', // 图标样式class
      children: [
        {path: '/volume', component: Volume, name: '卷列表', menuShow: true}
      ]
    },
    // {
    //   path: '/',
    //   component: Home,
    //   name: '图书管理',
    //   menuShow: true,
    //   iconCls: 'iconfont icon-books',
    //   children: [
    //     {path: '/book/list', component: BookList, name: '图书列表', menuShow: true},
    //     {path: '/book/category', component: BookCategoryList, name: '图书分类', menuShow: true}
    //   ]
    // },
    {
      path: '/',
      component: Home,
      name: '用户管理',
      menuShow: true,
      iconCls: 'iconfont icon-userMgr',
      children: [
        // {path: '/user', component: User, name: '用户', menuShow: true},
        {path: '/user/list', component: UserList, name: '用户列表', menuShow: true},
        {path: '/user/group', component: Group, name: '组列表', menuShow: true}
      ]
    },
    {
      path: '/',
      component: Home,
      name: '个人信息',
      menuShow: false,
      iconCls: 'iconfont icon-user',
      children: [
        // {path: '/user', component: User, name: '用户', menuShow: true},
        {path: '/selfinfo/profile', component: UserProfile, name: '个人信息', menuShow: true},
        {path: '/selfinfo/changepwd', component: UserChangePwd, name: '修改密码', menuShow: true}
      ]
    }
  ]
})

router.beforeEach((to, from, next) => {
  // console.log('to:' + to.path)
  if (to.path.startsWith('/login')) {
    window.sessionStorage.removeItem('access-user')
    next()
  } else {
    let user = JSON.parse(window.sessionStorage.getItem('access-user'))
    if (!user) {
      next({path: '/login'})
    } else {
      next()
    }
  }
})

export default router
