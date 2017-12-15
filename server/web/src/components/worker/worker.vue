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
        <el-button type="primary" @click="batchDelete" v-if="(role== 'superrole' || role == 'admin') && workers.length !=0">
          批量删除
        </el-button>
        <el-button type="primary" @click="confirmExport">导出客户端</el-button>
        <!--<el-button type="primary" @click="showAddDialog" style="margin-left: 5px"-->
                   <!--v-if="role == 'admin' || role == 'superrole'">新建</el-button>-->
        <el-form :inline="true" :model="filters" style="float:right; margin-right: 5px" onsubmit="return false;">
          <el-form-item>
            <el-input v-model="filters.name" placeholder="主机名" style="min-width: 240px;" @keyup.native="getWokersByName"></el-input>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="getWokersByName">查询</el-button>
          </el-form-item>
        </el-form>
      </el-col>

      <!--列表-->
      <el-table :data="workers" highlight-current-row v-loading="listLoading" @selection-change="handleSelectionChange"
                style="width: 100%;" max-height="750">
        <el-table-column type="selection"></el-table-column>
        <el-table-column prop="name" label="主机名">
        </el-table-column>
        <el-table-column prop="ip" label="IP地址">
        </el-table-column>
        <el-table-column label="启动时间">
          <template slot-scope="scope">
            <span>{{ scope.row.start_at | timeStamp2datetime }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态">
        </el-table-column>
        <el-table-column prop="owner" label="属组">
        </el-table-column>
        <el-table-column prop="version" label="软件版本">
        </el-table-column>
        <el-table-column label="操作" width="200" v-if="role == 'admin' || role == 'superrole'">
          <template slot-scope="scope">
            <!--<svg class="icon" aria-hidden="true" @click="showEditDialog(scope.$index,scope.row)">-->
              <!--<use xlink:href="#icon-modify"></use>-->
            <!--</svg>-->
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
    <el-dialog title="导出客户端" :visible.sync="dialogExportVisible" class="export-dialog">
      <el-form :model="exportConds">
        <el-col :span="8">
          <el-form-item label="自定义数据范围">
            <el-checkbox v-model="exportConds.customize"></el-checkbox>
          </el-form-item>
        </el-col>
        <el-col :span="16" v-if="exportConds.customize">
          <el-col :span="4" style="line-heeight:100%;height: 36px;padding: 10px 2px;">
            导出第
          </el-col>
          <el-col :span="3">
            <el-form-item label="">
              <el-input v-model="exportConds.from" auto-complete="off" style="height: 24px"></el-input>
            </el-form-item>
          </el-col>
          <el-col :span="4" style="line-heeight:100%;height: 36px;padding: 10px 2px;">
            页，至
          </el-col>
          <el-col :span="3">
            <el-form-item label="">
              <el-input v-model="exportConds.to" auto-complete="off" style="height: 24px"></el-input>
            </el-form-item>
          </el-col>
          <el-col :span="5" style="line-heeight:100%;height: 36px;padding: 10px 2px;">
            页数据
          </el-col>
        </el-col>
      </el-form>
      <div slot="footer" class="dialog-footer">
        <el-button @click="cancelExport">取 消</el-button>
        <el-button type="primary" @click="export2excel">确 定</el-button>
      </div>
    </el-dialog>
  </el-row>
</template>

<script>
  import { reqGetWorkerList, reqAddWorker, reqEditWorker, reqDelWorker} from '../../api/api';
  import export2Excel from '../../common/export2Excel'
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
          name: ''
        },
        listLoading: false,
        isVisible:true,
        workers:[],
        total: 0,
        page: 1,
        per_page: 10,
        offset: 0,
        edit_index: 0,
        role: '',

        //编辑相关数据
        editFormVisible: false,//编辑界面是否显示
        editLoading: false,
        dialogExportVisible: false,
        exportConds: {
          customize: false,
          from: 1,
          to: 1,
        },
        multipleSelection: [],
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
      //事件通知模块
      openNotify(title, msgtext, type){
          this.$notify({
              title: title,
              message: msgtext,
              type: type
          });
      },
      openMsg: function (msgtxt, msgtype) {
        this.$message({
          message: msgtxt,
          type: msgtype
        });
      },
      //获取用户列表
      getWorker: function (name_like='') {
        this.offset = this.per_page * (this.page - 1);
        let para = {
          user: this.sysUserName,
          limit: this.per_page,
          offset: this.offset,
        };
        if(name_like !== '') {
          para.name_like = name_like;
        }
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
      getWokersByName(event){
        if(this.filters.name !== '') {
          this.getWorker(this.filters.name);
        }else{
          this.getWorker()
        }
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
            this.$message({
              message: '输入有误，请检查',
              type: 'warning'
            });
          }
        });
      },
      confirmExport(){
        this.dialogExportVisible = true;
      },
      cancelExport(){
        this.dialogExportVisible = false;
        this.exportConds = {
          customize: false,
          from: 1,
          to: 1,
        };
      },
      export2excel(){
        var file_save_name = 'workers',
        file_save_name = file_save_name+(new Date().getTime().toString());
        let params = {
          user: this.sysUserName,
        };
        if(this.exportConds.customize){
          var page_offset = this.filter.per_page * (this.exportConds.from - 1);
          params.limit = (this.exportConds.to - this.exportConds.from + 1)*this.filter.per_page;
          params.offset = page_offset;
        }
        reqGetWorkerList(params).then(res => {
          let { status, data } = res;
          if (data == null) {
            this.$message({
              message: "未获取到信息",
              type: 'error'
            });
          } else {
            export2Excel.export2Excel(data.workers,'workers',file_save_name);
          }
          this.cancelExport();
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
          this.cancelExport();
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
              if(res.data.exist && res.data.exist === 'True') {
                this.$message({
                  message: `添加失败, 主机 ${res.data.worker.name} 已存在`,
                  type: 'error'
                });
              }else{
                this.$message({
                  message: '添加成功',
                  type: 'success'
                });
              }
              //NProgress.done();
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
            this.$message({
              message: '输入有误，请检查',
              type: 'warning'
            });
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
      handleSelectionChange: function (multipleSelection) {
        this.multipleSelection = multipleSelection;
      },
      //批量删除
      batchDelete(){
        if(this.multipleSelection.length > 0){
          this.$confirm('将删除选中的'+this.multipleSelection.length+'个客户端？','提示',{
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          }).then(() => {
            for (var i = 0; i < this.multipleSelection.length; ++i){
              let para = {user: this.sysUserName};
              reqDelWorker(this.multipleSelection[i].id, para).then((res) => {
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
                    err.response.data.tasks.length+" 个备份任务正在使用"+err.response.data.tasks[0].worker_id+"，请先删除任务";
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
            }
          }).catch(() => {
            this.$message({
              type: 'info',
              message: '已取消删除'
            });
          });
        }else{
          this.openMsg('至少选中一条数据', 'info');
        }
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
  .export-dialog .el-dialog {
    width: 35%
  }
</style>
