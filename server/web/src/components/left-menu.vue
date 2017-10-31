<template>
    <el-menu class="el-menu-vertical" theme="dark" :default-active="$route.path" :router="true">
        <!--<el-submenu index="1">-->
            <!--<template slot="title"><i class="el-icon-setting"></i>任务管理</template>-->
            <!--&lt;!&ndash;<el-submenu-item>&ndash;&gt;-->
                <!--&lt;!&ndash;<el-menu-item index="1-1">备份任务</el-menu-item>&ndash;&gt;-->
                <!--&lt;!&ndash;<el-menu-item index="1-2">备份策略</el-menu-item>&ndash;&gt;-->
            <!--&lt;!&ndash;</el-submenu-item>&ndash;&gt;-->
        <!--</el-submenu>-->
        <!--<el-submenu index="2">-->
            <!--<template slot="title"><i class="el-icon-message"></i>策略管理</template>-->
        <!--</el-submenu>-->
        <!--<el-submenu index="3">-->
            <!--<template slot="title"><i class="el-icon-setting"></i>卷管理</template>-->
        <!--</el-submenu>-->
        <!--<el-submenu index="4">-->
            <!--<template slot="title"><i class="el-icon-document"></i>日志管理</template>-->
        <!--</el-submenu>-->
        <!--<el-submenu index="5">-->
            <!--<template slot="title"><i class="el-icon-setting"></i>用户管理</template>-->
        <!--</el-submenu>-->
        <el-submenu index="1">
            <template slot="title"><i class="el-icon-setting"></i>任务</template>
            <el-menu-item index="/task">备份</el-menu-item>
            <el-menu-item index="/">恢复备份</el-menu-item>
        </el-submenu>
        <el-menu-item index="2"><i class="el-icon-message"></i>策略</el-menu-item>
        <el-menu-item index="3"><i class="el-icon-message"></i>卷</el-menu-item>
        <el-menu-item index="4"><i class="el-icon-document"></i>工作机</el-menu-item>
        <el-menu-item index="5"><i class="el-icon-document"></i>日志</el-menu-item>
        <el-menu-item index="6"><i class="el-icon-setting"></i>用户</el-menu-item>
    </el-menu>
</template>
<style type="text/css">
    .el-menu-vertical-demo {
     background-color: #373D41;
    }
    .glyphicon {

    }
</style>
<script>

</script>
