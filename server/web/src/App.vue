<!--App.vue是项目入口文件。-->
<style>
    .func-row {
        margin-bottom: 10px;
    }
    .container-fluid {
       margin-left: 0px;
       margin-fight: 0px;
    }
    .row .header-tab {
        margin-left: -15px;
        margin-right: -15px;
    }
    .el-row {
        /*margin-bottom: 20px;*/
        &:last-child {
          margin-bottom: 0;
        }
    }
    .el-col {
        /*border-radius: 4px;*/
    }
    .bg-purple-dark {
        background: #324157;
    }
    .bg-purple {
        background: #d3dce6;
    }
    .bg-purple-light {
        background: #e5e9f2;
    }
    .grid-content {
        /*border-radius: 4px;*/
        min-height: 53px;
    }
    .row-bg {
        padding: 10px 0;
        background-color: #f9fafc;
    }

</style>
<template>
    <div id="app-container" class="container-fluid" style="padding-left: 0px; padding-right:0px;">
        <header-tab></header-tab>
        <el-row>
            <el-col :span="3" style="background-color: #324157; min-height: 900px;">
                <left-menu></left-menu>
            </el-col>
            <el-col :span="21">
                <router-view></router-view>
            </el-col>
        </el-row>
    </div>
</template>

<script>
import HeaderTab from './components/header.vue';
import LeftMenu from './components/left-menu.vue';
import _global from './Global.vue';
export default {
    name: 'app-container',
    data () {
        return {
            msg: ''
        }
    },
    components:{
        'header-tab': HeaderTab,
        'left-menu' : LeftMenu
    }
}


</script>

