<template>
  <el-row class="warp">
    <el-col :span="24" class="warp-breadcrum">
      <el-breadcrumb separator="/">
        <el-breadcrumb-item :to="{ path: '/' }"><b>首页</b></el-breadcrumb-item>
        <el-breadcrumb-item>组列表</el-breadcrumb-item>
      </el-breadcrumb>
    </el-col>

    <el-col :span="24" class="warp-main">
      <!--工具条-->
      <el-col :span="24" class="toolbar" style="padding-bottom: 0px;">
        <el-form :inline="true" :model="filters">
          <el-form-item>
            <el-input v-model="filters.name" placeholder="组名" style="min-width: 240px;"></el-input>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="getGroup">查询</el-button>
          </el-form-item>
        </el-form>
      </el-col>

      <!--列表-->
      <el-table :data="groups" highlight-current-row v-loading="loading" style="width: 100%;">
        <el-table-column type="index" width="60">
        </el-table-column>
        <el-table-column prop="groupName" label="组名" width="200" sortable>
        </el-table-column>
        <el-table-column prop="role" label="角色" width="250" sortable>
        </el-table-column>
        <el-table-column prop="description" label="描述" sortable>
        </el-table-column>
      </el-table>

    </el-col>
  </el-row>
</template>

<script>
  import { reqGetGroupList } from '../../api/api';

  export default {
    data() {
      return {
        filters: {
          groupName: ''
        },
        loading: false,
        groups: [
        ]
      }
    },
    methods: {
      //获取用户列表
      getGroup: function () {
        let para = {
          groupname: this.filters.groupName
        };
        this.loading = true;
        //NProgress.start();
        reqGetGroupList(para).then((res) => {
          this.groups = res.data.groups;
          this.loading = false;
          //NProgress.done();
        });
      }
    },
    mounted() {
      this.getGroup();
    }
  }
</script>

<style scoped>

</style>
