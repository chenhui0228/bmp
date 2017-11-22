/**
* Create by 01369634 on 2017/11/21
*/

<template>
  <el-row class="warp">
    <el-col :span="24" class="warp-breadcrum">
      <el-breadcrumb separator="/">
        <el-breadcrumb-item :to="{ path: '/' }"><b>首页</b></el-breadcrumb-item>
        <el-breadcrumb-item>日志管理</el-breadcrumb-item>
      </el-breadcrumb>
    </el-col>

    <el-col el-col :span="24" class="warp-main">
      <!--列表-->
      <el-table :data="OplogList" highlight-current-row v-loading="listLoading" style="width: 100%;" max-height="750">
        <el-table-column prop="username" label="用户名"sortable>
        </el-table-column>
        <el-table-column prop="created_at" label="时间" sortable>
          <template slot-scope="scope">
            <span>{{ scope.row.created_at | dateStampFormat }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="message" label="日志">
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

    </el-col>


  </el-row>
</template>

<script>
  import {reqGetOplogList} from '../../api/api';

  export default {
    data() {
      return {
        OplogList: [],
        listLoading: false,

        total: 0,
        page: 1,
        per_page: 10,
        offset: 0,
      };
    },
    methods: {
      handleCurrentChange(val) {
        //console.log(`当前 ${val} 页`)
        this.page = val;
        this.getOplogList();
      },
      handleSizeChange(val) {
        //console.log(`每页 ${val} 条`)
        this.per_page = val;
        this.getOplogList();
      },
      openMsg: function (msgtxt, msgtype) {
        this.$message({
          message: msgtxt,
          type: msgtype
        })
      },
      getOplogList: function () {
        this.offset = this.per_page * (this.page - 1);
        let para = {
          user: this.sysUserName,
          limit: this.per_page,
          offset: this.offset,
        };
        reqGetOplogList(para).then((res) => {
          this.total = res.data.total;
          this.OplogList = res.data.oplogs;
          //NProgress.done();
        }).catch((err) => {
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
    },
    mounted() {
      var accessInfo = sessionStorage.getItem('access-user');
      if (accessInfo) {
        accessInfo = JSON.parse(accessInfo);
        this.sysUserName = accessInfo.username;
        this.role = accessInfo.role;
      }
      this.getOplogList();
    }
  }

</script>

