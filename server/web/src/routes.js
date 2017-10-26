/**
 * Created by 01107267 on 2017/8/7.
 */
// 引用模板
import Vue from 'vue';
import VueRouter from 'vue-router';

import 'element-ui/lib/theme-default/index.css';

//import headerPage from './components/header.vue';
import taskPage from './views/task.vue';
import policyPage from './views/policy.vue';
import userPage from './views/user.vue';

Vue.use(VueRouter);


export default new VueRouter({
    routes:[
        {
            path:'/',
            component:taskPage
        },
        {
            path:'/task',
            component:taskPage
        },
        {
            path:'/policy',
            component:policyPage
        },
        {
            path:'/user',
            component:userPage
        }
    ]
});
