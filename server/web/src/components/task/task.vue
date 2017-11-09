<style>
  .table-expand {
    font-size: 0;
  }
  .table-expand label {
    width: 90px;
    color: #99a9bf;
  }
  .table-expand .el-form-item {
    margin-right: 0;
    margin-bottom: 0;
    width: 50%;
  }
</style>
<template>
  <el-row class="warp">
    <el-col :span="24" class="warp-breadcrum">
      <el-breadcrumb separator="/">
        <el-breadcrumb-item :to="{ path: '/' }"><b>首页</b></el-breadcrumb-item>
        <el-breadcrumb-item>任务管理</el-breadcrumb-item>
      </el-breadcrumb>
    </el-col>

    <el-col :span="24" class="warp-main">
      <!--工具条-->
      <el-col :span="24" class="toolbar" style="padding-bottom: 0px;">
        <el-button type="danger" @click="batchDelete" :disabled="this.sels.length===0">
          批量删除
        </el-button>
        <el-button type="primary" @click="showAddDialog" style="margin-left: 5px">新建</el-button>
        <!--<el-button type="primary" @click="exportExcel" style="margin-left: 5px">导出</el-button>-->
        <el-form :inline="true" :model="filters" style="float:right; margin-right: 5px">
          <el-form-item>
            <el-input v-model="filters.name" placeholder="任务名" style="min-width: 240px;"></el-input>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="getWorker">查询</el-button>
          </el-form-item>
        </el-form>
      </el-col>

      <!--列表-->
      <el-table :data="workers" highlight-current-row v-loading="listLoading" @selection-change="selsChange"
                style="width: 100%;" max-height="750">
        <el-table-column type="selection"></el-table-column>
        <!--<el-table-column type="index" width="60">-->
        <!--</el-table-column>-->
        <el-table-column type="expand">
          <template slot-scope="props">
            <el-form label-position="left" inline class="table-expand">
              <el-form-item label="任务名">
                <span>{{ props.row.name }}</span>
              </el-form-item>
              <el-form-item label="创建时间">
                <span>{{ props.row.create_at }}</span>
              </el-form-item>
              <el-form-item label="更新时间">
                <span>{{ props.row.updated_at }}</span>
              </el-form-item>
              <el-form-item label="开始时间">
                <span>{{ props.row.start_time }}</span>
              </el-form-item>
              <el-form-item label="源地址">
                <span>{{ props.row.source }}</span>
              </el-form-item>
              <el-form-item label="目的地址">
                <span>{{ props.row.destination }}</span>
              </el-form-item>
            </el-form>
          </template>
        </el-table-column>
        <el-table-column prop="name" label="任务名"sortable>
        </el-table-column>
        <el-table-column prop="source" label="源地址">
        </el-table-column>
        <el-table-column prop="destination" label="目标地址">
        </el-table-column>
        <el-table-column prop="start_time" label="开始时间" sortable>
        </el-table-column>
        <!--<el-table-column prop="description" label="描述" sortable>-->
        <!--</el-table-column>-->
        <el-table-column label="操作" width="200">
          <template slot-scope="scope">
            <el-button size="small" @click="showEditDialog(scope.$index,scope.row)">
              <i class="iconfont icon-modiffy"></i>
            </el-button>
            <el-button type="danger" @click="delGroup(scope.$index,scope.row)" size="small">
              <i class="iconfont icon-delete"></i>
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!--编辑框 -->
      <el-dialog title="编辑" v-model="editFormVisible" :close-on-click-modal="false">
        <el-form :model="editForm" label-width="100px" :rules="editFormRules" ref="editForm">
          <el-form-item prop="name" label="主机名">
            <el-input v-model="editForm.name" auto-complete="off"></el-input>
          </el-form-item>
          <el-form-item prop="start_time" label="开始时间">
            <el-date-picker type="date" placeholder="选择日期" v-model="editForm.start_time"></el-date-picker>
          </el-form-item>
          <el-form-item prop="source" label="源地址">
            <el-input v-model="editForm.source" auto-complete="off"></el-input>
          </el-form-item>
          <el-form-item prop="destination" label="目标地址">
            <el-input v-model="editForm.destination" auto-complete="off"></el-input>
          </el-form-item>
          <el-form-item prop="description" label="描述">
            <el-input type="textarea" v-model="editForm.description" :rows="4"></el-input>
          </el-form-item>
        </el-form>
        <div slot="footer" class="dialog-footer">
          <el-button @click.native="editFormVisible = false">取消</el-button>
          <el-button type="primary" @click.native="editSubmit" :loading="editLoading">提交</el-button>
        </div>
      </el-dialog>

      <!--新建框-->
      <el-dialog title="新建" v-model="addFormVisible" :close-on-click-modal="false">
        <el-form :model="addForm" label-width="100px" :rules="editFormRules" ref="editForm">
          <el-form-item prop="name" label="主机名">
            <el-input v-model="addForm.name" auto-complete="off"></el-input>
          </el-form-item>
          <el-form-item prop="start_time" label="开始时间">
            <el-date-picker type="date" placeholder="选择日期" v-model="addForm.start_time"></el-date-picker>
          </el-form-item>
          <el-form-item prop="source" label="源地址">
            <el-input v-model="addForm.source" auto-complete="off"></el-input>
          </el-form-item>
          <el-form-item prop="destination" label="目标地址">
            <el-input v-model="addForm.destination" auto-complete="off"></el-input>
          </el-form-item>
          <el-form-item prop="description" label="描述">
            <el-input type="textarea" v-model="addForm.description" :rows="4"></el-input>
          </el-form-item>
        </el-form>
        <div slot="footer" class="dialog-footer">
          <el-button @click.native="addFormVisible = false">取消</el-button>
          <el-button type="primary" @click.native="addSubmit" :loading="addLoading">提交</el-button>
        </div>
      </el-dialog>

    </el-col>
  </el-row>
