<template>
    <el-row style="border-bottom: 1px solid hsla(0,0%,100%,.15);">
        <el-col :span="4">
            <div class="grid-content bg-purple-dark">
                <a class="navbar-brand" href="#"><img alt="Brand" src="../assets/imgs/configuration-1.png" class="navbar-brand-img"></a>
                <!--文件备份管理平台-->
            </div>
        </el-col>
        <el-col :span="17">
            <div class="grid-content bg-purple-dark"></div>
        </el-col>
        <el-col :span="3">
            <div class="grid-content bg-purple-dark">
                <el-menu theme="dark" :default-active="activeIndex" class="el-menu" mode="horizontal" @select="handleSelect">
                    <el-menu-item index="1">01107267</el-menu-item>
                    <el-menu-item index="2">退出</el-menu-item>
                </el-menu>
            </div>
        </el-col>
    </el-row>
</template>
<style type="text/css">
    a {
        color: #FFFFFF!important;
        text-decoration: none;
    }
    .navbar-brand-img {
        height: 28px;
    }
    .navbar-brand {
        float: left;
        height: 53px;
        padding-top: 13px;
        padding-left: 20px;
        font-size: 18px;
        line-height: 20px;
    }

    a:hover {
        color: #08F1F3!important;
        text-decoration: none;
    }
    a a:focus {
        color: #08F1F3!important;
        text-decoration: underline;
    }

    .el-menu--horizontal .el-menu-item {
        float: left;
        height: 53px;
        line-height: 53px;
        margin: 0;
        cursor: pointer;
        position: relative;
        box-sizing: border-box;
         border-bottom: 5px solid transparent;
    }

    * {
        margin: 0;
        padding: 0;
    }
    *, :after, :before{
        box-sizing: border-box;
    }
</style>
<script>

</script>
