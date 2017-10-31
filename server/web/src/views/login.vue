<style>
    .el-row {
        margin-bottom: 20px;
    &:last-child {
         margin-bottom: 0;
     }
    }
    .el-col {
        border-radius: 4px;
    }
    .grid-content {
        border-radius: 4px;
        min-height: 36px;
    }
    .row-bg {
        padding: 10px 0;
        background-color: #f9fafc;
    }
</style>

<template>
    <el-row :gutter="5">
        <el-col :xs="1" :sm="5" :md="6" :lg="9" :xl="11">
            <div class="grid-content"></div>
        </el-col>
        <el-col :xs="22" :sm="14" :md="12" :lg="6" :xl="2">
            <el-form :model="userInfo" :rules="rules" ref="loginForm" label-width="100px">
                <el-form-item label="账号" prop="username">
                    <el-input type="text" placeholder="请输入账号" v-model="userInfo.username" autoComplete="false"></el-input>
                </el-form-item>
                <el-form-item label="密码" prop="password">
                    <el-input size="medium" type="password" placeholder="请输入密码" v-model="userInfo.password" autoComplete="false"></el-input>
                </el-form-item>
                <el-form-item>
                    <el-checkbox name="type" v-model="userInfo.remember"></el-checkbox>
                    <span>记住密码</span>
                </el-form-item>
                <el-form-item>
                    <el-button type="primary" @click="login('loginForm')">提交</el-button>
                    <el-button @click="resetForm('loginForm')">重置</el-button>
                </el-form-item>
            </el-form>
        </el-col>
        <el-col :xs="1" :sm="5" :md="6" :lg="9" :xl="11">
            <div class="grid-content"></div>
        </el-col>
    </el-row>
</template>

<script>
    import ElCol from "element-ui/packages/col/src/col";

    export default {
        components: {ElCol},
        data() {
            return {
                userInfo: {
                    username: '',
                    password: '',
                    remember: false
                },
                rules : {
                    username : [
                        { required: true, message: '请输入用户名', trigger: 'blur' }
                    ],
                    password : [
                        { required: true, message: '请输入密码', trigger: 'blur' }
                    ]
                }
            };
        },
        methods: {
            login(formName){
                this.$refs[formName].validate((valid) => {
                    if (valid) {
                        alert('登录成功');
                        this.$router.push('/task')
                    } else {
                        alert('error submit!!');
                        return false;
                    }
                });
            },
            resetForm(formName) {
                this.$refs[formName].resetFields();
            }
        }
    }
</script>