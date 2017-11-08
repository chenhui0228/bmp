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
        <el-button type="primary" @click="">新建</el-button>
        <el-button type="primary" @click="">批量删除</el-button>
      </div>
      <div class="toolbar" style="float:right;">
        <el-form :inline="true" :model="filters">
          <el-form-item>
            <el-input v-model="filters.name" placeholder="姓名" style="min-width: 240px;"></el-input>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="getUser">查询</el-button>
          </el-form-item>
        </el-form>
      </div>
      <el-table :data="users" highlight-current-row v-loading="loading" style="width: 100%;">
        <el-table-column type="selection" width="50">
        </el-table-column>
        <!--<el-table-column type="index" width="60">-->
        <!--</el-table-column>-->
        <el-table-column prop="name" label="用户名" width="240" sortable>
        </el-table-column>
        <el-table-column prop="role" label="角色" width="180" sortable>
          <!--<template scope="scope">-->

          <!--</template>-->
        </el-table-column>
        <el-table-column prop="group" label="属组" width="240" sortable>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="240" sortable>
        </el-table-column>
        <el-table-column label="操作">
          <template scope="scope">
            <el-button type="text" icon="information" @click=""></el-button>
            <el-button v-if="!gdeleted" type="text" icon="edit" @click="handleEdit(scope.$index, scope.row.task)"></el-button>
            <el-button v-if="!gdeleted" type="text" icon="delete" style="color: red" @click="confimDeleteMsgbox('handleDelete',scope.$index, scope.row.task, scope._self.confimTaskDeleteMsg)"></el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-col>
  </el-row>
  <el-row class="warp">
    <el-col :span="24" class="warp-main">
      <div class="tab-pagination" v-show="!tabLoading">
        <el-pagination
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
          :current-page="1"
          :page-sizes="[10, 15, 20, 30]"
          :page-size="6"
          layout="total, sizes, prev, pager, next, jumper"
          total="100"
          style="float: right;">
        </el-pagination>
      </div>
    </el-col>
  </el-row>
  </el-row>
</template>
<script>
  export default{
    data(){
      return {
        msg: 'hello vue'
      }
    }
  }
</script>
