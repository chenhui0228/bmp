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
          <el-button type="primary" @click="">批量删除</el-button>
        </div>
        <div class="toolbar" style="float:right;">
          <el-form :inline="true" :model="searchCmds">
            <el-form-item>
              <el-input v-model="searchCmds.name" placeholder="姓名" style="min-width: 240px;"></el-input>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="">查询</el-button>
            </el-form-item>
          </el-form>
        </div>
        <el-table :data="policies" highlight-current-row v-loading="loading" style="width: 100%;">
          <el-table-column type="selection" width="50">
          </el-table-column>
          <el-table-column prop="name" label="策略名" width="240" sortable>
          </el-table-column>
          <el-table-column prop="recurring" label="备份频率" width="180">
            <template scope="scope">
              <span v-if="scope.row.recurring == 'once'">仅一次</span>
              <span v-else-if="scope.row.recurring == 'hourly'">小时</span>
              <span v-else-if="scope.row.recurring == 'daily'">天</span>
              <span v-else-if="scope.row.recurring == 'weekly'">周</span>
              <span v-else="scope.row.recurring == 'monthly'">月</span>
            </template>
          </el-table-column>
          <el-table-column prop="start_time" label="开始时间" width="240" sortable>
            <template scope="scope">
              <span>{{ scope.row.start_time | timeStamp2datetime }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="user.name" label="创建用户" width="240">
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" width="240" sortable>
            <template scope="scope">
              <span>{{ scope.row.created_at | timeStamp2datetime }}</span>
            </template>
          </el-table-column>
          <el-table-column label="操作">
            <template scope="scope">
              <el-button type="text" icon="information" @click=""></el-button>
              <el-button v-if="" type="text" icon="edit" @click=""></el-button>
              <el-button v-if="" type="text" icon="delete" style="color: red" @click=""></el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-col>
    </el-row>
    <el-row class="warp">
      <!--<el-col :span="24" class="warp-main">-->
      <!--<div class="tab-pagination" v-show="!tabLoading">-->
      <!--<el-pagination-->
      <!--@size-change="handleSizeChange"-->
      <!--@current-change="handleCurrentChange"-->
      <!--:current-page="1"-->
      <!--:page-sizes="[10, 15, 20, 30]"-->
      <!--:page-size="6"-->
      <!--layout="total, sizes, prev, pager, next, jumper"-->
      <!--total="100"-->
      <!--style="float: right;">-->
      <!--</el-pagination>-->
      <!--</div>-->
      <!--</el-col>-->
    </el-row>
    <el-dialog title="新建策略" v-model="dialogNewPolicyVisible">
      <el-form :model="policyBaseForm" :rules="policyRules" ref="policyBaseForm">
        <el-form-item prop="name" label="策略名" :label-width="formLabelWidth">
          <el-input v-model="policyBaseForm.name" auto-complete="off"></el-input>
        </el-form-item>
        <el-form-item label="描述" :label-width="formLabelWidth">
          <el-input v-model="policyBaseForm.description" auto-complete="off"></el-input>
        </el-form-item>
      </el-form>
      <!--<div class="line"></div>-->
      <el-form :model="policyTimeForm" :rules="policyRules" ref="policyTimeForm">
        <el-row>
          <el-col :span="5">
            <el-form-item prop="delay" label="指定开始日期" :label-width="formLabelWidth">
              <template>
                <el-switch v-model="policyTimeForm.delay" on-text="是" off-text="否"></el-switch>
                <!--<el-checkbox-group v-model="policyTimeForm.delay">-->
                  <!--<el-checkbox label="1"></el-checkbox>-->
                <!--</el-checkbox-group>-->
              </template>
            </el-form-item>
          </el-col>
          <el-col :span="19">
            <el-form-item :label-width="formLabelWidth" style="margin-left: -120px">
              <template>
                <el-date-picker
                  v-model="policyTimeForm.start_date"
                  type="date"
                  :picker-options="pickerOptionsForDate" :disabled="!policyTimeForm.delay">
                </el-date-picker>

              </template>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item prop="start_time" label="开始时间" :label-width="formLabelWidth" :show-message="formCheckErrorMsgForStarTime">
          <template>
            <el-time-picker
              v-model="policyTimeForm.start_time">
            </el-time-picker>
            <div class="el-form-item__error" v-if="checkStarTimeError">起始时间必须设置在当前时刻5分钟以后</div>
          </template>
        </el-form-item>
      </el-form>
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
              <el-checkbox label="1">周一</el-checkbox>
              <el-checkbox label="2">周二</el-checkbox>
              <el-checkbox label="3">周三</el-checkbox>
              <el-checkbox label="4">周四</el-checkbox>
              <el-checkbox label="5">周五</el-checkbox>
              <el-checkbox label="6">周六</el-checkbox>
              <el-checkbox label="7">周日</el-checkbox>
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
        <el-button @click="dialogNewPolicyVisible = false">取 消</el-button>
        <el-button type="primary" @click="savePolicy('policyBaseForm','policyTimeForm','policyRecurringForm','policyProtectionForm')">确 定</el-button>
      </div>
    </el-dialog>
  </el-row>
</template>
<script>
  import {reqGetPolicyList, reqPostPolicyList} from '../../api/api'
  import {util} from '../../common/util'
  export default{
    props: ["roles", "groups"],
    data(){
      var checkStarTime = (rule, value, callback) => {
        if (this.dialogNewPolicyVisible && !this.policyTimeForm.delay) {
          var nowTime = new Date(new Date().getTime() + 5*60*1000).getTime();
          var valueTime = new Date(value).getTime();
          if (valueTime < nowTime) {
            callback(new Error('起始时间必须设置在当前时刻5分钟以后'));
            //this.checkStarTimeError = true;
            //callback();
          } else {
            callback();
          }
        } else if (this.dialogEditPolicyVisible) {
          callback();
        } else {
          callback();
        }
      };
      var checkStarTimeAgain = (rule, value, callback) => {
        this.formCheckErrorMsgForStarTime = !this.formCheckErrorMsgForStarTime;
        this.checkStarTimeError = false;
        callback();
      };
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
        policyTimeForm: {
          start_time: '',
          delay: false,
          start_date: ''
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
        formCheckErrorMsgForStarTime: true,
        checkStarTimeError: false,
        formLabelWidth: '120px',
        pickerOptionsForDate: {
          disabledDate(time) {
            return time.getTime() < Date.now() - 8.64e7;
          }
        },

        policyRules: {
          name: [
            { required: true, message: '请输入策略名称', trigger: 'blur' }
          ],
          start_time: [
            { required: true, validator: checkStarTime, trigger: 'blur' }
          ],
          delay : [
            { type: 'array',  validator: checkStarTimeAgain, trigger: 'change' }
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
    },
    methods: {
      changeFormCheckErrorMsgForStarTime(){
        this.formCheckErrorMsgForStarTime = !this.formCheckErrorMsgForStarTime;
      },

      initialPolicyForms() {
        this.policyBaseForm.name = '',
        this.policyBaseForm.description = '',
        this.policyTimeForm.start_time = '',
        this.policyTimeForm.delay = false,
        this.policyTimeForm.start_date = '',
        this.policyRecurringForm.recurring = 'once',
        this.policyRecurringForm.recurring_options_every = '',
        this.policyRecurringForm.recurring_options_week = [],
        this.policyProtectionForm.protectionType = '1',
        this.policyProtectionForm.protection = '',
        this.formCheckErrorMsgForStarTime = true
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
      getPolicys(username){
        let params = {
          user: username,
        };
        reqGetPolicyList(params).then(res => {
          this.policies = res.data.policies;
          console.log(res);
        },err => {
          console.log(err);
        });
      },
      newPolicy(){
        this.dialogNewPolicyVisible = true;
        this.initialPolicyForms();
      },
      savePolicy(policyBaseForm, policyTimeForm, policyRecurringForm, policyProtectionForm){
        console.log(this.policyTimeForm, this.policyRecurringForm, this.policyProtectionForm)
        this.$refs[policyBaseForm].validate((valid) => {
          this.$refs[policyTimeForm].validate((valid) => {
            this.mergePolicyForm();
            let params = {
              user: this.sysUserName,
            };
            reqPostPolicyList(params, this.policy).then(res => {
              this.openMsg('新增作业机成功', 'success');
              this.dialogNewPolicyVisible = false;
              this.getPolicys(this.sysUserName);
            });
          });
        });
      },
      mergePolicyForm(){
        this.policy.name = this.policyBaseForm.name;
        this.policy.description = this.policyBaseForm.description;
        this.policy.recurring = this.policyRecurringForm.recurring;
        if (this.policyRecurringForm.recurring != 'once'){
          this.policy.recurring_options_every = this.policyRecurringForm.recurring_options_every;
        }
        if (this.policyRecurringForm.recurring == 'weekly'){
          this.policy.recurring_options_week = this.policyRecurringForm.recurring_options_week;
        }
        if (this.policyTimeForm.start_date !== "" ){
          var dateStr = this.policyTimeForm.start_date.toDateString();
          var timeStr = this.policyTimeForm.start_time.toTimeString();
          this.policy.start_time = new Date(dateStr + ' ' + timeStr).getTime()/1000;
        } else {
          this.policy.start_time = this.policyTimeForm.start_time.getTime()/1000;
        }
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
      }
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
