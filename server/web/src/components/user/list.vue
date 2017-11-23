<template>
  <el-row class="warp">
    <el-col :span="24" class="warp-breadcrum">
      <el-breadcrumb separator="/">
        <el-breadcrumb-item :to="{ path: '/' }"><b>首页</b></el-breadcrumb-item>
        <el-breadcrumb-item>用户列表</el-breadcrumb-item>
      </el-breadcrumb>
    </el-col>

    <el-row class="warp">
      <el-col :span="24" class="warp-main">
        <!--工具条-->
        <div class="toolbar" style="float:left;margin-left: 10px;">
          <el-button type="primary" @click="newUser">新建</el-button>
          <el-button type="primary" @click="">批量删除</el-button>
        </div>
        <div class="toolbar" style="float:right;">
          <el-form :inline="true" :model="searchCmds">
            <el-form-item>
              <el-input v-model="searchCmds.name" placeholder="用户名" style="min-width: 240px;"></el-input>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="">查询</el-button>
            </el-form-item>
          </el-form>
        </div>
        <el-table :data="users" highlight-current-row v-loading="loading" style="width: 100%;">
          <el-table-column type="selection" width="50">
          </el-table-column>
          <el-table-column prop="name" label="用户名" width="240" sortable>
          </el-table-column>
          <el-table-column prop="role" label="角色" width="180">
          </el-table-column>
          <el-table-column prop="group" label="属组" width="240">
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" width="240" sortable>
            <template scope="scope">
              <span>{{ scope.row.created_at | timeStamp2datetime }}</span>
            </template>
          </el-table-column>
          <el-table-column label="操作">
            <template scope="scope">
              <!--<el-button type="text" icon="information" @click=""></el-button>-->
              <svg class="icon" aria-hidden="true" @click="editUser(scope.$index,scope.row)">
                <use xlink:href="#icon-modify"></use>
              </svg>
              <svg class="icon" aria-hidden="true" @click="confirmDeleteMsgbox('deleteUser',scope.$index, scope.row, _self.confimUserDeleteMsg)">
                <use xlink:href="#icon-delete"></use>
              </svg>
            </template>
          </el-table-column>
        </el-table>
      </el-col>
    </el-row>
    <el-row class="warp">
      <el-col :span="24" class="warp-main">
        <div class="tab-pagination" v-show="">
          <el-pagination
            @size-change="handleSizeChange"
            @current-change="handleCurrentChange"
            :current-page="filter.page"
            :page-sizes="[10, 15, 20, 30]"
            :page-size="filter.per_page"
            layout="total, sizes, prev, pager, next, jumper"
            :total="total_rows"
            style="float: right;">
          </el-pagination>
        </div>
      </el-col>
    </el-row>
    <el-dialog :title="dialogUserTitle" :visible.sync="dialogUserVisible" :close-on-click-modal="!dialogUserVisible" @close="cancelUserDialog">
      <el-form :model="userForm" :rules="userRules" ref="userForm">
        <el-form-item prop="name" label="用户名" :label-width="formLabelWidth">
          <el-input v-model="userForm.name" auto-complete="off" :disabled="dialogEditUserVisible"></el-input>
        </el-form-item>
        <el-form-item prop="group_id" label="用户组" :label-width="formLabelWidth">
          <!--<el-input v-model="userForm.group_id" auto-complete="off"></el-input>-->
          <el-select v-if="userForm.role != 'superrole'" v-model="userForm.group_id" placeholder="选择组" :disabled="role != 'superrole'">
            <el-option v-for="group in groups"  :label="group.name" :value="group.id" :key="group.id"></el-option>
          </el-select>
          <el-input v-if="userForm.role == 'superrole'" auto-complete="off" :disabled="dialogEditUserVisible" placeholder="不属于任何组"></el-input>
        </el-form-item>
        <el-form-item prop="role_id" label="角色" :label-width="formLabelWidth">
          <!--<el-input v-model="userForm.role_id" auto-complete="off"></el-input>-->
          <el-select v-if="userForm.role != 'superrole'" v-model="userForm.role_id" placeholder="选则角色">
            <el-option v-for="role in roles"  :label="role.name" :value="role.id" :key="role.id"></el-option>
          </el-select>
          <el-input v-if="userForm.role == 'superrole'" v-model="role" auto-complete="off" :disabled="dialogEditUserVisible"></el-input>
        </el-form-item>
        <el-form-item label="随机密码" :label-width="formLabelWidth" v-if="dialogNewUserVisible">
          <!--<el-input v-model="randomPassword" auto-complete="off"></el-input>-->
          <template>
            <el-switch v-model="randomPassword" on-text="是" off-text="否"></el-switch>
          </template>
        </el-form-item>
        <el-form-item label="修改密码" :label-width="formLabelWidth" v-if="dialogEditUserVisible">
          <!--<el-input v-model="randomPassword" auto-complete="off"></el-input>-->
          <template>
            <el-switch v-model="modifyPassword" on-text="是" off-text="否"></el-switch>
          </template>
        </el-form-item>
        <el-form-item prop="password" label="密码" :label-width="formLabelWidth" v-if="!randomPassword || modifyPassword">
          <el-input type="password" v-model="userForm.password" auto-complete="off"></el-input>
        </el-form-item>
        <el-form-item prop="password2" label="密码确认" :label-width="formLabelWidth" v-if="!randomPassword || modifyPassword">
          <el-input type="password" v-model="userForm.password2" auto-complete="off"></el-input>
        </el-form-item>
      </el-form>
      <div slot="footer" class="dialog-footer">
        <el-button @click="cancelUserDialog">取 消</el-button>
        <el-button type="primary"
                   @click="saveUser('userForm')">确定
        </el-button>
      </div>
    </el-dialog>
  </el-row>
