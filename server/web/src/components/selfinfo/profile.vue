<template>
  <el-row class="warp">
    <el-col :span="24" class="warp-breadcrum">
      <el-breadcrumb separator="/">
        <el-breadcrumb-item :to="{ path: '/' }"><b>首页</b></el-breadcrumb-item>
        <el-breadcrumb-item>个人信息</el-breadcrumb-item>
      </el-breadcrumb>
    </el-col>
    <el-row class="warp">
      <!--<el-col :span="1" min-height="12px">-->
      <!--</el-col>-->
      <el-col :span="10" class="warp-main" style="border-top: 1px solid #bbb;margin-top: 20px">
        <div class="detail-item">
          <div class="item-key">用户名&nbsp:</div>
          <div class="item-value">&nbsp{{ user.name }}</div>
        </div>
        <div class="detail-item">
          <div class="item-key">角色&nbsp:</div>
          <div class="item-value">&nbsp{{ user.role }}</div>
        </div>
        <div class="detail-item">
          <div class="item-key">组织&nbsp:</div>
          <div class="item-value">&nbsp{{ user.group }}</div>
        </div>
        <div class="detail-item">
          <div class="item-key">创建时间&nbsp:</div>
          <div class="item-value">&nbsp{{ user.created_at | timeStamp2datetime }}</div>
        </div>
        <div class="detail-item">
          <div class="item-key">更新时间&nbsp:</div>
          <div class="item-value">&nbsp{{ user.updated_at | timeStamp2datetime }}</div>
        </div>
      </el-col>
    </el-row>
  </el-row>
</template>

<script>
  import {reqSaveUserProfile, reqGetUserProfile, reqGetRoleList, reqGetGroupList, reqUpdateUserProfile} from '../../api/api';
  import {bus} from '../../bus.js'
  import export2Excel from '../../common/export2Excel'
  export default {
    //props: ["roles", "groups"],
    data() {
      return {
        form: {
          name: '',
          role: 0,
          group: 0
        },
        sysUserName: '',
        user: {
          id: '',
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
      getRoles(username){
        let params = {
          user: username
        };
        reqGetRoleList(params).then(res => {
          let { status, data } = res;
          if (data == null) {
            console.log("无法获取角色列表");
          } else {
            //this.roles = data.roles;
            //bus.$emit('roles', data.roles);
          }
        },err => {
          if (err.response.status == 401) {
            this.$message({
              message: "请重新登陆",
              type: 'error'
            });
            sessionStorage.removeItem('access-user');
            this.$router.push({ path: '/' });
          } else if (err.response.status == 403){
            this.$message({
              message: "没有权限",
              type: 'error'
            });
          }  else {
            this.$message({
              message: "请求异常",
              type: 'error'
            });
          }
        });
      },
      getGroups(username){
        let params = {
          user: username
        };
        reqGetGroupList(params).then(res => {
          let { status, data } = res;
          if (data == null) {
            console.log("无法获取组列表");
          } else {
            //this.groups = data.groups;
            this.$emit("transferRoles", groups)
            //bus.$emit('groups', data.groups);
          }
        },err => {
          if (err.response.status == 401) {
            this.$message({
              message: "请重新登陆",
              type: 'error'
            });
            sessionStorage.removeItem('access-user');
            this.$router.push({ path: '/' });
          } else if (err.response.status == 403){
            this.$message({
              message: "没有权限",
              type: 'error'
            });
          }  else {
            this.$message({
              message: "请求异常",
              type: 'error'
            });
          }
        });
      },
      submitUserProfile(user){
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
          } else if (err.response.status == 403){
            this.$message({
              message: "没有权限",
              type: 'error'
            });
          }  else {
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
        };
        reqGetUserProfile(params, this.user.id).then(res => {
          let { status, data } = res;
          if (data == null) {
            this.$message({
              message: "未获取到信息",
              type: 'error'
            });
          } else {
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
      }
    },
    mounted() {
      var accessInfo = sessionStorage.getItem('access-user');
      this.sysUserName = JSON.parse(accessInfo).username;
      this.user.id = JSON.parse(accessInfo).uid;
      //this.getRoles(this.sysUserName);
      //this.getGroups(this.sysUserName);
      this.getUserProfile(this.sysUserName);
      //console.log(this.roles);
      //console.log(this.groups);
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
<style scoped lang="scss">
  .detail-item {
    display: table;
    height: 30px;
  }
  .item-key {
    display: table-cell;
    vertical-align: middle;
    width: 100px;
    text-align: right;
  }
  .item-value {
    display: table-cell;
    vertical-align: middle;
  }
</style>
