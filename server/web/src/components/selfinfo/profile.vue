<template>
  <el-row class="warp">
    <el-col :span="24" class="warp-breadcrum">
      <el-breadcrumb separator="/">
        <el-breadcrumb-item :to="{ path: '/' }"><b>首页</b></el-breadcrumb-item>
        <el-breadcrumb-item>个人信息</el-breadcrumb-item>
      </el-breadcrumb>
    </el-col>

    <el-col :span="24" class="warp-main">
      <el-form ref="form" :model="form" :rules="rules" label-width="80px">
        <el-form-item label="用户名">
          <el-input v-model="form.name" disabled></el-input>
        </el-form-item>
        <el-form-item prop="role" label="角色" >
          <el-radio-group v-model="form.role">
            <el-radio :label="0" :disabled="isSuperAdm">超级管理员</el-radio>
            <el-radio :label="1">角色2</el-radio>
            <el-radio :label="2">角色3</el-radio>
            <el-radio :label="3">角色4</el-radio>
            <el-radio :label="4">角色5</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item prop="group" label="用户组">
          <template>
            <el-radio class="radio" v-model="form.group" :label="0">ALL</el-radio>
            <el-radio class="radio" v-model="form.group" :label="1">网络组</el-radio>
            <el-radio class="radio" v-model="form.group" :label="2">存储组</el-radio>
            <el-radio class="radio" v-model="form.group" :label="3">数据库组</el-radio>
            <el-radio class="radio" v-model="form.group" :label="4">系统组</el-radio>
          </template>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="onSubmit">修改并保存</el-button>
        </el-form-item>
      </el-form>
    </el-col>
  </el-row>
</template>

<script>
  import {reqSaveUserProfile} from '../../api/api';
  import {reqGetUserProfile} from '../../api/api';
  import {bus} from '../../bus.js'
  import export2Excel from '../../common/export2Excel'
  export default {
    data() {
      return {
        form: {
          name: '',
          role: 0,
          group: 0
        },
        isSuperAdm: false,
        rules: {

        },
      }
    },
    created(){

    },
    methods: {

      onSubmit() {
        var that = this;
        /**this.$refs.form.validate((valid) => {
          if (valid) {
            var args = {name: this.form.name, email: this.form.email};
            reqSaveUserProfile(args).then(function (data) {
              let {msg, code, user} = data;
              if (code !== 200) {
                that.$message({
                  message: msg,
                  type: 'error'
                });
              } else {
                sessionStorage.setItem('access-user', JSON.stringify(user));
                bus.$emit('setUserName', user.name);
                that.$message({
                  message: "修改成功！",
                  type: 'success',
                  duration: 2000 //默认3s太长
                });
              }
            })
          } else {
            console.log('error submit!!');
            return false;
          }
        });*/
      },
      getUserProfile(user){
        reqGetUserProfile(user).then(res => {
          let { status, data } = res;
          if (data == null) {
            this.$message({
              message: "未获取到信息",
              type: 'error'
            });
          } else {
              export2Excel.export2Excel(data.users, "test", "user");
          }
        },err => {
          if (err.response.status == 401) {
            this.$message({
              message: "请重新登陆",
              type: 'error'
            });
            sessionStorage.removeItem('access-user');
            this.$router.push({ path: '/' });
          } else {
            this.$message({
              message: "请求异常",
              type: 'error'
            });
          }
        });
      }
    },
    mounted() {
      var accessInfo = sessionStorage.getItem('access-user');
      var username = JSON.parse(accessInfo).username;
      console.log(username);
      let user = {
        user: username
      };
      this.getUserProfile(user)

      /*if (user) {
        user = JSON.parse(user);
        this.form.name = user.name;
        this.form.role = user.role;
        this.form.group = user.group;
        if (this.form.role == 0) {
          this.isSuperAdm = false;
        }
      }*/
    }
  }
</script>
