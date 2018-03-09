<template>
  <el-row class="warp">
    <el-col :span="24" class="warp-breadcrum">
      <el-breadcrumb separator="/">
        <el-breadcrumb-item :to="{ path: '/' }"><b>首页</b></el-breadcrumb-item>
        <el-breadcrumb-item>策略管理</el-breadcrumb-item>
      </el-breadcrumb>
    </el-col>
    <el-row class="warp">
      <el-col :span="24" class="warp-main">
        <!--工具条-->
        <div class="toolbar" style="float:left;margin-left: 10px;">
          <el-button type="primary" @click="newPolicy">新建</el-button>
          <el-button type="primary" @click="batchDelete" v-if="policies.length !=0">
            批量删除
          </el-button>
        </div>
        <div class="toolbar" style="float:right;">
          <el-form :inline="true" :model="searchCmds" onsubmit="return false;">
            <el-form-item>
              <el-input v-model="searchCmds.name" placeholder="策略名" style="min-width: 240px;" @keyup.native="getPoliciesByName"></el-input>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="getPoliciesByName">查询</el-button>
            </el-form-item>
          </el-form>
        </div>
        <el-table :data="policies" highlight-current-row v-loading="loading" @selection-change="handleSelectionChange" style="width: 100%;">
          <el-table-column type="selection" width="50">
          </el-table-column>
          <el-table-column type="expand">
            <template slot-scope="scope">
              <el-form label-position="right" inline class="table-expand" label-width="100px">
                <el-form-item label="策略名">
                  <span>{{ scope.row.name }}</span>
                </el-form-item>
                <el-form-item label="策略ID">
                  <span>{{ scope.row.id }}</span>
                </el-form-item>
                <el-form-item label="策略说明" v-if="scope.row.description">
                  <span>{{ scope.row.description }}</span>
                </el-form-item>
                <el-form-item label="重复策略">
                  <span v-if="scope.row.recurring == 'once'">仅一次</span>
                  <span v-else-if="scope.row.recurring == 'hourly'">小时</span>
                  <span v-else-if="scope.row.recurring == 'daily'">天</span>
                  <span v-else-if="scope.row.recurring == 'weekly'">周</span>
                  <span v-else="scope.row.recurring == 'monthly'">月</span>
                </el-form-item>
                <el-form-item label="备份频率" v-if="scope.row.recurring_options_every">
                  <span>{{ scope.row.recurring_options_every }}</span>
                </el-form-item>
                <el-form-item label="周选项" v-if="scope.row.recurring == 'weekly'">
                  <template>
                    <span>{{ scope.row.recurring_options_week | weeksFormat }}</span>
                  </template>
                </el-form-item>
                <el-form-item label="备份保存周期">
                  <span v-if="scope.row.protection == -1">永久保存</span>
                  <span v-if="scope.row.protection != -1">{{ scope.row.protection }} 天</span>
                </el-form-item>
                <el-form-item label="创建用户">
                  <span>{{ scope.row.user }}</span>
                </el-form-item>
                <el-form-item label="创建时间">
                  <span>{{ scope.row.created_at | timeStamp2datetime}}</span>
                </el-form-item>
                <el-form-item label="更新时间">
                  <span>{{ scope.row.updated_at | timeStamp2datetime}}</span>
                </el-form-item>
              </el-form>
            </template>
          </el-table-column>
          <el-table-column prop="name" label="策略名" width="240" sortable>
          </el-table-column>
          <el-table-column prop="recurring" label="重复策略" width="180">
            <template slot-scope="scope">
              <span v-if="scope.row.recurring == 'once'">仅一次</span>
              <span v-else-if="scope.row.recurring == 'hourly'">小时</span>
              <span v-else-if="scope.row.recurring == 'daily'">天</span>
              <span v-else-if="scope.row.recurring == 'weekly'">周</span>
              <span v-else="scope.row.recurring == 'monthly'">月</span>
            </template>
          </el-table-column>
          <el-table-column prop="user" label="创建用户" width="240">
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" width="240" sortable>
            <template slot-scope="scope">
              <span>{{ scope.row.created_at | timeStamp2datetime }}</span>
            </template>
          </el-table-column>
          <el-table-column label="操作">
            <template slot-scope="scope">
              <svg class="icon" aria-hidden="true" @click="editPolicy(scope.$index, scope.row)">
                <use xlink:href="#icon-modify"></use>
              </svg>

              <svg class="icon" aria-hidden="true" @click="confirmDeleteMsgbox('deletePolicy',scope.$index, scope.row, _self.confimPolicyDeleteMsg)">
                <use xlink:href="#icon-delete"></use>
              </svg>
            </template>
          </el-table-column>
        </el-table>
      </el-col>
    </el-row>
    <el-row class="warp">
      <el-col :span="24" class="warp-main">
        <div class="tab-pagination" v-show="!loading">
          <el-pagination
            @size-change="handleSizeChange"
            @current-change="handleCurrentChange"
            :current-page="filter.page"
            :page-sizes="[10, 15, 20, 30]"
            :page-size="filter.per_page"
            layout="total, sizes, prev, pager, next, jumper"
            :total="total_rows"
            style="float: right; margin-top: 20px">
          </el-pagination>
        </div>
      </el-col>
    </el-row>
    <el-dialog :title="dialogPolicyTitle" :visible.sync="dialogPolicyVisible" :close-on-click-modal="!dialogPolicyVisible" @close="cancelPolicyDialog">
      <el-form :model="policyBaseForm" :rules="policyRules" ref="policyBaseForm">
        <el-form-item prop="name" label="策略名" :label-width="formLabelWidth">
          <el-input v-model="policyBaseForm.name" auto-complete="off" :disabled="!dialogNewPolicyVisible"></el-input>
        </el-form-item>
        <el-form-item label="描述" :label-width="formLabelWidth">
          <el-input v-model="policyBaseForm.description" auto-complete="off"></el-input>
        </el-form-item>
      </el-form>
      <!--<div class="line"></div>-->
      <!--<div class="line"></div>-->
      <el-form :model="policyRecurringForm" :rules="policyRules" ref="policyRecurringForm">
        <el-form-item label="重复策略" :label-width="formLabelWidth">
          <template>
            <el-radio class="radio" v-model="policyRecurringForm.recurring" label="once">仅一次</el-radio>
            <el-radio class="radio" v-model="policyRecurringForm.recurring" label="hourly">时</el-radio>
            <el-radio class="radio" v-model="policyRecurringForm.recurring" label="daily">天</el-radio>
            <el-radio class="radio" v-model="policyRecurringForm.recurring" label="weekly">周</el-radio>
            <el-radio class="radio" v-model="policyRecurringForm.recurring" label="monthly">月</el-radio>
          </template>

        </el-form-item>
        <el-form-item v-if="policyRecurringForm.recurring != 'once'" prop="recurring_options_every" label="备份频率"
                      :label-width="formLabelWidth">
          <el-input type="number" v-model="policyRecurringForm.recurring_options_every" auto-complete="off"></el-input>
        </el-form-item>
        <el-form-item v-if="policyRecurringForm.recurring == 'weekly'" prop="recurring_options_week" label="周选项"
                      :label-width="formLabelWidth">
          <template>
            <el-checkbox-group v-model="policyRecurringForm.recurring_options_week">
              <el-checkbox label=1>周一</el-checkbox>
              <el-checkbox label=2>周二</el-checkbox>
              <el-checkbox label=4>周三</el-checkbox>
              <el-checkbox label=8>周四</el-checkbox>
              <el-checkbox label=16>周五</el-checkbox>
              <el-checkbox label=32>周六</el-checkbox>
              <el-checkbox label=64>周日</el-checkbox>
            </el-checkbox-group>
          </template>
        </el-form-item>
      </el-form>
      <!--<div class="line"></div>-->
      <el-form :model="policyProtectionForm" :rules="policyRules" ref="policyProtectionForm">
        <el-form-item label="备份保存策略" :label-width="formLabelWidth">
          <template>
            <el-radio class="radio" v-model="policyProtectionForm.protectionType" label="1">天</el-radio>
            <el-radio class="radio" v-model="policyProtectionForm.protectionType" label="2">周</el-radio>
            <el-radio class="radio" v-model="policyProtectionForm.protectionType" label="3">月</el-radio>
            <el-radio class="radio" v-model="policyProtectionForm.protectionType" label="4">永久保存</el-radio>
          </template>
        </el-form-item>
        <el-form-item v-if="policyProtectionForm.protectionType != 4" prop="protection" label="备份保存周期"
                      :label-width="formLabelWidth">
          <el-input type="number" v-model="policyProtectionForm.protection" auto-complete="off"></el-input>
        </el-form-item>
      </el-form>
      <div slot="footer" class="dialog-footer">
        <el-button @click="cancelPolicyDialog">取 消</el-button>
        <el-button type="primary"
                   @click="savePolicy('policyBaseForm','policyTimeForm','policyRecurringForm','policyProtectionForm')">确定
        </el-button>
      </div>
    </el-dialog>
  </el-row>
