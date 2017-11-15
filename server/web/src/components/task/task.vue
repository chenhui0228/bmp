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
    width: 46%;
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

    <el-col :span="24" style="margin-top:5px;margin-bottom: 10px">
      <el-tabs value="backup" @tab-click="handleClick">
        <el-tab-pane label="备份任务" name="backup"></el-tab-pane>
        <el-tab-pane label="恢复任务" name="recover"></el-tab-pane>
      </el-tabs>
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
            <el-button type="primary" @click="getTasks">查询</el-button>
          </el-form-item>
        </el-form>
      </el-col>

      <!--列表-->
      <el-table :data="tasks" highlight-current-row v-loading="listLoading" @selection-change="selsChange"
                style="width: 100%;" max-height="750">
        <el-table-column type="selection"></el-table-column>
        <!--<el-table-column type="index" width="60">-->
        <!--</el-table-column>-->
        <el-table-column type="expand">
          <template slot-scope="props">
            <el-form label-position="left" inline class="table-expand">
              <el-form-item label="任务名">
                <span>{{ props.row.task.name }}</span>
              </el-form-item>
              <el-form-item label="任务描述">
                <span>{{ props.row.task.description }}</span>
              </el-form-item>
              <el-form-item label="创建时间">
                <span>{{ props.row.task.created_at | timeStamp2datetime }}</span>
              </el-form-item>
              <el-form-item label="更新时间">
                <span>{{ props.row.task.updated_at | timeStamp2datetime }}</span>
              </el-form-item>
              <el-form-item label="任务策略">
                <span>{{ props.row.policy.name }}</span>
              </el-form-item>
              <el-form-item label="作业机">
                <span>{{ props.row.worker.name }}</span>
              </el-form-item>
              <el-form-item label="源地址">
                <span>{{ props.row.task.source }}</span>
              </el-form-item>
              <el-form-item label="目的地址">
                <span>{{ props.row.task.destination }}</span>
              </el-form-item>
            </el-form>
          </template>
        </el-table-column>
        <el-table-column prop="task.name" label="任务名"sortable>
        </el-table-column>
        <el-table-column prop="task.source" label="源地址">
        </el-table-column>
        <el-table-column prop="task.destination" label="目标地址">
        </el-table-column>
        <el-table-column prop="policy.name" label="任务策略" v-if="isVisible" sortable>
        </el-table-column>
        <!--<el-table-column prop="description" label="描述" sortable>-->
        <!--</el-table-column>-->
        <el-table-column label="操作" width="200">
          <template slot-scope="scope">
            <el-button type="text" icon="information" @click="showEditDialog(scope.$index,scope.row)">
            </el-button>
            <el-button type="text" icon="edit" @click="showEditDialog(scope.$index,scope.row)">
              <!--<i class="iconfont icon-modiffy"></i>-->
            </el-button>
            <el-button type="text" icon="delete" style="color:red;" @click="delTask(scope.$index,scope.row)" size="small">
              <!--<i class="iconfont icon-delete"></i>-->
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!--工具条-->
      <el-col :span="24" class="toolbar" style="margin-top: 5px;">
        <el-pagination
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
          :page-sizes="[10, 15, 20, 30]"
          :page-size="per_page"
          :current-page="page"
          :total="total" style="float:right;margin-right: 5px">
        </el-pagination>
      </el-col>

      <!--编辑框 -->
      <el-dialog title="编辑" v-model="editFormVisible" :close-on-click-modal="false" beforeClose="cancelEdit">
        <el-form :model="editForm" label-width="100px" :rules="editFormRules" ref="editForm">
          <el-form-item prop="name" label="任务名">
            <el-input v-model="editForm.name" auto-complete="off"></el-input>
          </el-form-item>
          <el-form-item prop="policy" label="任务策略">
            <el-select v-model="editForm.policy_id" clearable placeholder="请选择">
              <el-option
                v-for="policy in policies"
                :key="policy.id"
                :label="policy.name"
                :value="policy.id">
              </el-option>
            </el-select>
          </el-form-item>
          <el-form-item prop="worker" label="作业机">
            <el-select v-model="editForm.worker_id" clearable placeholder="请选择">
              <el-option
                v-for="worker in workers"
                :key="worker.id"
                :label="worker.name"
                :value="worker.id">
              </el-option>
            </el-select>
          </el-form-item>
          <el-form-item prop="source" label="源地址">
            <el-input v-model="editForm.source" auto-complete="off"></el-input>
          </el-form-item>
          <el-form-item prop="volume" label="卷">
            <el-select v-model="editForm.volume_id" clearable placeholder="请选择" @change="handleChange">
              <el-option
                v-for="volume in volumes"
                :key="volume.id"
                :label="volume.name"
                :value="volume.id">
              </el-option>
            </el-select>
          </el-form-item>
          <el-form-item prop="destination" label="目标地址">
            <el-input v-model="editForm.destination" auto-complete="off"></el-input>
          </el-form-item>
          <el-form-item prop="script_path" label="脚本地址">
            <el-input v-model="editForm.script_path" auto-complete="off"></el-input>
          </el-form-item>
          <el-form-item prop="description" label="描述">
            <el-input type="textarea" v-model="editForm.description" :rows="2"></el-input>
          </el-form-item>
        </el-form>
        <div slot="footer" class="dialog-footer">
          <el-button @click.native="cancelEdit">取消</el-button>
          <el-button type="primary" @click.native="editSubmit" :loading="editLoading">提交</el-button>
        </div>
      </el-dialog>

      <!--新建框-->
      <el-dialog title="新建" v-model="addFormVisible" :close-on-click-modal="false" :beforeClose="cancelAdd">
        <el-form :model="addForm" label-width="100px" :rules="editFormRules" ref="addForm">
          <el-form-item prop="name" label="任务名">
            <el-input v-model="addForm.name" auto-complete="off"></el-input>
          </el-form-item>
          <el-form-item prop="policy" label="任务策略">
            <el-select v-model="addForm.policy_id" clearable placeholder="请选择">
              <el-option
                v-for="policy in policies"
                :key="policy.id"
                :label="policy.name"
                :value="policy.id">
              </el-option>
            </el-select>
          </el-form-item>
          <el-form-item prop="worker" label="作业机">
            <el-select v-model="addForm.worker_id" clearable placeholder="请选择">
              <el-option
                v-for="worker in workers"
                :key="worker.id"
                :label="worker.name"
                :value="worker.id">
              </el-option>
            </el-select>
          </el-form-item>
          <el-form-item prop="source" label="源地址">
            <el-input v-model="addForm.source" auto-complete="off"></el-input>
          </el-form-item>
          <el-form-item prop="volume" label="卷">
            <el-select v-model="addForm.volume" clearable placeholder="请选择" @change="handleChange">
              <el-option
                v-for="volume in volumes"
                :key="volume.id"
                :label="volume.name"
                :value="volume.id">
              </el-option>
            </el-select>
          </el-form-item>
          <el-form-item prop="destination" label="目标地址">
            <el-input v-model="addForm.destination" auto-complete="off"></el-input>
          </el-form-item>
          <el-form-item prop="script_path" label="脚本地址">
            <el-input v-model="addForm.script_path" auto-complete="off"></el-input>
          </el-form-item>
          <el-form-item prop="description" label="描述">
            <el-input type="textarea" v-model="addForm.description" :rows="2"></el-input>
          </el-form-item>
        </el-form>
        <div slot="footer" class="dialog-footer">
          <el-button @click.native="cancelAdd">取消</el-button>
          <el-button type="primary" @click.native="addSubmit" :loading="addLoading">提交</el-button>
        </div>
      </el-dialog>

    </el-col>
  </el-row>
