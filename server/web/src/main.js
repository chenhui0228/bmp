// The Vue build version to load with the `import` command
// (runtime-only or standalone) has been set in webpack.base.conf with an alias.
import Vue from 'vue'
import App from './App'
import router from './router'
import ElementUI from 'element-ui'
import 'element-ui/lib/theme-default/index.css'
//import '@/assets/iconfont.css'
import '@/assets/styles/main.scss'
import '@/assets/js/iconfont.js'

// import Mock from './mock'
// Mock.init()

Vue.config.productionTip = false
Vue.use(ElementUI)

Vue.filter("timeStamp2datetime", function (value) {
  if(!value) {
    return 'N/A';
  }
  return Vue.prototype.myDateFormat(new Date(value*1000), "yyyy-MM-dd hh:mm:ss");
});
Vue.filter("weeksFormat", function (value) {
  var w = [];
  var weeks = [1, 2, 4, 8, 16, 32, 64];
  for (var i in weeks) {
    if ((value & weeks[i]) == weeks[i]){
      w.push(weeks[i].toString());
    }
  }
  w.sort(function (a,b) {
    return a-b;
  })
  var str = "";
  for (var i in w) {
    switch (w[i]){
      case '1':
        str = str + "一  ";
        break;
      case '2':
        str = str + "二  ";
        break;
      case '4':
        str = str + "三  ";
        break;
      case '8':
        str = str + "四  ";
        break;
      case '16':
        str = str + "五  ";
        break;
      case '32':
        str = str + "六  ";
        break;
      case '64':
        str = str + "日";
        break;
    }
  }
  return str;
});
Vue.filter("pathFilter", function (path) {
  console.log(typeof (path));
  path = path.replace(/^\w+:\//g,'');
  return path;
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
    if (new RegExp("(" + k + ")").test(fmt)) {
      if (k == "y+") {
        fmt = fmt.replace(RegExp.$1, ("" + o[k]).substr(4 - RegExp.$1.length));
      }
      else if (k == "S+") {
        var lens = RegExp.$1.length;
        lens = lens == 1 ? 3 : lens;
        fmt = fmt.replace(RegExp.$1, ("00" + o[k]).substr(("" + o[k]).length - 1, lens));
      }
      else {
        fmt = fmt.replace(RegExp.$1, (RegExp.$1.length == 1) ? (o[k]) : (("00" + o[k]).substr(("" + o[k]).length)));
      }
    }
  }
  return fmt;
};

/* eslint-disable no-new */
new Vue({
  el: '#app',
  router,
  template: '<App/>',
  components: {App}
})
