<template>
  <el-row class="warp">
    <el-col :span="24" class="warp-breadcrum">
      <el-breadcrumb separator="/">
        <el-breadcrumb-item :to="{ path: '/' }"><b>首页</b></el-breadcrumb-item>
        <el-breadcrumb-item>个人信息</el-breadcrumb-item>
      </el-breadcrumb>
    </el-col>

    <el-col :span="24" class="warp-main">
      <el-form ref="userForm" :model="userForm" :rules="rules" label-width="80px">
        <el-form-item label="用户名">
          <el-input v-model="userForm.name" disabled></el-input>
        </el-form-item>
        <el-form-item label="角色" >
            <el-select v-model="userForm.role_id" placeholder="角色选择">
              <el-option v-for="role in roles"  :label="role.name" :value="role.id" :key="role.id"></el-option>
            </el-select>
        </el-form-item>
        <el-form-item label="用户组">
          <el-select v-model="userForm.group_id" placeholder="组选择">
            <el-option v-for="group in groups"  :label="group.name" :value="group.id" :key="group.id"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="submitUserProfile('userForm')">修改并保存</el-button>
        </el-form-item>
      </el-form>
    </el-col>
  </el-row>
</template>

<script>
  import {reqSaveUserProfile, reqGetUserProfile, reqGetRoleList, reqGetGroupList, reqUpdateUserProfile} from '../../api/api';
  import {bus} from '../../bus.js'
  import export2Excel from '../../common/export2Excel'
  export default {
    props: ["roles", "groups"],
    data() {
      return {
        form: {
          name: '',
          role: 0,
          group: 0
        },
        sysUserName: '',
        userForm: {
          name: '',
          role_id: '',
          group_id: '',
          created_at: ''
        },
        //roles: [],
        //groups: [],
        isSuperAdm: false,
        rules: {

        },
      }
    },
    created(){
      bus.$on('roles', (obj) => {
        this.roles = obj;
      });
      bus.$on('groups', (obj) => {
        this.groups = obj;
      });
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
      submitUserProfile(userForm){
        let params = {
          user: this.userForm.name,
          userProfile: this.userForm
        }
        reqUpdateUserProfile(this.userForm).then(res => {
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
            this.userForm = data.user;
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
            this.userForm = data.users[0];
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
      this.sysUserName = JSON.parse(accessInfo).username;
      this.getUserProfile(this.sysUserName);
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
