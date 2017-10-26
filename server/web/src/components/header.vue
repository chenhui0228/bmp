<template>
    <nav class="navbar navbar-inverse navbar-fixed-top" style="border-radius: 0px;">
        <div class="container-fluid">
            <div class="navbar-header">
                <a class="navbar-brand" href="#"><img alt="Brand" src="../assets/imgs/configuration-1.png" class="navbar-brand-img"></a>
            </div>
            <div class="collapse navbar-collapse" id="bs-example-navbar-collapse-1">
                <ul class="nav navbar-nav">
                    <li class="navbar-text"><a href="javascript:void(0);" class="navbar-link"><router-link class="nav-item" to="/task">任务管理</router-link></a></li>
                    <!--<li class="navbar-text"><a href="javascript:void(0);" class="navbar-link"><router-link class="nav-item" to="/policy">策略管理</router-link></a></li>-->
                    <!--<li class="navbar-text"><a href="javascript:void(0);" class="navbar-link"><router-link class="nav-item" to="/user">用户管理</router-link></a></li>-->
                </ul>
                <ul class="nav navbar-nav navbar-right">
                    <!--<li class="navbar-text"><a href="javascript:void(0);" class="a-self navbar-link"><router-link class="nav-item" to="/">01107267</router-link></a></li>-->
                    <!--<li class="navbar-text"><a href="javascript:void(0);" class="a-self navbar-link"><router-link class="nav-item" to="/">退出</router-link></a></li>-->
                </ul>
            </div>
        </div>
    </nav>
</template>
<style type="text/css">
    .navbar {
        background-color: #373D41;
        border-color: #080808;
        position: relative;
        min-height: 50px;
        border: 1px solid transparent;
    }
    .navbar-brand-img {
        height: 28px;
    }
    .navbar-text {
        margin-top: 3px;
        margin-bottom: 0px;
        font-family: "Noto Sans",'Microsoft Yahei',SimSun;
        -webkit-font-smoothing: antialiased;
        margin-right: 0px!important;
        margin-left: 0px!important;
    }
    a {
        color: #FFFFFF!important;
        text-decoration: none;
    }
    a:hover {
        color: #08F1F3!important;
        text-decoration: none;
    }
    a a:focus {
        color: #08F1F3!important;
        text-decoration: underline;
    }
    .a-self .navbar-link :focus{
        color: #08F1F3!important;
        text-decoration: none;
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