</template>
<script>
  import {reqGetPolicyList, reqPostPolicy, reqPutPolicy, reqDelPolicy} from '../../api/api'
  import {util} from '../../common/util'
  export default{
    //props: ["roles", "groups"],
    data(){
      var checkOptionsEvery = (rule, value, callback) => {
        if (this.policyRecurringForm.recurring != 'once') {
          if (this.policyRecurringForm.recurring_options_every == null || this.policyRecurringForm.recurring_options_every == "undefined") {
            callback(new Error('至少为1个重复周期'));
          }else{
            callback();
          }
        }else{
          callback();
        }
        callback();
      };
      var checkOptionsWeek = (rule, value, callback) => {
        if (this.policyRecurringForm.recurring == 'weekly') {
          if (this.policyRecurringForm.recurring_options_week == null || this.policyRecurringForm.recurring_options_week == "undefined") {
            callback(new Error('至少选择一个日期'));
          }else{
            callback();
          }
        }else{
          callback();
        }
        callback();
      };
      return {
        loading: false,
        searchCmds: {
          name: ''
        },
        sysUserName: '',
        policies: [],
        policyBaseForm: {
          name: '',
          description: ''
        },
        policyRecurringForm: {
          recurring: 'once',
          recurring_options_every: '',
          recurring_options_week: []
        },
        policyProtectionForm: {
          protectionType: '1',
          protection: ''
        },
        policy:{},
        dialogNewPolicyVisible: false,
        dialogEditPolicyVisible: false,
        dialogPolicyVisible: false,
        formCheckErrorMsgForStarTime: true,
        checkStarTimeError: false,
        dialogPolicyTitle: '',
        formLabelWidth: '120px',
        confimPolicyDeleteMsg: '您确定要删除这个策略吗？',
        multipleSelection: [],
        filter: {
          per_page: 10,   //页大小
          page: 1,   //当前页
        },
        total_rows: 0,
        policyRules: {
          name: [
            { required: true, message: '请输入策略名称', trigger: 'blur' }
          ],
          recurring_options_every: [
            { validator: checkOptionsEvery, trigger: 'change' }
          ],
          recurring_options_week: [
            { type: 'array', validator: checkOptionsWeek, trigger: 'change' }
          ],
          protection: []
        }
      }
    },
    created(){
    },
    watch:{
      //policyTimeForm.start_now: function(o, n){
      //}
      dialogNewPolicyVisible: function(val, oldVal) {
        this.dialogPolicyVisible = val || this.dialogEditPolicyVisible;
      },
      dialogEditPolicyVisible: function(val, oldVal) {
        this.dialogPolicyVisible = val || this.dialogNewPolicyVisible;
      },
    },
    methods: {
      changeFormCheckErrorMsgForStarTime(){
        this.formCheckErrorMsgForStarTime = !this.formCheckErrorMsgForStarTime;
      },

      initialPolicyForms() {
        this.policyBaseForm.name = '';
        this.policyBaseForm.description = '';
        //this.policyTimeForm.start_time = '';
        //this.policyTimeForm.delay = false;
        //this.policyTimeForm.start_date = '';
        this.policyRecurringForm.recurring = 'once';
        this.policyRecurringForm.recurring_options_every = '';
        this.policyRecurringForm.recurring_options_week = [];
        this.policyProtectionForm.protectionType = '1';
        this.policyProtectionForm.protection = '';
        this.formCheckErrorMsgForStarTime = true;
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
      getPolicys(username, name_like=''){
        var page_offset = this.filter.per_page * (this.filter.page - 1);
        let params = {
          user: username,
          limit: this.filter.per_page,
          offset: page_offset,
        };
        if(name_like !== '') {
          params.name_like = name_like;
        }
        reqGetPolicyList(params).then(res => {
          this.policies = res.data.policies;
          this.total_rows = res.data.total;
          this.filter.page = this.filter.page;
          this.filter.per_page = this.filter.per_page;
        },err => {
          if (err.response.status == 401) {
            this.openMsg('请重新登陆', 'error');
            sessionStorage.removeItem('access-user');
            this.$router.push({ path: '/' });
          } else if (err.response.status == 403){
            this.$message({
              message: "没有权限",
              type: 'error'
            });
          }  else {
            console.log(err);
          }
        });
      },
      getPoliciesByName(event){
        if(this.searchCmds.name !== ''){
          this.getPolicys(this.sysUserName, this.searchCmds.name)
        }else{
          this.getPolicys(this.sysUserName)
        }
      },
      newPolicy(){
        this.dialogNewPolicyVisible = true;
        this.dialogEditPolicyVisible = false;
        this.initialPolicyForms();
        this.dialogPolicyTitle = '新建策略';
      },
      editPolicy(index, row){
        this.dialogEditPolicyVisible = true;
        this.dialogNewPolicyVisible = false;
        this.dialogPolicyTitle = '修改策略';
        this.policy = row;
        this.policyBaseForm.name = row.name;
        this.policyBaseForm.description = row.description;
        //this.policyTimeForm.delay = false;
        //this.policyTimeForm.start_date = new Date(row.start_time*1000);
        // this.policyTimeForm.start_time = new Date(row.start_time*1000);
        this.policyRecurringForm.recurring = row.recurring;
        this.policyRecurringForm.recurring_options_every = row.recurring_options_every;
        if (row.recurring_options_week !== null && row.recurring_options_week !== "" && row.recurring_options_week != 0) {
          this.policyRecurringForm.recurring_options_week = [];
          if (typeof(row.recurring_options_week) !== "number") {
            row.recurring_options_week = parseInt(row.recurring_options_week);
          }
          var weeks = [1, 2, 4, 8, 16, 32, 64];
          for (var i in weeks) {
            if ((row.recurring_options_week & weeks[i]) == weeks[i]){
              this.policyRecurringForm.recurring_options_week.push(weeks[i].toString())
            }
          }
        }
        if (row.protection == -1) {
          this.policyProtectionForm.protectionType = '4';
          this.policyProtectionForm.protection = '';
        } else {
          this.policyProtectionForm.protectionType = '1';
          this.policyProtectionForm.protection = row.protection;
        }
      },
      savePolicy(policyBaseForm, policyTimeForm, policyRecurringForm, policyProtectionForm){
        this.$refs[policyBaseForm].validate((valid) => {
          if (valid) {
            this.mergePolicyForm();
            let params = {
              user: this.sysUserName,
            };
            if (this.dialogNewPolicyVisible){
              reqPostPolicy(params, this.policy).then(res => {
                if(res.data.exist && res.data.exist === 'True') {
                  this.$message({
                    message: `添加失败, 策略 ${res.data.policy.name} 已存在`,
                    type: 'error'
                  });
                }else{
                  this.openMsg(this.dialogPolicyTitle+'成功', 'success');
                }
              },err => {
                if (err.response.status == 401) {
                  this.openMsg('请重新登陆', 'error');
                  sessionStorage.removeItem('access-user');
                  this.$router.push({ path: '/' });
                } else {
                  this.openMsg(this.dialogPolicyTitle+'失败', 'error');
                }
              });
            }
            if (this.dialogEditPolicyVisible){
              reqPutPolicy(params, this.policy).then(res => {
                this.openMsg(this.dialogPolicyTitle+'成功', 'success');
              },err => {
                if (err.response.status == 401) {
                  this.openMsg('请重新登陆', 'error');
                  sessionStorage.removeItem('access-user');
                  this.$router.push({ path: '/' });
                } else {
                  this.openMsg(this.dialogPolicyTitle+'失败', 'error');
                }
              });
            }
            this.cancelPolicyDialog();
            this.getPolicys(this.sysUserName);
          }else{
            this.openMsg('信息输入不正确，请检查格式！', 'error')
          }
        });
      },
      cancelPolicyDialog(){
        this.dialogNewPolicyVisible = false;
        this.dialogEditPolicyVisible = false;
        this.dialogPolicyVisible = false;
      },
      mergePolicyForm(){
        this.policy.name = this.policyBaseForm.name;
        this.policy.description = this.policyBaseForm.description;
        this.policy.recurring = this.policyRecurringForm.recurring;
        if (this.policyRecurringForm.recurring != 'once'){
          this.policy.recurring_options_every = this.policyRecurringForm.recurring_options_every;
        }
        this.policy.recurring_options_week = 0;
        if (this.policyRecurringForm.recurring == 'weekly'){
          console.log(this.policyRecurringForm.recurring_options_week);
          var i;
          for (i in this.policyRecurringForm.recurring_options_week) {
            this.policy.recurring_options_week = parseInt(this.policy.recurring_options_week) +
            parseInt(this.policyRecurringForm.recurring_options_week[i]);
          }
          //this.policy.recurring_options_week = this.policyRecurringForm.recurring_options_week;
        }
        /*
        if (this.policyTimeForm.start_date !== "" &&  this.policyTimeForm.start_date !== undefined && this.policyTimeForm.start_date !== null){
          var dateStr = this.policyTimeForm.start_date.toDateString();
          this.policy.start_time = new Date(dateStr).getTime()/1000;
        } else {
          this.policy.start_time = this.policyTimeForm.start_time.getTime()/1000;
        }*/
        switch(this.policyProtectionForm.protectionType){
          case '1':
            this.policy.protection = this.policyProtectionForm.protection;
            break;
          case '2':
            this.policy.protection = this.policyProtectionForm.protection*7;
            break;
          case '3':
            this.policy.protection = this.policyProtectionForm.protection*30;
            break;
          case '4':
            this.policy.protection = -1;
            break;
        };
      },
      deletePolicy(index ,row){
        let params = {
          user: this.sysUserName,
        };
        reqDelPolicy(params, row.id).then(res =>{
          this.getPolicys(this.sysUserName);
          this.openMsg('删除成功', 'success');
        }, err =>{
          if (err.response.status == 401) {
            this.openMsg('请重新登陆', 'error');
            sessionStorage.removeItem('access-user');
            this.$router.push({ path: '/' });
          } else if (err.response.status == 403) {
            var tips = '';
            if(err.response.data.code == 403){
              tips = err.response.data.tasks[0]+' 等 '+err.response.data.tasks.length+" 个备份任务正在使用，请先删除任务"
              this.openMsg('删除失败', 'error');
              this.openNotify('失败提示',tips,'error');
            }else if(err.response.data.code == 401) {
              this.openMsg('没有权限', 'error');
            }
          }else {
            this.openMsg('请求失败', 'error');
          }
        });
      },
      //勾选
      handleSelectionChange: function (multipleSelection) {
        this.multipleSelection = multipleSelection;
      },
      batchDelete(){
        if(this.multipleSelection.length > 0){
          this.$confirm('将删除选中的'+this.multipleSelection.length+'个策略？','提示',{
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          }).then(() => {
            for (var i = 0; i < this.multipleSelection.length; ++i){
              this.deletePolicy(i,this.multipleSelection[i])
            }
          }).catch(e => {
            this.$message({
              type: 'info',
              message: '已取消删除'
            });
          });
        }else{
          this.openMsg('至少选中一条数据', 'info');
        }
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
              if(func == 'deletePolicy'){
                  this.deletePolicy(index, row);
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
          this.getPolicys(this.sysUserName);
          //console.log(`每页 ${val} 条`);
      },
      handleCurrentChange(val) {
          this.filter.page = val;
          this.getPolicys(this.sysUserName);
          //console.log(`当前页: ${val}`);
      },
    },
    mounted() {
      var accessInfo = sessionStorage.getItem('access-user');

      this.sysUserName = JSON.parse(accessInfo).username;
      this.getPolicys(this.sysUserName);
    }
  }



</script>
<style scoped lang="scss">
  .line {
    line-height: 1px;
    border-top: 1px solid #999;
    //border-bottom: 1px solid #999;
    margin: 20px 0;
    text-align: center;
  }
</style>
