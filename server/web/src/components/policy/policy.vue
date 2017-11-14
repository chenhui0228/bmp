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
        <el-form :inline="true" :model="filters">
          <el-form-item>
            <el-input v-model="filters.name" placeholder="姓名" style="min-width: 240px;"></el-input>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="">查询</el-button>
          </el-form-item>
        </el-form>
      </div>
      <el-table :data="policys" highlight-current-row v-loading="loading" style="width: 100%;">
        <el-table-column type="selection" width="50">
        </el-table-column>
        <!--<el-table-column type="index" width="60">-->
        <!--</el-table-column>-->
        <el-table-column prop="name" label="策略名" width="240" sortable>
        </el-table-column>
        <el-table-column prop="role" label="备份频率" width="180">
          <!--<template scope="scope">-->

          <!--</template>-->
        </el-table-column>
        <el-table-column prop="role" label="开始时间" width="240" sortable>
          <!--<template scope="scope">-->

          <!--</template>-->
        </el-table-column>
        <el-table-column prop="group" label="创建用户" width="240">
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="240" sortable>
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
      <el-form :model="policyBaseForm">
        <el-form-item label="策略名" :label-width="formLabelWidth">
          <el-input v-model="policyBaseForm.name" auto-complete="off"></el-input>
        </el-form-item>
        <el-form-item label="说明" :label-width="formLabelWidth">
          <el-input v-model="policyBaseForm.description" auto-complete="off"></el-input>
        </el-form-item>
      </el-form>
      <!--<div class="line"></div>-->
      <el-form :model="policyTimeForm">
        <el-form-item label="开始时间" :label-width="formLabelWidth">
          <!--<el-input v-model="policyTimeForm.start_time" auto-complete="off"></el-input>-->
          <template>
            <el-time-picker
              v-model="policyTimeForm.start_time">
            </el-time-picker>
          </template>
        </el-form-item>
        <el-row>
        <el-col :span="4">
        <el-form-item label="延迟开始" :label-width="formLabelWidth">
          <!--<el-input v-model="policyTimeForm.start_now" auto-complete="off"></el-input>-->
          <template>
            <!-- `checked` 为 true 或 false -->
            <el-checkbox v-model="policyTimeForm.start_now"></el-checkbox>
          </template>
        </el-form-item>
        </el-col>
        <el-col :span="20">
        <el-form-item :label-width="formLabelWidth" style="margin-left: -120px" >
          <!--<el-input v-model="policyTimeForm.start_date" auto-complete="off"></el-input>-->
          <template>
            <el-date-picker
              v-model="policyTimeForm.start_date"
              type="date"
              :picker-options="pickerOptionsForDate" :disabled="!policyTimeForm.start_now">
            </el-date-picker>
          </template>
        </el-form-item>
        </el-col>
        </el-row>
      </el-form>
      <!--<div class="line"></div>-->
      <el-form :model="policyRecurringForm">
        <el-form-item label="重复策略" :label-width="formLabelWidth">
          <!--<el-input v-model="policyRecurringForm.interval" auto-complete="off"></el-input>-->
          <template>
            <el-radio class="radio" v-model="policyRecurringForm.interval" label="1">仅一次</el-radio>
            <el-radio class="radio" v-model="policyRecurringForm.interval" label="2">天</el-radio>
            <el-radio class="radio" v-model="policyRecurringForm.interval" label="3">周</el-radio>
            <el-radio class="radio" v-model="policyRecurringForm.interval" label="4">月</el-radio>
          </template>

        </el-form-item>
        <el-form-item v-if="policyRecurringForm.interval != 1" label="备份频率" :label-width="formLabelWidth">
          <el-input type="number" v-model="policyRecurringForm.recurring_options_every" auto-complete="off"></el-input>
        </el-form-item>
        <el-form-item v-if="policyRecurringForm.interval == 3" label="周选项" :label-width="formLabelWidth">
          <!--<el-input v-model="policyRecurringForm.recurring_options_week" auto-complete="off"></el-input>-->
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
      <el-form :model="policyProtectionForm">
        <el-form-item label="备份保存策略" :label-width="formLabelWidth">
          <!--<el-input v-model="policyProtectionForm.protectionType" auto-complete="off"></el-input>-->
          <template>
            <el-radio class="radio" v-model="policyProtectionForm.protectionType" label="1">天</el-radio>
            <el-radio class="radio" v-model="policyProtectionForm.protectionType" label="2">周</el-radio>
            <el-radio class="radio" v-model="policyProtectionForm.protectionType" label="3">月</el-radio>
            <el-radio class="radio" v-model="policyProtectionForm.protectionType" label="4">永久保存</el-radio>
          </template>
        </el-form-item>
        <el-form-item v-if="policyProtectionForm.protectionType != 4" label="备份保存周期" :label-width="formLabelWidth">
          <el-input type="number" v-model="policyProtectionForm.protection" auto-complete="off"></el-input>
        </el-form-item>
      </el-form>
      <div slot="footer" class="dialog-footer">
        <el-button @click="dialogNewPolicyVisible = false">取 消</el-button>
        <el-button type="primary" @click="dialogNewPolicyVisible = false">确 定</el-button>
      </div>
    </el-dialog>
  </el-row>
</template>
<script>
  import {reqGetPolicyList} from '../../api/api'
  export default{
    props: ["roles", "groups"],
    data(){
      return {
        loading: false,
        filters: {
          name: '',
        },
        sysUserName: '',
        policys: [],
        policyBaseForm: {
          name: '',
          description: ''
        },
        policyTimeForm: {
          start_time: '',
          start_now: false,
          start_date: ''
        },
        policyRecurringForm: {
          interval: '1',
          recurring_options_every: '',
          recurring_options_week: []
        },
        policyProtectionForm: {
          protectionType: '1',
          protection: ''
        },
        policy:{},
        dialogNewPolicyVisible: false,
        formLabelWidth: '120px',
        pickerOptionsForDate: {
        disabledDate(time) {
          return time.getTime() < Date.now() - 8.64e7;
        }
      },
      }
    },
    created(){
    },
    watch:{
      //policyTimeForm.start_now: function(o, n){
      //}
    },
    methods: {
      initialPolicyForms() {
        this.policyBaseForm.name = '',
        this.policyBaseForm.description = '',
        this.policyTimeForm.start_time = '',
        this.policyTimeForm.start_now = false,
        this.policyTimeForm.start_date = '',
        this.policyRecurringForm.interval = '1',
        this.policyRecurringForm.recurring_options_every = '',
        this.policyRecurringForm.recurring_options_week = [],
        this.policyProtectionForm.protectionType = '1',
        this.policyProtectionForm.protection = ''
      },
      getPolicys(username){
        let params = {
          user: username,
        };
        reqGetPolicyList(params).then(res => {
          console.log(res);
        },err => {
          console.log(err);
        });
      },
      newPolicy(){
        this.dialogNewPolicyVisible = true;
        this.initialPolicyForms();
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