</template>
<script>
  import { reqGetWorkerList} from '../../api/api';
  import {bus} from '../../bus.js'
  export default {
    created(){
      bus.$on('setUserName', (text) => {
        console.log("text");
        console.log(text);
        this.sysUserName = text;
      })
    },
    data() {
      var validateIp = (rule, value, callback) => {
        var ip = /^([1-9]|[1-9]\d|1\d\d|2[0-4]\d|25[0-5])(\.(\d|[1-9]\d|1\d\d|2[0-4]\d|25[0-5])){3}$/
        if (!ip.test(value)) {
          callback(new Error('输入IP格式不正确，请重新输入！'));
        }else{
          callback();
        }
      };
      return {
        sysUserName: '',
        filters: {
          name: ''
        },
        options:[{
          value: '1',
          label: '1'
        },{
          value: '2',
          label: '2'
        },{
          value: '3',
          label: '3'
        },{
          value: '4',
          label: '4'
        }],
        listLoading: false,
        isVisible:true,
        workers:[],
        total: 0,
        page: 1,
        per_page: 10,
        sels: [], //列表选中列

        //编辑相关数据
        editFormVisible: false,//编辑界面是否显示
        editLoading: false,
        editFormRules: {
          name: [
            {required: true, message: '请输入主机名', trigger: 'blur'}
          ],
          ip: [
            {required: true, validator: validateIp, trigger: 'blur'}
          ],
          owner: [
            {required: true, message: '请输入角色', trigger: 'blur'}
          ],
          port: [
            {required: true, message: '请输入'}
          ],
          description: [
            {required: true, message: '请输入描述', trigger: 'blur'}
          ]
        },
        editForm: {
          id: 0,
          name: '',
          ip: '',
          owner: '',
          port: '',
          description: ''
        },

        //新增数据相关
        addFormVisible: false,
        addLoading: false,
        addForm: {
          name: '',
          ip: '',
          owner: '',
          port: '',
          description: ''
        },
      }
    },
    methods: {
      handleCurrentChange(val) {
        //console.log(`当前 ${val} 页`)
        this.page = val;
        this.getWorker();
      },
      handleSizeChange(val) {
        //console.log(`每页 ${val} 条`)
        this.per_page = val;
        this.getWorker();
      },
      //获取用户列表
      getWorker: function () {
        let para = {
          user: this.sysUserName,
//          page: this.page,
//          pagesize: this.per_page,
//          ip: this.filters.ip
        };
        this.listLoading = true;
        this.isVisible = false;
        //NProgress.start();
        reqGetWorkerList(para).then((res) => {
          this.total = res.data.total;
          this.workers = res.data.workers;
          this.listLoading = false;
          this.isVisible = true;
          //NProgress.done();
        }).catch(err=>{
          this.listLoading = false;
          if (err.response.status == 401) {
            this.$message({
              message: "请重新登录",
              type: 'error'
            });
            this.$router.push({ path: '/login' });
          }else{
            this.$message({
              message: "获取数据失败",
              type: 'error'
            });
          }
        });
      },

      //====编辑相关====
      //显示编辑界面
      showEditDialog: function (index, row) {
        this.editFormVisible = true;
        this.editForm = Object.assign({}, row);
      },
      //编辑
      editSubmit: function () {
        this.$refs.editForm.validate((valid) => {
          if (valid) {
            this.$confirm('确认提交吗？', '提示', {}).then(() => {
              this.editLoading = true;
              //NProgress.start();
              let para = Object.assign({}, this.editForm);
              reqEditWorker(para).then((res) => {
                this.editLoading = false;
                //NProgress.done();
                this.$message({
                  message: '提交成功',
                  type: 'success'
                });
                this.$refs['editForm'].resetFields();
                this.editFormVisible = false;
                this.getWorker();
              });
            });
          }
          else{
            alert('输入有误，提交失败')
          }
        });
      },

      //====新建相关====
      //显示新建界面
      showAddDialog: function (index, row) {
        this.addFormVisible = true;
        this.addForm = {
          user: this.sysUserName,
          name: '',
          ip: '',
          owner: '',
          port: '',
          description: ''
        };
      },
      addSubmit: function () {
        this.$refs.addForm.validate((valid) => {
          if (valid) {
            this.addLoading = true;
            //NProgress.start();
            let para = Object.assign({}, this.addForm);
            reqAddWorker(para).then((res) => {
              this.addLoading = false;
              //NProgress.done();
              this.$message({
                message: '提交成功',
                type: 'success'
              });
              this.$refs['addForm'].resetFields();
              this.addFormVisible = false;
              this.getWorker();
            });
          }
          else{
            alert('输入有误，提交失败')
          }
        });
      },
      //====删除相关====
      //单个删除
      delGroup: function (index, row) {
        this.$confirm('确认删除该记录吗?', '提示', {type: 'warning'}).then(() => {
          this.listLoading = true;
          //NProgress.start();
          let para = {id: row.id};
          reqDelWorker(para).then((res) => {
            this.listLoading = false;
            //NProgress.done();
            this.$message({
              message: '删除成功',
              type: 'success'
            });
            this.getWorker();
          });
        }).catch(() => {
        });
      },
      //勾选
      selsChange: function (sels) {
        this.sels = sels;
      },
      //批量删除
      batchDelete: function () {
        var ids = this.sels.map(item => item.id).toString();
        this.$confirm('确认删除选中记录吗？', '提示', {
          type: 'warning'
        }).then(() => {
          this.listLoading = true;
          //NProgress.start();
          let para = {ids: ids};
          reqBatchDelWorker(para).then((res) => {
            this.listLoading = false;
            //NProgress.done();
            this.$message({
              message: '删除成功',
              type: 'success'
            });
            this.getWorker();
          });
        }).catch(() => {

        });
      },

    },
    mounted() {
      var accessInfo = sessionStorage.getItem('access-user');
      if (accessInfo) {
        accessInfo = JSON.parse(accessInfo);
        this.sysUserName = accessInfo.username || '';
      }
      this.getWorker();
    }
  }
</script>