</template>

<script>
  import {reqGetUserProfile, reqGetRoleList, reqGetGroupList, reqUpdateUserProfile, reqGetUserList, reqPostUser, reqPutUser, reqDelUser} from '../../api/api'
  import util from '../../common/util'
  export default {
    //props: ["roles", "groups"],
    data() {
    var validatePass = (rule, value, callback) => {
        if (value === '') {
          callback(new Error('请输入密码'));
        } else {
          if (this.userForm.password !== '') {
            //this.$refs.form.validateField('newPwd');
          }
          callback();
        }
      };
      var validatePass2 = (rule, value, callback) => {
        if (value === '') {
          callback(new Error('请再次输入密码'));
        } else if (value !== this.userForm.password2) {
          callback(new Error('两次输入密码不一致!'));
        } else {
          callback();
        }
      };
      return {
        searchCmds: {
          name: ''
        },
        loading: false,
        sysUser:{
          id: '',
        },
        role: '',
        roles: [],
        groups: [],
        users: [],
        userForm: {
          name: '',
          group_id: '',
          role_id: '',
          password: '',
          password2: '',
          role: ''
        },  //表单
        user:{},  //提交user对象
        dialogNewUserVisible: false,
        dialogEditUserVisible: false,
        dialogUserVisible: false,
        dialogUserTitle: '',
        randomPassword: true,
        modifyPassword: false,
        confimUserDeleteMsg: '你确定要删除这个用户吗？',
        filter: {
          per_page: 10,   //页大小
          page: 1   //当前页
        },
        total_rows: 0,
        formLabelWidth: '120px',
        userRules: {
          name: [
            { required: true, message: '请输入用户名', trigger: 'blur' }
          ],
          group_id: [
            { required: true, message: '必须选则一个组', trigger: 'change' }
          ],
          role_id: [
            { required: true, message: '必须给定角色', trigger: 'change' }
          ],
          password: [{ required: !this.randomPassword, validator: validatePass, trigger: 'blur'}],
          password2: [{required: !this.randomPassword, validator: validatePass2, trigger: 'blur'}]
        },
      }
    },
    watch:{
      //UserTimeForm.start_now: function(o, n){
      //}
      dialogNewUserVisible: function(val, oldVal) {
        this.dialogUserVisible = val || this.dialogEditUserVisible;
      },
      dialogEditUserVisible: function(val, oldVal) {
        this.dialogUserVisible = val || this.dialogNewUserVisible;
      },
    },
    methods: {
      /*
      roleId2Name(row, column, cellValue){
        var index;
        var tmpValue = "未知";
        for (index in this.roles){
          if (this.roles[index].id == cellValue) {
            tmpValue = this.roles[index].name;
            break;
          }
        }
        return tmpValue;
      },
      groupId2Name(row, column, cellValue){
        var index;
        var tmpValue = "未知";
        for (index in this.groups){
          if (this.groups[index].id == cellValue) {
            tmpValue = this.groups[index].name;
            break;
          }
        }
        return tmpValue;
      },*/



      //性别显示转换
      formatSex: function (row, column) {
        return row.sex == 1 ? '男' : row.sex == 0 ? '女' : '未知';
      },
      //获取用户列表
      getUsers(username){
        let params = {
          user: username,
        };
        reqGetUserList(params).then(res => {
          let { status, data } = res;
          if (data == null) {
            this.$message({
              message: "未获取到信息",
              type: 'error'
            });
          } else {
            this.users = data.users;
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
          } else {
            this.$message({
              message: "请求异常",
              type: 'error'
            });
          }
        });
      },
      initialUserForms(){
        this.userForm.name = '';
        this.userForm.role_id = '';
        if(this.role != 'superrole'){
          this.userForm.group_id = this.sysUser.group_id;
        }else {
          this.userForm.group_id = '';
        }
        this.randomPassword = true;
        this.userForm.password = '';
        this.userForm.password2 = '';
      },
      //新建用户
      newUser() {
        this.dialogNewUserVisible = true;
        this.dialogEditUserVisible = false;
        this.initialUserForms();
        this.dialogUserTitle = '新建用户';
      },
      cancelUserDialog(){
        this.dialogNewUserVisible = false;
        this.dialogEditUserVisible = false;
        this.dialogUserVisible = false;
      },
      editUser(index, row){
        this.dialogEditUserVisible = true;
        this.dialogNewUserVisible = false;
        this.dialogUserTitle = '修改用户信息';
        this.modifyPassword = false;
        this.user = row;
        this.userForm.name = row.name;
        this.userForm.role_id = row.role_id;
        this.userForm.group_id = row.group_id;
        this.userForm.role = row.role;
      },
      saveUser(userForm){
        this.$refs[userForm].validate((valid) => {
          if(valid){
            this.userForm2user();
            let params = {
              user: this.sysUserName,
            };
            if (this.dialogNewUserVisible){
                console.log(params, this.user);
                reqPostUser(params, this.user).then(res => {
                  this.openMsg(this.dialogUserTitle+'成功', 'success');
                  if(this.randomPassword){
                    this.$alert(this.user.name+'的密码是' + this.user.password + '，登陆后可修改！', '用户密码', {
                      confirmButtonText: '确定',
                    });
                  }
                },err => {
                  if (err.response.status == 401) {
                    this.openMsg('请重新登陆', 'error');
                    sessionStorage.removeItem('access-user');
                    this.$router.push({ path: '/' });
                  } else {
                    this.openMsg(this.dialogUserTitle+'失败', 'error');
                  }
                });
              }
            if (this.dialogEditUserVisible){
              reqPutUser(params, this.user).then(res => {
                this.openMsg(this.dialogUserTitle+'成功', 'success');
              },err => {
                if (err.response.status == 401) {
                  this.openMsg('请重新登陆', 'error');
                  sessionStorage.removeItem('access-user');
                  this.$router.push({ path: '/' });
                } else {
                  this.openMsg(this.dialogUserTitle+'失败', 'error');
                }
              });
            }
            this.cancelUserDialog();
            this.getUsers(this.sysUserName);
          }else{
            this.openMsg('信息输入不正确，请检查格式！', 'error');
          }
        });
        this.initialUserForms();
      },
      userForm2user(){
        this.user.name = this.userForm.name;
        this.user.role_id = this.userForm.role_id;
        this.user.group_id = this.userForm.group_id;
        if(this.dialogNewUserVisible){
          if(this.randomPassword){
            this.user.password = util.randomStr(8);
          }else{
            this.user.password = this.userForm.password;
          }
        };
        if(this.dialogEditUserVisible){
          if(this.modifyPassword){
            this.user.password = this.userForm.password;
          }
        }
      },
      getRoles(username){
        let params = {
          user: username
        };
        reqGetRoleList(params).then(res => {
          let { status, data } = res;
          if (data == null) {
            console.log("无法获取角色列表");
          } else {
            this.roles = data.roles;
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
          } else {
            this.$message({
              message: "请求异常",
              type: 'error'
            });
          }
        });
      },
      deleteUser(index ,row){
        let params = {
          user: this.sysUserName,
        };
        reqDelUser(params, row.id).then(res =>{
          this.getUsers(this.sysUserName);
          this.openMsg('删除成功', 'success');
        }, err =>{
          if (err.response.status == 401) {
            this.openMsg('请重新登陆', 'error');
            sessionStorage.removeItem('access-user');
            this.$router.push({ path: '/' });
          } else if (err.response.status == 403) {
            if(err.response.data.code == 403){
              this.openMsg('删除失败', 'error');
            }else if(err.response.data.code == 401) {
              this.openMsg('没有权限', 'error');
            }else {
              this.openMsg('删除失败', 'error');
            }
          }else {
            this.openMsg('请求失败', 'error');
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
            this.groups = data.groups;
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
        };
        reqGetUserProfile(params, this.sysUser.id).then(res => {
          let { status, data } = res;
          if (data == null) {
            this.$message({
              message: "未获取到信息",
              type: 'error'
            });
          } else {
            this.sysUser = data.user;
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
      //事件通知模块
      openNotify(title, msgtext, type){
          this.$notify({
              title: title,
              message: msgtext,
              type: type
          });
      },
      //事件消息模块
      openMsg(msgtext, type){
          this.$message({
              message: msgtext,
              type: type
          });
      },
      confirmDeleteMsgbox(func, index, row, mymsg){
        const h = this.$createElement;
        this.$msgbox({
          title: '重要提醒',
          message: h('p',{style: 'color: red'}, mymsg),
          type: 'warning',
          showCancelButton: true,
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          beforeClose: (action, instance, done) => {
            if (action === 'confirm') {
              if(func == 'deleteUser'){
                  this.deleteUser(index, row);
              }else {

              }
              done();
            } else {
              done();
            }
          }
        }).then(action => {
        });
        },
      //-----分页----
      handleSizeChange(val) {
        this.filter.per_page = val;
        this.getUsers(this.sysUserName);
        //console.log(`每页 ${val} 条`);
      },
      handleCurrentChange(val) {
        this.filter.page = val;
        this.getUsers(this.sysUserName);
        //console.log(`当前页: ${val}`);
      },
    },
    mounted() {
      var accessInfo = sessionStorage.getItem('access-user');
      this.sysUserName = JSON.parse(accessInfo).username;
      this.role = JSON.parse(accessInfo).role;
      this.sysUser.id = JSON.parse(accessInfo).uid;
      this.getUsers(this.sysUserName);
      this.getRoles(this.sysUserName);
      this.getGroups(this.sysUserName);
      this.getUserProfile(this.sysUserName);
    }
  }



</script>

<style scoped>

</style>
