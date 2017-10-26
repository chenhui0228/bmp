/**
 * Created by 01107267 on 2017/8/7.
 */
//main.js这是项目的核心文件。全局的配置都在这个文件里面配置
import  'jquery/dist/jquery.min.js'
import 'bootstrap/dist/css/bootstrap.min.css'
import 'bootstrap/dist/js/bootstrap.min.js'

import Vue from 'vue'
import App from './App.vue'
import Global from './Global.vue'
import ElementUI from 'element-ui';
import axios from 'axios'
import VueAxios from 'vue-axios'
import Qs from 'qs'
import router from './routes.js'

axios.defaults.timeout = 5000;

//axios.defaults.baseURL = 'http://10.202.127.11:8089';
axios.defaults.headers.post['Content-Type'] = 'application/x-www-form-urlencoded;charset=UTF-8';
axios.defaults.headers.put['Content-Type'] = 'application/x-www-form-urlencoded;charset=UTF-8';
//请求时的拦截
axios.interceptors.request.use((config) => {
    if(config.method  === 'post' || config.method  === 'put'){
        config.data = Qs.stringify(config.data);
    }
    return config;
},error => {
    alert("error");
});

// router.beforeEach(({meta, path}, from, next) => {
//     var { auth = true } = meta
//     var isLogin = Boolean(store.state.user.id) //true用户已登录， false用户未登录
//
//     if (auth && !isLogin && path !== '/login') {
//         return next({ path: '/login' })
//     }
//     next()
// })

Vue.config.devtools = true;
Vue.config.debug = true;//开启错误提示
Vue.use(ElementUI);
// Vue.use(VueResource)
Vue.use(VueAxios, axios);
// Vue.use(Qs)
Vue.prototype.GLOBAL = Global;
Vue.prototype.Axios = axios;
Vue.filter("timeStamp2datetime", function (value) {
    return Vue.prototype.myDateFormat(new Date(value), "yyyy-MM-dd hh:mm:ss");
});
Vue.filter("dateStampFormat", function (value) {
    var _date = new Date(value);
    if (value == 0 || value == '0' || _date == undefined){
        return "-";
    }
    var _datetime = Vue.prototype.myDateFormat(_date,"yyyy-MM-dd hh:mm:ss");
    return _datetime;
});
Vue.filter("Bytes", function (bytes) {
    if (bytes === 0) return '0 B';
    let k = 1024, // or 1024
        sizes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'],
        i = Math.floor(Math.log(bytes) / Math.log(k));
    return (bytes / Math.pow(k, i)).toPrecision(3) + ' ' + sizes[i];
});
Vue.filter("getStateByTask",function (value) {
    axios.get(Vue.prototype.GLOBAL.url+"/backup/policies",{
        params: {
            task_id: value,
            limit: 1,
        }
    })
    .then(res => {
        var tasks  = res.data.tasks;


    },err => {
        console.log(err.response.status);
        this.tabLoading = false;
        this.openMsg('请求错误', 'warning')
    })
    .catch(function(response) {
        console.log(response);
    });
});

Vue.prototype.myDateFormat = function (date, fmt) {
    var o = {
        "y+": date.getFullYear(),
        "M+": date.getMonth() + 1,                 //月份
        "d+": date.getDate(),                    //日
        "h+": date.getHours(),                   //小时
        "m+": date.getMinutes(),                 //分
        "s+": date.getSeconds(),                 //秒
        "q+": Math.floor((date.getMonth() + 3) / 3), //季度
        "S+": date.getMilliseconds()             //毫秒
    };
    for (var k in o) {
        if (new RegExp("(" + k + ")").test(fmt)){
            if(k == "y+"){
                fmt = fmt.replace(RegExp.$1, ("" + o[k]).substr(4 - RegExp.$1.length));
            }
            else if(k=="S+"){
                var lens = RegExp.$1.length;
                lens = lens==1?3:lens;
                fmt = fmt.replace(RegExp.$1, ("00" + o[k]).substr(("" + o[k]).length - 1,lens));
            }
            else{
                fmt = fmt.replace(RegExp.$1, (RegExp.$1.length == 1) ? (o[k]) : (("00" + o[k]).substr(("" + o[k]).length)));
            }
        }
    }
    return fmt;
};


new Vue({
    router,
    el: '#app',
    render: h => h(App)
})
