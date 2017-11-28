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
  .custom_size .el-dialog {
    width: 85%;
  }
  .el-table-row {
    cursor: pointer;
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
        <el-button type="primary" v-if="isBackupTask" @click="showAddDialog" style="margin-left: 5px">新建</el-button>
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
      <el-table :data="tasks" highlight-current-row
                v-loading="listLoading"
                @selection-change="selsChange"
                @row-dblclick="taskStateDetail"
                style="width: 100%;" max-height="750"
                row-class-name="el-table-row">
        <el-table-column type="selection"></el-table-column>
        <el-table-column type="expand">
          <template slot-scope="props">
            <el-form label-position="left" inline class="table-expand">
              <el-form-item label="任务名">
                <span>{{ props.row.task.name }}</span>
              </el-form-item>
              <el-form-item v-if="props.row.task.description" label="任务描述">
                <span>{{ props.row.task.description }}</span>
              </el-form-item>
              <el-form-item label="创建时间">
                <span>{{ props.row.task.created_at | timeStamp2datetime }}</span>
              </el-form-item>
              <el-form-item label="更新时间">
                <span>{{ props.row.task.updated_at | timeStamp2datetime }}</span>
              </el-form-item>
              <el-form-item label="任务策略" v-if="isBackupTask">
                <span>{{ props.row.policy.name }}</span>
              </el-form-item>
              <el-form-item label="作业机">
                <span>{{ props.row.worker.name }}  (IP:{{ props.row.worker.ip }})</span>
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
        <el-table-column prop="task.name" label="任务名" width="taskname_label_width" show-overflow-tooltip>
        </el-table-column>
        <el-table-column prop="policy.name" label="任务策略"  v-if="isBackupTask" sortable width="180rem">
        </el-table-column>
        <el-table-column prop="worker.name" label="作业机" sortable width="180rem">
        </el-table-column>
        <el-table-column prop="task.state" label="状态" width="120rem">
          <template slot-scope="scope">
            <span v-if="scope.row.task.state == 'waiting'" style="color: #f7c410">等待...</span>
            <span v-else-if="scope.row.task.state == 'running_w' || scope.row.task.state == 'running_s'" style="color: blue">执行中...</span>
            <span v-else-if="scope.row.task.state == 'stopped'" style="color: red">已停止</span>
            <span v-else-if="scope.row.task.state == 'end'" style="color: green">完成</span>
            <span v-else style="color: red">未知</span>
          </template>
        </el-table-column>
        <el-table-column
          label="任务进度"
          width="150rem">
          <template slot-scope="scope">
            <span v-if="scope.row.state">
            <el-progress v-if="(scope.row.task.state == 'running_w' || scope.row.task.state == 'running_s' || scope.row.task.state == 'end') && scope.row.state.process" :percentage="parseInt(scope.row.state.process)"></el-progress>
            </span>
            <span v-else>--</span>
          </template>
        </el-table-column>
        <el-table-column label="开始时间" sortable width="180rem">
          <template slot-scope="scope">
            <span v-if="scope.row.state">
              <span v-if="scope.row.task.state == 'running_w' || scope.row.task.state == 'running_s' || scope.row.task.state == 'end'">{{ scope.row.state.start_time | dateStampFormat }}</span>
            </span>
            <span v-else>--</span>
          </template>
        </el-table-column>
        <el-table-column label="文件大小" width="100rem">
          <template slot-scope="scope">
          <span v-if="scope.row.state">
            <span v-if="scope.row.task.state == 'running_w' || scope.row.task.state == 'running_s' || scope.row.task.state == 'end'">{{ scope.row.state.total_size | Bytes  }}</span>
            <span v-else>--</span>
          </span>
          </template>
        </el-table-column>
        <el-table-column prop="user" label="创建人" width="150rem">
        </el-table-column>
        <el-table-column label="操作" width="">

          <template slot-scope="scope">
            <svg class="icon" aria-hidden="true" @click="showEditDialog(scope.$index,scope.row)" v-if="isBackupTask">
              <use xlink:href="#icon-modify"></use>
            </svg>
            <svg class="icon" aria-hidden="true" @click="delTask(scope.$index,scope.row)">
              <use xlink:href="#icon-delete"></use>
            </svg>
            <el-tooltip content="立即执行" placement="top" v-if="scope.row.task.state == 'waiting' || scope.row.task.state == 'stopped'" >
              <svg class="icon" aria-hidden="true" @click="taskActions(scope.$index,scope.row,'start')">
                <use xlink:href="#icon-exec"></use>
              </svg>
            </el-tooltip>
            <el-tooltip content="停止" placement="top" v-if="scope.row.task.state == 'waiting' || scope.row.task.state == 'running_w' || scope.row.task.state == 'running_s'"><!--没暂停就显示暂停按钮-->
              <svg class="icon" aria-hidden="true" @click="taskActions(scope.$index,scope.row,'stop')">
                <use xlink:href="#icon-stop"></use>
              </svg>
            </el-tooltip>
            <el-tooltip content="恢复任务" placement="top" v-if="scope.row.task.state == 'stopped'">
              <svg class="icon" aria-hidden="true" @click="taskActions(scope.$index,scope.row,'resume')">
                <use xlink:href="#icon-recover"></use>
              </svg>
            </el-tooltip>
            <el-tooltip content="重新下发" placement="top" v-if="scope.row.task.state != 'stopped' && scope.row.task.state != 'running_w' && scope.row.task.state != 'running_s' && scope.row.task.state != 'waiting'">
              <svg class="icon" aria-hidden="true" @click="taskActions(scope.$index,scope.row,'resume')">
                <use xlink:href="#icon-reload"></use>
              </svg>
            </el-tooltip>
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
      <el-dialog title="编辑" v-model="editFormVisible" :close-on-click-modal="false" :beforeClose="cancelEdit">
        <el-form :model="editForm" label-width="100px" :rules="editFormRules" ref="editForm">
          <el-form-item prop="name" label="任务名">
            <el-input v-model="editForm.name" auto-complete="off"></el-input>
          </el-form-item>
          <el-form-item prop="policy" label="任务策略">
            <el-select v-model="editForm.policy_id" placeholder="请选择">
              <el-option
                v-for="policy in policies"
                :key="policy.id"
                :label="policy.name"
                :value="policy.id">
              </el-option>
            </el-select>
          </el-form-item>
          <el-form-item prop="worker" label="作业机">
            <el-select v-model="editForm.worker_id" placeholder="请选择">
              <el-option
                v-for="worker in workers"
                :key="worker.id"
                :label="worker.name"
                :value="worker.id">
              </el-option>
            </el-select>
            <span v-for="worker in workers"
                  v-if="editForm.worker_id == worker.id"
                  style="margin-left:10px; color:#99a9bf">IP: {{ worker.ip }}
            </span>
          </el-form-item>
          <el-form-item prop="source" label="源地址">
            <el-input v-model="editForm.source" auto-complete="off"></el-input>
          </el-form-item>
          <el-form-item prop="volume" label="卷">
            <el-select v-model="editForm.volume_id" placeholder="请选择" @change="handleChange">
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
            <el-select v-model="addForm.policy_id" placeholder="请选择">
              <el-option
                v-for="policy in policies"
                :key="policy.id"
                :label="policy.name"
                :value="policy.id">
              </el-option>
            </el-select>
            <span v-for="policy in policies"
                  v-if="addForm.policy_id == policy.id"
                  style="margin-left:10px; color:#99a9bf">
              <span v-for="group in groups"
                    v-if="policy.group_id == group.id"
                    style="margin-left:10px; color:#99a9bf">属组：{{ group.name }}
              </span>
            </span>
          </el-form-item>
          <el-form-item prop="worker" label="作业机">
            <el-select v-model="addForm.worker_id" placeholder="请选择">
              <el-option
                v-for="worker in workers"
                :key="worker.id"
                :label="worker.name"
                :value="worker.id">
              </el-option>
            </el-select>
            <span v-for="worker in workers"
                  v-if="addForm.worker_id == worker.id"
                  style="margin-left:10px; color:#99a9bf">IP: {{ worker.ip }}
            </span>
          </el-form-item>
          <el-form-item prop="source" label="源地址">
            <el-input v-model="addForm.source" auto-complete="off"></el-input>
          </el-form-item>
          <el-form-item prop="volume" label="卷">
            <el-select v-model="addForm.volume_id" placeholder="请选择" @change="handleChange">
              <el-option
                v-for="volume in volumes"
                :key="volume.id"
                :label="volume.name"
                :value="volume.id">
              </el-option>
            </el-select>
          </el-form-item>
          <el-form-item prop="destination" label="目标地址">
            <el-input v-model="addForm.destination" auto-complete="off">
              <!--<template slot="prepend">{{ destination_prefix}}</template>-->
            </el-input>
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

      <!--任务状态框-->
      <el-dialog  class="custom_size" :title="currTaskStateTabTitle" :visible.sync="dialogTaskStateDetailTableVisible" :beforeClose="closeStateDialog">
        <el-table :data="taskStates"
                  border
                  style="margin: auto;">
          <el-table-column label="开始时间" width="200">
            <template slot-scope="scope">
              <span>{{ scope.row.start_time | timeStamp2datetime }}</span>
            </template>
          </el-table-column>
          <el-table-column label="结束时间" width="200">
            <template slot-scope="scope">
              <span>{{ scope.row.end_time | timeStamp2datetime }}</span>
            </template>
          </el-table-column>
          <el-table-column label="总大小" width="120">
            <template slot-scope="scope">
              <span>{{ scope.row.total_size | Bytes }}</span>
            </template>
          </el-table-column>
          <el-table-column label="已备份" width="120">
            <template slot-scope="scope">
              <span>{{ scope.row.current_size | Bytes }}</span>
            </template>
          </el-table-column>
          <el-table-column label="更新时间" width="200">
            <template slot-scope="scope">
              <span>{{ scope.row.updated_at | timeStamp2datetime }}</span>
            </template>
          </el-table-column>
          <el-table-column label="任务状态" width="180">
            <template slot-scope="scope">
              <span v-if="scope.row && scope.row.state == 'success'" style="color: green">已完成</span>
              <span v-else-if="scope.row && scope.row.state == 'start'" style="color: blue">执行中...</span>
              <span v-else-if="scope.row && scope.row.state == 'failed'" style="color: red">
                <el-button type="text" @click="failedMsgbox(scope.row)">失败</el-button>
              </span>
              <el-progress v-else-if="scope.row && scope.row.process" :percentage="parseInt(scope.row.process)"></el-progress>
              <span v-else-if="scope.row">--</span>
              <span v-else style="color: #F7AD01">未开始</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" min-width="180" v-if="isBackupTask">
            <template slot-scope="scope">
              <!--TODO:创建恢复任务-->
              <el-button type="text" v-if="scope.row && scope.row.state == 'success'" @click="showCreateRecoverTaskDialog(scope.row)">创建恢复任务</el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-pagination
          @size-change="taskStateHandleSizeChange"
          @current-change="taskStateHandleCurrentChange"
          :current-page="taskStateFilter.page"
          :page-sizes="[10, 15]"
          :page-size="taskStateFilter.per_page"
          layout="total, sizes, prev, pager, next, jumper"
          :total="taskState_total_rows"
          style="margin: 5px;float: right;">
        </el-pagination>
      </el-dialog>

      <!--TODO: 创建恢复任务框-->
      <el-dialog title="创建恢复任务" v-model="createRecoverTaskFormVisible" :close-on-click-modal="false">
        <el-form :model="createRecoverTaskForm" label-width="100px" ref="createRecoverTaskForm">
          <el-form-item prop="worker" label="作业机">
            <el-select v-model="createRecoverTaskForm.worker_id" placeholder="请选择">
              <el-option
                v-for="worker in workers"
                :key="worker.id"
                :label="worker.name"
                :value="worker.id">
              </el-option>
            </el-select>
            <span v-for="worker in workers"
                  v-if="addForm.worker_id == worker.id"
                  style="margin-left:10px; color:#99a9bf">IP: {{ worker.ip }}
            </span>
          </el-form-item>
          <el-form-item prop="destination" label="目标地址">
            <el-input v-model="createRecoverTaskForm.destination" auto-complete="off"></el-input>
          </el-form-item>
        </el-form>
        <div slot="footer" class="dialog-footer">
          <el-button @click.native="createRecoverTaskFormVisible = false">取消</el-button>
          <el-button type="primary" @click.native="createRecoverTask" :loading="createRecoverTaskLoading">提交</el-button>
        </div>
      </el-dialog>

    </el-col>
  </el-row>
</template>
<script>
  import { reqGetTaskList, reqAddTask, reqEditTask, reqDelTask, reqTaskAction, reqGetVolumeList,
    reqGetWorkerList, reqGetPolicyList, reqBackupStates, reqBackupStatesDetail,reqGetGroupList } from '../../api/api';
  import {bus} from '../../bus.js'
  import util from '../../common/util'
  export default {
    data() {
      return {
        sysUserName: '',
        filters: {
          name: ''
        },
        listLoading: false,
        isBackupTask:true,
        taskname_label_width: '180rem',
        tasks:[],
        total: 0,
        page: 1,
        per_page: 10,
        offset: 0,
        task_type: 'backup',
        volumeName: '',
        sels: [], //列表选中列
        workers:[],
        volumes:[],
        policies:[],

        //TODO: 创建恢复任务相关数据
        createRecoverTaskLoading: false,
        createRecoverTaskFormVisible: false,
        currentWatchingTask: [],
        createRecoverTaskForm: {},

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

        //任务详情相关数据
        dialogTaskStateDetailTableVisible: false,
        currTaskStateTabTitle: '',
        taskStates: [],
        currTaskRow: '',
        taskStateFilter:{
          page: 0,
          per_page: 15,
        },
        taskState_total_rows: 0,
        //操作按钮相关数据
        isPause: false,
        intervalTask: '',
        groups: [],
      }
    },
    created() {

    },
    beforeDestroy() {
        clearInterval(this.intervalTask)
    },
    methods: {
      handleClick(tag) {
        this.page = 1;
        this.per_page = 10;
        this.offset = 0;
        this.tasks = [];
        if(tag.index === '1') {
          this.task_type = 'recover';
          this.isBackupTask = false;
          this.taskname_label_width = '250rem';
          this.getTasks('recover');
        }else{
          this.task_type = 'backup';
          this.taskname_label_width = '180rem';
          this.isBackupTask = true;
          this.getTasks();
        }
      },
      handleCurrentChange(val) {
        //console.log(`当前 ${val} 页`)
        this.page = val;
        this.getTasks(this.task_type);
      },
      handleSizeChange(val) {
        //console.log(`每页 ${val} 条`)
        this.per_page = val;
        this.getTasks(this.task_type);
      },
      //获取任务列表
      getTasks: function (type='backup') {
        this.offset = this.per_page * (this.page - 1);
        let para = {
          user: this.sysUserName,
          type: type,
          limit: this.per_page,
          offset: this.offset,
//          ip: this.filters.ip
        };
        this.listLoading = true;
        //NProgress.start();
        reqGetTaskList(para).then((res) => {
          this.total = res.data.total;
          this.tasks = res.data.tasks;
          this.listLoading = false;
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

      //TODO:Recover Task
      showCreateRecoverTaskDialog: function (row) {
        this.createRecoverTaskFormVisible = true;
        let task_suffix = util.formatDate.format(row.start_time, 'yyyyMMddhhmmss');
        let descript_suffix = util.formatDate.format(row.start_time, 'yyyy-MM-dd hh:mm:ss');
        let name = this.currentWatchingTask.name + '_Recover_' + task_suffix;
        let source_suffix = '/' + this.currentWatchingTask.name + '_' + this.currentWatchingTask.id + '_' +task_suffix;
        let source = this.currentWatchingTask.destination + source_suffix;
        let description = `This is a recover task for ${this.currentWatchingTask.name} which worked in ${descript_suffix}`;
        this.createRecoverTaskForm = {
          name: name,
          worker_id: '',
          source: source,
          destination: '',
          description: description,
        };
      },
      createRecoverTask: function () {
        let user = {
          user: this.sysUserName,
        };
        let para = Object.assign({}, this.createRecoverTaskForm);
        para.type = 'recover';
        para.destination = 'file:/' + para.destination;
        console.log(para);
        reqAddTask(user, para).then((res) => {
          this.createRecoverTaskLoading = false;
          //NProgress.done();
          this.openMsg('创建成功，请前往恢复任务查看','success');
          this.$refs['createRecoverTaskForm'].resetFields();
          this.createRecoverTaskFormVisible = false;
        }).catch(err=>{
          this.createRecoverTaskLoading = false;
          this.openMsg('添加失败','error');
          console.log(err.message);
          this.$refs['createRecoverTaskForm'].resetFields();
          this.createRecoverTaskFormVisible = false;
        });
      },

      //====编辑相关====
      //处理显示
      beforeShow: function (row) {
        let source = row.task.source;
        let destination = row.task.destination;
        //source = source.match(/\/\/(\S*)/)[1];
        let desArr = destination.split('/');
        let volumeName = desArr[2];
        //destination = destination.match(/\/(\S*)/)[1];
        let volume = this.volumes.find((volume)=>{
          return volume.name === volumeName;
        });
        if(!volume) {
//          console.log('volume is null');
          volume = this.volumes[0];
        }
        if(row.task.type === 'backup'){
          source = source.replace(/file:\//i,'');
          var re = new RegExp("glusterfs:\/\/"+volumeName,"i");
          destination = destination.replace(re,'');
        }else{
          source = source.replace(/glusterfs:\//i,'');
          destination = destination.replace(/file:\//i,'');
        }
        if(volume) {
          this.volumeName = volume.name;
          row.task.volume_id = volume.id;
        }
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
                para.source = 'file:/' + para.source;
                para.destination = 'glusterfs://' + this.volumeName + para.destination;
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
//        console.log(value);
//        this.destination_prefix = "glusterfs://";
        if(typeof(value) !== "undefined"){
          let volume = this.volumes.find((volume)=>{
            return volume.id === value;
          });
          this.volumeName = volume.name;
//          this.destination_prefix = this.destination_prefix + this.volumeName;
        }
      },
      failedMsgbox(row){
        var errMsg;
        if(row.message){
          errMsg = row.message;
        }else{
          errMsg = "未知错误";
        }
        this.$alert(errMsg,'错误日志',{
          callback: action =>{}
        });
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
//            console.log(this.addForm);
            para.type = this.task_type;

            if(para.type === "backup"){
              para.source = 'file:/' + para.source;
              para.destination = 'glusterfs://' + this.volumeName + para.destination;
            }

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
              console.log(err.message);
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
            this.getTasks(this.task_type);
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
      //任务状态详情
      taskStateHandleSizeChange: function (val) {
        this.taskStateFilter.per_page = val;
        this.getTaskStates(this.currTaskRow);
      },
      taskStateHandleCurrentChange: function (val) {
        this.taskStateFilter.page = val;
        this.getTaskStates(this.currTaskRow);
      },
      closeStateDialog() {
        this.currentWatchingTask = [];
        this.dialogTaskStateDetailTableVisible = false;
      },
      taskStateDetail(row) {
        if(this.isBackupTask){
          this.taskStateFilter.per_page = 10;
          this.taskStateFilter.page = 1;
          this.currTaskRow = row.task.id;
          this.currentWatchingTask = row.task;
          this.getTaskStates(this.currTaskRow);
          this.currTaskStateTabTitle = row.task.name;
        }
      },
      getTaskStates(task_id){
        var page_offset = this.taskStateFilter.per_page * (this.taskStateFilter.page - 1);

        let params = {
          user: this.sysUserName,
          limit: this.taskStateFilter.per_page,
          offset: page_offset,
          task_id: task_id,
        };
        reqBackupStates(params).then(res => {
          this.taskStates = res.data.states;
          this.dialogTaskStateDetailTableVisible = true;
          this.taskState_total_rows = res.data.total;
        },err => {
          this.$message({
            message: '获取失败',
            type: 'error'
          });
        })
          .catch(function(response) {
            console.log(response);
          });
      },
      //消息通知模块
      openMsg(msgtext, type){
          this.$message({
              message: msgtext,
              type: type
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
      //TODO:操作按钮相关方法
      taskActions: function (index, row, action) {
        let params = {
          user: this.sysUserName,
        };
        let headers = {
          'Content-Type': 'application/json;charset=UTF-8'
        };
        let data = ''
        //let data = {};
        var info = '';
        if (action == "start") {
          //data.start = action;
          data = "{\"start\": \"start\"}"
          info = "命令下发成功，正在准备执行..."
        } else if (action == "stop") {
          data = "{\"stop\": \"stop\"}"
          info = "命令下发成功，从下一个任务周期停止执行..."
        } else if (action == "resume") {
          data = "{\"resume\": \"resume\"}"
          info = "命令下发成功，任务正在恢复..."
        }
        reqTaskAction(row.task.id, data, params, headers).then(res => {
          this.openMsg(info, 'success');
          params.task_id = row.task.id;
          reqGetTaskList(params).then(res =>{
            this.tasks[index] = res.data.tasks[0]
          })
        }, err => {
          if (err.response.status == 401) {
            this.openMsg('请重新登陆', 'error');
            sessionStorage.removeItem('access-user');
            this.$router.push({ path: '/' });
          } else if (err.response.status == 403) {
            if(err.response.data.code == 403){
              this.openMsg('命令下发失败', 'error');
            }else if(err.response.data.code == 401) {
              this.openMsg('没有权限', 'error');
            }else {
              this.openMsg('命令下发失败', 'error');
            }
          }else {
            this.openMsg('请求失败', 'error');
          }
        });
      },
      toPause:function (index, row) {
        this.isPause = true;
        console.log(index);
      },
      toResume:function (index, row) {
        this.isPause = false;
        console.log(index);
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
      reqGetGroupList(para).then(res=>{
        this.groups = res.data.groups;
      });
      reqGetVolumeList(para).then(res=>{
        this.volumes = res.data.volumes;
      });
      reqGetPolicyList(para).then(res=>{
        this.policies = res.data.policies;
      });
      this.getTasks();
      // 组件创建完后获取数据，
      // 此时 data 已经被 observed 了
      this.intervalTask = setInterval(() => {
        this.offset = this.per_page * (this.page - 1);
        let params = {
          user: this.sysUserName,
          limit: this.per_page,
          offset: this.offset,
        }
        if (this.isBackupTask){
          params.type = 'backup';
        }else{
          params.type = 'recover';
        }
        reqGetTaskList(params).then((res) => {
          this.total = res.data.total;
          if(this.tasks.length != res.data.tasks.length){
            this.tasks = res.data.tasks;
          }else{
            for (var i = 0; i < Math.min(this.per_page,this.total); ++i) {
              this.tasks[i].task.state = res.data.tasks[i].task.state;
              this.tasks.splice(i, {'task.state': res.data.tasks[i].task.state});
              if (res.data.tasks[i].state && this.tasks[i].state){
                this.tasks[i].state.state = res.data.tasks[i].state.state;
                this.tasks.splice(i, {'state.state': res.data.tasks[i].state.state});
                this.tasks[i].state.process = res.data.tasks[i].state.process;
                this.tasks.splice(i, {'state.process': res.data.tasks[i].state.process});
                this.tasks[i].state.start_time = res.data.tasks[i].state.start_time;
                this.tasks.splice(i, {'state.start_time': res.data.tasks[i].state.start_time});
                this.tasks[i].state.total_size = res.data.tasks[i].state.total_size;
                this.tasks.splice(i, {'state.total_size': res.data.tasks[i].state.total_size});
              }
            }
          }
        },err => {
          console.log(err)
        });
      },3000)
    }
  }
</script>