</template>
<script>
  import { reqGetTaskList, reqAddTask, reqEditTask, reqDelTask, reqTaskAction, reqGetVolumeList, reqGetWorkerList, reqGetPolicyList} from '../../api/api';
  import {bus} from '../../bus.js'
  export default {
    data() {
      return {
        sysUserName: '',
        filters: {
          name: ''
        },
        listLoading: false,
        isVisible:true,
        tasks:[],
        total: 0,
        page: 1,
        per_page: 10,
        offset: 0,
        task_type: 'backup',
        sels: [], //列表选中列
        workers:[],
        volumes:[],
        policies:[],

        //编辑相关数据
        editFormVisible: false,//编辑界面是否显示
        editLoading: false,
        editFormRules: {
//          name: [
//            {required: true, message: '请输入主机名', trigger: 'blur'}
//          ],
//          owner: [
//            {required: true, message: '请输入角色', trigger: 'blur'}
//          ],
//          port: [
//            {required: true, message: '请输入'}
//          ],
//          description: [
//            {required: true, message: '请输入描述', trigger: 'blur'}
//          ]
        },
        editForm: {
          id: 0,
          name: '',
          policy_id: '',
          worker_id: '',
          source: '',
          destination: '',
          description: '',
        },

        //新增数据相关
        addFormVisible: false,
        addLoading: false,
        addForm: {
//          name: '',
//          source: '',
//          destination: '',
//          policy_id: '',
//          description: '',
//          worker_id: '',
//          volume: '',
        },
      }
    },
    methods: {
      handleClick(tag) {
        if(tag.index === '1') {
          this.task_type = 'recover';
          this.isVisible = false;
        }else{
          this.task_type = 'backup';
          this.isVisible = true;
        }
      },
      handleCurrentChange(val) {
        //console.log(`当前 ${val} 页`)
        this.page = val;
        this.getTasks();
      },
      handleSizeChange(val) {
        //console.log(`每页 ${val} 条`)
        this.per_page = val;
        this.getTasks();
      },
      //获取用户列表
      getTasks: function () {
        this.offset = this.per_page * (this.page - 1);
        let para = {
          user: this.sysUserName,
          limit: this.per_page,
          offset: this.offset,
//          ip: this.filters.ip
        };
        this.listLoading = true;
        this.isVisible = false;
        //NProgress.start();
        reqGetTaskList(para).then((res) => {
          this.total = res.data.total;
          this.tasks = res.data.tasks;
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
      //处理显示
      beforeShow: function (row) {
        let source = row.task.source;
        let destination = row.task.destination;
        source = source.match(/\/\/(\S*)/)[1];
        let volumeName = destination.match(/\/\/(\S*)\//)[1];
        destination = destination.match(/\/(\S*)/)[1];
        let volume = {};
        volume = this.volumes.find((volume)=>{
          return volume.name === volumeName;
        });
        row.task.volume_id = volume.id;
        row.task.source = source;
        row.task.destination = destination;
      },
      //取消编辑
      cancelEdit: function () {
        this.editFormVisible = false;
        this.$refs['editForm'].resetFields();
        this.getTasks();
      },
      //显示编辑界面
      showEditDialog: function (index, row) {
        this.editFormVisible = true;
        this.beforeShow(row);
        this.editForm = Object.assign({}, row.task);
        console.log(this.editForm);
      },
      //编辑
      editSubmit: function () {
        this.$refs.editForm.validate((valid) => {
          if (valid) {
            this.$confirm('确认提交吗？', '提示', {}).then(() => {
              this.editLoading = true;
              //NProgress.start();
              let user_para = {
                user: this.sysUserName,
              };
              let para = Object.assign({}, this.editForm);
              if(para.type === "backup"){
                para.source = 'file://' + para.source;
                para.destination = 'glusterfs:/' + para.destination;
              }
              reqEditTask(para.id, user_para, para).then((res) => {
                this.editLoading = false;
                //NProgress.done();
                this.$message({
                  message: '修改成功',
                  type: 'success'
                });
                this.$refs['editForm'].resetFields();
                this.editFormVisible = false;
                this.getTasks();
              }).catch(err=>{
                this.editLoading = false;
                this.$message({
                  message: '修改失败：',
                  type: 'error'
                });
                this.$refs['editForm'].resetFields();
                this.editFormVisible = false;
                this.getTasks();
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
          name: '',
          policy_id: '',
          worker_id: '',
          source: '',
          destination: '',
          description: '',
        };
      },
      //取消提交
      cancelAdd: function () {
        this.addFormVisible = false;
        this.$refs['addForm'].resetFields();
      },
      handleChange: function (value) {
        if(typeof(value) !== "undefined"){
          let volume = {};
          volume = this.volumes.find((volume)=>{
            return volume.id === value;
          });
          if(this.addFormVisible){
            this.addForm.destination = '';
            this.addForm.destination = '/' + this.addForm.destination + volume.name + '/';
          }else if(this.editFormVisible) {
            this.editForm.destination = '';
            this.editForm.destination = '/' + this.editForm.destination + volume.name + '/';
          }
        }
      },

      addSubmit: function () {
        this.$refs.addForm.validate((valid) => {
          if (valid) {
            this.addLoading = true;
            //NProgress.start();
            let user = {
              user: this.sysUserName,
            };
            let para = Object.assign({}, this.addForm);
            para.type = this.task_type;

            if(para.type === "backup"){
              para.source = 'file://' + para.source;
              para.destination = 'glusterfs:/' + para.destination;
            }
//            console.log("!!!####!!!");
//            console.log(para);

            reqAddTask(user, para).then((res) => {
              this.addLoading = false;
              //NProgress.done();
              this.$message({
                message: '添加成功',
                type: 'success'
              });
              this.$refs['addForm'].resetFields();
              this.addFormVisible = false;
              this.getTasks();
            }).catch(err=>{
              this.addLoading = false;
              this.$message({
                message: '添加失败',
                type: 'error'
              });
              console.log(err.message)
              this.$refs['addForm'].resetFields();
              this.addFormVisible = false;
            });
          }
          else{
            alert('输入有误，提交失败')
          }
        });
      },
      //====删除相关====
      //单个删除
      delTask: function (index, row) {
        this.$confirm('确认删除该记录吗?', '提示', {type: 'warning'}).then(() => {
          this.listLoading = true;
          //NProgress.start();
          let para = {user: this.sysUserName};
          reqDelTask(row.task.id, para).then((res) => {
            this.listLoading = false;
            //NProgress.done();
            this.$message({
              message: '删除成功',
              type: 'success'
            });
            this.getTasks();
          });
        }).catch(() => {
          this.listLoading = false;
          this.$message({
            message: '删除失败',
            type: 'error'
          });
        });
      },
      //勾选
      selsChange: function (sels) {
        this.sels = sels;
      },
      //批量删除
      batchDelete: function () {
//        var ids = this.sels.map(item => item.id).toString();
//        this.$confirm('确认删除选中记录吗？', '提示', {
//          type: 'warning'
//        }).then(() => {
//          this.listLoading = true;
//          //NProgress.start();
//          let para = {ids: ids};
//          reqBatchDelWorker(para).then((res) => {
//            this.listLoading = false;
//            //NProgress.done();
//            this.$message({
//              message: '删除成功',
//              type: 'success'
//            });
//            this.getTasks();
//          });
//        }).catch(() => {
//
//        });
      },

    },
    mounted() {
      var accessInfo = sessionStorage.getItem('access-user');
      if (accessInfo) {
        accessInfo = JSON.parse(accessInfo);
        this.sysUserName = accessInfo.username || '';
      }
      let para = {
        user: this.sysUserName
      };
      reqGetWorkerList(para).then(res=>{
        this.workers = res.data.workers;
      });
      reqGetVolumeList(para).then(res=>{
        this.volumes = res.data.volumes;
      });
      reqGetPolicyList(para).then(res=>{
        this.policies = res.data.policies;
      });
      this.getTasks();
    }
  }
</script>
