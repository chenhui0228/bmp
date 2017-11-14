<template>
  <el-row class="warp">
    <el-col :span="24" class="warp-breadcrum">
      <el-breadcrumb separator="/">
        <el-breadcrumb-item :to="{ path: '/' }"><b>首页</b></el-breadcrumb-item>
        <el-breadcrumb-item>修改密码</el-breadcrumb-item>
      </el-breadcrumb>
    </el-col>

    <el-col :span="24" class="warp-main">
      <el-form ref="form" :model="form" :rules="rules" label-width="120px">
        <el-form-item label="新密码" prop="newPwd">
          <el-input type="password" v-model="form.newPwd"></el-input>
        </el-form-item>
        <el-form-item label="确认新密码" prop="confirmPwd">
          <el-input type="password" v-model="form.confirmPwd"></el-input>
        </el-form-item>
        <el-form-item>
          <el-button type="default" @click="submitUserProfile">提交</el-button>
        </el-form-item>
      </el-form>
    </el-col>
  </el-row>
</template>

<script>
  import {reqGetUserProfile,reqUpdateUserProfile} from '../../api/api';
  export default{
    data(){
      var validatePass = (rule, value, callback) => {
        if (value === '') {
          callback(new Error('请输入密码'));
        } else {
          if (this.form.newPwd !== '') {
            //this.$refs.form.validateField('newPwd');
          }
          callback();
        }
      };
      var validatePass2 = (rule, value, callback) => {
        if (value === '') {
          callback(new Error('请再次输入密码'));
        } else if (value !== this.form.newPwd) {
          callback(new Error('两次输入密码不一致!'));
        } else {
          callback();
        }
      };
      return {
        form: {
          newPwd: '',
          confirmPwd: ''
        },
        user: {},
        rules: {
          newPwd: [{ validator: validatePass, trigger: 'blur'}],
          confirmPwd: [{validator: validatePass2, trigger: 'blur'}]
        }
      }
    },
    methods:{
      getUserProfile(username){
        let params = {
          user: username,
          name: username
        };
        reqGetUserProfile(params).then(res => {
          let { status, data } = res;
          if (data == null) {
            this.$message({
              message: "未获取到信息",
              type: 'error'
            });
          } else {
            this.user = data.users[0];
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
      },
      submitUserProfile(){
        this.user.password = this.form.newPwd;
        let params = {
          user: this.user.name,
          userProfile: this.user
        }
        reqUpdateUserProfile(this.user).then(res => {
          let { status, data } = res;
          if (data == null) {
            this.$message({
              message: "修改失败！",
              type: 'error'
            });
          } else {
            this.$message({
                message: "修改成功！",
                type: 'success'
            });
            this.user = data.user;
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

      },
      onSubmit() {
        this.$message({message:"此功能暂时未开发",duration:1500});
      }
    },
    mounted() {
      var accessInfo = sessionStorage.getItem('access-user');
      this.sysUserName = JSON.parse(accessInfo).username;
      this.getUserProfile(this.sysUserName);
      console.log(this.user);
    }
  }

</script>
