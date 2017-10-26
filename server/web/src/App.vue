<!--App.vue是项目入口文件。-->
<style>
    .func-row {
        margin-bottom: 10px;
    }
</style>
<template>
    <div id="app-container">
        <div><header-tab></header-tab></div>
        <div class="container-fluid">
            <router-view></router-view>
        </div>
    </div>
</template>

<script>
import HeaderTab from './components/header.vue';
import _global from './Global.vue';
export default {
    name: 'app-container',
    data () {
        return {
            msg: ''
        }
    },
    components:{
        'header-tab': HeaderTab
    }
}
</script>

