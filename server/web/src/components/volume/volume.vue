<template>
  <el-row class="warp">
    <el-col :span="24" class="warp-breadcrum">
      <el-breadcrumb separator="/">
        <el-breadcrumb-item :to="{ path: '/' }"><b>首页</b></el-breadcrumb-item>
        <el-breadcrumb-item>卷列表</el-breadcrumb-item>
      </el-breadcrumb>
    </el-col>

    <el-col :span="24" class="warp-main">
      <!--工具条-->
      <el-col :span="24" class="toolbar" style="padding-bottom: 0px;">
        <el-button type="primary" @click="showAddDialog" style="margin-left: 5px">新建</el-button>
        <el-button type="danger" @click="batchDelete" :disabled="this.sels.length===0">
          批量删除
        </el-button>
        <el-form :inline="true" :model="filters" style="float:right; margin-right: 5px">
          <el-form-item>
            <el-input v-model="filters.volumeName" placeholder="卷名" style="min-width: 240px;"></el-input>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="getVolume">查询</el-button>
          </el-form-item>
        </el-form>
      </el-col>

      <!--列表-->
      <el-table :data="volumes" highlight-current-row v-loading="listLoading" @selection-change="selsChange"
                style="width: 100%;">
        <el-table-column type="selection" width="50"></el-table-column>
        <el-table-column type="index" width="60">
        </el-table-column>
        <el-table-column prop="volumeName" label="卷名"  sortable>
        </el-table-column>
        <!--<el-table-column prop="worker" label="所属主机" sortable>-->
        <!--</el-table-column>-->
        <el-table-column prop="description" label="描述">
        </el-table-column>
        <el-table-column label="操作" width="250">
          <template slot-scope="scope">
            <el-button size="small" @click="showEditDialog(scope.$index,scope.row)">
              <i class="iconfont icon-modiffy"></i>
            </el-button>
            <el-button type="danger" @click="delVolume(scope.$index,scope.row)" size="small">
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
          :page-sizes="[10, 20, 30, 40]"
          :page-size="per_page"
          :current-page="page"
          :total="total" style="float:right;margin-right: 5px">
        </el-pagination>
      </el-col>

      <!--编辑框 -->
      <el-dialog title="编辑" v-model="editFormVisible" :close-on-click-modal="false">
        <el-form :model="editForm" label-width="100px" :rules="editFormRules" ref="editForm">
          <el-form-item prop="volumeName" label="卷名">
            <el-input v-model="editForm.volumeName" auto-complete="off"></el-input>
          </el-form-item>
          <!--<el-form-item prop="worker" label="所属主机">-->
            <!--<el-input v-model="editForm.worker" auto-complete="off"></el-input>-->
          <!--</el-form-item>-->
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
        <el-form :model="addForm" label-width="100px" :rules="addFormRules" ref="addForm">
          <el-form-item prop="volumeName" label="组名">
            <el-input v-model="addForm.volumeName" auto-complete="off"></el-input>
          </el-form-item>
          <!--<el-form-item prop="worker" label="所属主机">-->
            <!--<el-input v-model="addForm.worker" auto-complete="off"></el-input>-->
          <!--</el-form-item>-->
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
  import { reqGetVolumeList, reqEditVolume, reqAddVolume, reqDelVolume} from '../../api/api';

  export default {
    data() {
      return {
        filters: {
          volumeName: ''
        },
        listLoading: false,
        isVisible:true,
        volumes: [],
        total: 0,
        page: 1,
        per_page: 10,
        offset: 0,
        sels: [], //列表选中列

        //编辑相关数据
        editFormVisible: false,//编辑界面是否显示
        editLoading: false,
        editFormRules: {
          volumeName: [
            {required: true, message: '请输入组名', trigger: 'blur'}
          ],
          worker: [
            {required: true, message: '请输入角色', trigger: 'blur'}
          ],
          description: [
            {required: true, message: '请输入描述', trigger: 'blur'}
          ]
        },
        editForm: {
          id: 0,
          volumeName: '',
          worker: '',
          description: ''
        },

        //新增数据相关
        addFormVisible: false,
        addLoading: false,
        addFormRules: {
          volumeName: [
            {required: true, message: '请输入组名', trigger: 'blur'}
          ],
          worker: [
            {required: true, message: '请输入角色', trigger: 'blur'}
          ],
          description: [
            {required: true, message: '请输入描述', trigger: 'blur'}
          ]
        },
        addForm: {
          volumeName: '',
          worker: '',
          description: ''
        },
      }
    },
    methods: {
      handleCurrentChange(val) {
        //console.log(`当前 ${val} 页`)
        this.page = val;
        this.getVolume();
      },
      handleSizeChange(val) {
        //console.log(`每页 ${val} 条`)
        this.per_page = val;
        this.getVolume();
      },
      //获取用户列表
      getVolume: function () {
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
        reqGetVolumeList(para).then((res) => {
          this.total = res.data.total;
          this.volumes = res.data.groups;
          this.listLoading = false;
          this.isVisible = true;
          //NProgress.done();
        }).catch(err=>{
          alert(err.message);
          this.listLoading = false;
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
              let user_para = {
                user: this.sysUserName,
              };
              let para = Object.assign({}, this.editForm);
              reqEditVolume(para.id,user_para,para).then((res) => {
                this.editLoading = false;
                //NProgress.done();
                this.$message({
                  message: '提交成功',
                  type: 'success'
                });
                this.$refs['editForm'].resetFields();
                this.editFormVisible = false;
                this.getVolume();
              }).catch(err=>{
                alert("添加失败");
                console.log(err)
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
          volumeName: '',
          worker: '',
          description: ''
        };
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
            reqAddVolume(user, para).then((res) => {
              this.addLoading = false;
              //NProgress.done();
              this.$message({
                message: '提交成功',
                type: 'success'
              });
              this.$refs['addForm'].resetFields();
              this.addFormVisible = false;
              this.getVolume();
            }).catch(err=>{
              alert("添加失败");
              console.log(err)
            });
          }
          else{
            alert('输入有误，提交失败')
          }
        });
      },
      //====删除相关====
      //单个删除
      delVolume: function (index, row) {
        this.$confirm('确认删除该记录吗?', '提示', {type: 'warning'}).then(() => {
          this.listLoading = true;
          //NProgress.start();
          let para = {id: row.id};
          reqDelVolume(para).then((res) => {
            this.listLoading = false;
            //NProgress.done();
            this.$message({
              message: '删除成功',
              type: 'success'
            });
            this.getVolume();
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
//        var ids = this.sels.map(item => item.id).toString();
//        this.$confirm('确认删除选中记录吗？', '提示', {
//          type: 'warning'
//        }).then(() => {
//          this.listLoading = true;
//          //NProgress.start();
//          let para = {ids: ids};
//          reqBatchDelGroup(para).then((res) => {
//            this.listLoading = false;
//            //NProgress.done();
//            this.$message({
//              message: '删除成功',
//              type: 'success'
//            });
//            this.getVolume();
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
      this.getVolume();
    }
  }
</script>

<style scoped>

</style>
