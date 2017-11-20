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
      <el-col :span="24" class="toolbar" style="padding-bottom: 0px;" >
        <el-button type="danger" @click="batchDelete" :disabled="this.sels.length===0"
                   v-if="role == 'admin' || role == 'superadmin'">
          批量删除
        </el-button>
        <el-button type="primary" @click="showAddDialog" style="margin-left: 5px"
                   v-if="role == 'admin' || role == 'superadmin'">新建</el-button>
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
            <el-form label-position="left" inline class="table-expand">
              <el-form-item label="[主机描述]">
                <span>{{ props.row.description }}</span>
              </el-form-item>
              <el-form-item label="[启动时间]">
                <span>{{ props.row.start_at | timeStamp2datetime }}</span>
              </el-form-item>
              <el-form-item label="[软件版本号]">
                <span>{{ props.row.version }}</span>
              </el-form-item>
            </el-form>
          </template>
        </el-table-column>
        <el-table-column prop="name" label="主机名"sortable>
        </el-table-column>
        <el-table-column prop="ip" label="IP地址" sortable>
        </el-table-column>
        <el-table-column prop="status" label="状态">
        </el-table-column>
        <el-table-column prop="user.name" label="用户" sortable>
        </el-table-column>
        <!--<el-table-column prop="description" label="描述" sortable>-->
        <!--</el-table-column>-->
        <el-table-column label="操作" width="200" v-if="role == 'admin' || role == 'superadmin'">
          <template slot-scope="scope">
            <svg class="icon" aria-hidden="true" @click="showEditDialog(scope.$index,scope.row)">
              <use xlink:href="#icon-modify"></use>
            </svg>
            <svg class="icon" aria-hidden="true" @click="delWorker(scope.$index,scope.row)">
              <use xlink:href="#icon-delete"></use>
            </svg>
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
      <el-dialog title="新建" v-model="addFormVisible" :close-on-click-modal="false" :beforeClose="cancelAdd">
        <el-form :model="addForm" label-width="100px" :rules="editFormRules" ref="addForm">
          <el-form-item prop="name" label="主机名">
            <el-input v-model="addForm.name" auto-complete="off"></el-input>
          </el-form-item>
          <el-form-item prop="ip" label="IP地址">
            <el-input v-model="addForm.ip" auto-complete="off"></el-input>
          </el-form-item>
          <!--<el-form-item prop="owner" label="用户">-->
            <!--<el-input v-model="addForm.owner" auto-complete="off"></el-input>-->
          <!--</el-form-item>-->
          <el-form-item prop="description" label="描述">
            <el-input type="textarea" v-model="addForm.description" :rows="4"></el-input>
          </el-form-item>
        </el-form>
        <div slot="footer" class="dialog-footer">
          <el-button @click.native="cancelAdd()">取消</el-button>
          <el-button type="primary" @click.native="addSubmit" :loading="addLoading">提交</el-button>
        </div>
      </el-dialog>

    </el-col>

  </el-row>
</template>

<script>
  import { reqGetWorkerList, reqAddWorker, reqEditWorker, reqDelWorker} from '../../api/api';

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
        listLoading: false,
        isVisible:true,
        workers:[],
        total: 0,
        page: 1,
        per_page: 10,
        offset: 0,
        edit_index: 0,
        sels: [], //列表选中列
        role: '',

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
          description: [
            {required: true, message: '请输入描述', trigger: 'blur'}
          ]
        },
        editForm: {
          id: 0,
          name: '',
          ip: '',
          description: '',
          user: ''
        },

        //新增数据相关
        addFormVisible: false,
        addLoading: false,
        addForm: {
          name: '',
          ip: '',
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
      openMsg: function (msgtxt, msgtype) {
        this.$message({
          message: msgtxt,
          type: msgtype
        });
      },
      //获取用户列表
      getWorker: function () {
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
              message: "请重新登录",
              type: 'error'
            });
            sessionStorage.removeItem('access-user');
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
        console.log(row);
        this.edit_index = index;
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
              let user_para = {
                user: this.sysUserName,
              };
              let para = Object.assign({}, this.editForm);
              reqEditWorker(para.id,user_para,para).then((res) => {
                this.editLoading = false;
                //NProgress.done();
                this.$message({
                  message: '提交成功',
                  type: 'success'
                });
                this.$refs['editForm'].resetFields();
                this.editFormVisible = false;
                this.getWorker();
              }).catch(err=>{
                this.editLoading = false;
                this.$message({
                  message: '提交失败：',
                  type: 'error'
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
          name: '',
          ip: '',
          description: ''
        };
      },
      //取消提交
      cancelAdd: function () {
        this.addFormVisible = false;
        this.$refs['addForm'].resetFields();
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
            reqAddWorker(user, para).then((res) => {
              this.addLoading = false;
              //NProgress.done();
              this.$message({
                message: '提交成功',
                type: 'success'
              });
              this.$refs['addForm'].resetFields();
              this.addFormVisible = false;
              this.getWorker();
            }).catch(err=>{
              this.addLoading = false;
              this.$message({
                message: '添加失败：' + err.message,
                type: 'error'
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
      delWorker: function (index, row) {
        this.$confirm('确认删除该记录吗?', '提示', {type: 'warning'}).then(() => {
          this.listLoading = true;
          //NProgress.start();
          let para = {user: this.sysUserName};
          reqDelWorker(row.id, para).then((res) => {
            this.listLoading = false;
            //NProgress.done();
            this.openMsg('删除成功','success');
            this.getWorker();
          }).catch((err) => {
            this.listLoading = false;
            if (err.response.status == 401) {
              this.openMsg('请重新登陆', 'error');
              sessionStorage.removeItem('access-user');
              this.$router.push({ path: '/' });
            }else if(err.response.data.code === 403) {
              this.openMsg('删除失败', 'error');
              let tips = err.response.data.tasks[0].name+' 等 '+
                err.response.data.tasks.length+" 个备份任务正在使用，请先删除任务";
              this.$notify({
                title: '删除作业机失败',
                message: tips,
                type: 'error'
              });
            }else if(err.response.data.code === 401) {
              this.openMsg('没有权限', 'error');
            }else {
            this.openMsg('请求失败', 'error');
          }
          });
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
          console.log(para);
//          reqBatchDelWorker(para).then((res) => {
//            this.listLoading = false;
//            //NProgress.done();
//            this.$message({
//              message: '删除成功',
//              type: 'success'
//            });
//            this.getWorker();
//          }).catch((err) => {
//            alert(err.message)
//          });
        });
      },

    },
    mounted() {
      var accessInfo = sessionStorage.getItem('access-user');
      if (accessInfo) {
        accessInfo = JSON.parse(accessInfo);
        this.sysUserName = accessInfo.username;
        this.role = accessInfo.role;
      }
      this.getWorker();
    }
  }
</script>

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
