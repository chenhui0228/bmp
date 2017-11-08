/**
 *Modified by 01369634 on 2017/11/2
*/
<template>
  <el-row class="warp">
    <el-col :span="24" class="warp-breadcrum">
      <el-breadcrumb separator="/">
        <el-breadcrumb-item :to="{ path: '/' }"><b>首页</b></el-breadcrumb-item>
        <el-breadcrumb-item>主机管理</el-breadcrumb-item>
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
            <el-input v-model="filters.ip" placeholder="IP地址" style="min-width: 240px;"></el-input>
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
            <el-form label-position="left" inline class="demo-table-expand">
              <el-form-item label="[主机描述]">
                <br />
                <span>{{ props.row.description }}</span>
              </el-form-item>
            </el-form>
          </template>
        </el-table-column>
        <el-table-column prop="name" label="主机名"sortable>
        </el-table-column>
        <el-table-column prop="ip" label="IP地址" sortable>
        </el-table-column>
        <el-table-column prop="port" label="端口号">
        </el-table-column>
        <el-table-column prop="owner" label="用户" sortable>
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
      <el-dialog title="编辑" v-model="editFormVisible" :close-on-click-modal="false">
        <el-form :model="editForm" label-width="100px" :rules="editFormRules" ref="editForm">
          <el-form-item prop="name" label="主机名">
            <el-input v-model="editForm.name" auto-complete="off"></el-input>
          </el-form-item>
          <el-form-item prop="ip" label="IP地址">
            <el-input v-model="editForm.ip" auto-complete="off"></el-input>
          </el-form-item>
          <el-form-item prop="owner" label="用户">
            <el-input v-model="editForm.owner" auto-complete="off"></el-input>
          </el-form-item>
          <el-form-item prop="port" label="端口号">
            <el-input v-model="editForm.port" auto-complete="off"></el-input>
            <!--<el-select v-model="editForm.port" placeholder="请选择主机类型" clearable>-->
              <!--<el-option-->
                <!--v-for="item in options"-->
                <!--:key="item.value"-->
                <!--:label="item.label"-->
                <!--:value="item.value">-->
              <!--</el-option>-->
            <!--</el-select>-->
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
        <el-form :model="addForm" label-width="100px" :rules="editFormRules" ref="addForm">
          <el-form-item prop="name" label="主机名">
            <el-input v-model="addForm.name" auto-complete="off"></el-input>
          </el-form-item>
          <el-form-item prop="ip" label="IP地址">
            <el-input v-model="addForm.ip" auto-complete="off"></el-input>
          </el-form-item>
          <el-form-item prop="owner" label="用户">
            <el-input v-model="addForm.owner" auto-complete="off"></el-input>
          </el-form-item>
          <el-form-item prop="port" label="端口号">
            <el-input v-model="addForm.port" auto-complete="off"></el-input>
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
  import { reqGetWorkerList, reqAddWorker, reqEditWorker, reqBatchDelWorker, reqDelWorker} from '../../api/api';

  export default {
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
          ip: ''
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
        }).catch((err) => {
          this.listLoading = false;
          if (err.response.status == 401) {
            this.$message({
              message: "鉴权失败",
              type: 'error'
            });
            this.$router.push({ path: '/login' });
          }else{
            this.$message({
              message: "获取数据失败",
              type: 'error'
            });
          }
        })
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
