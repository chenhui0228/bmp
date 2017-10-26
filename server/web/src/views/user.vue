//about.vue
<style type="text/css">
    .common-view {
        min-width: 320px;
        margin: 0.3rem 8rem;
    }
    .my-el-button-right {
        float: left;
        margin: 0rem 0.2rem;
    }
    .my-el-button-left {
        float: left;
        margin: 0rem 0.2rem;
    }
    .serach {
        width: 24rem;
    }
    .function-zone {
        height: 3.4rem;
    }
    .tab-pagination {
        float: right;
        margin-top: 20px
    }
</style>
<template>
    <div class="common-view">
        <div class="function-zone" >
            <div class="global-op-mid" style="float: left">
                <el-input v-model="input" placeholder="请输入要查询的用户" class="serach my-el-button-left" :disabled="true"></el-input>
                <el-button type="primary" @click="searchUser" class="my-el-button-left" :disabled="true">查询</el-button>
            </div>
            <div class="global-op-left" style="float: right">
                <!--<el-button type="primary" @click="newPolicy" class="my-el-button-right">新建</el-button>-->
                <el-button type="primary" @click="dialogFormVisible = true" class="my-el-button-right">新建</el-button>
                <el-button type="primary" @click="deleteUser" :disabled="true" class="my-el-button-right">批量删除</el-button>
            </div>
            <div class="el-dialog-modul">
                <el-dialog title="新建用户" :visible.sync="dialogFormVisible">
                    <el-form :model="ruleForm" :rules="rules" ref="ruleForm" label-width="100px" class="dremo-ruleForm">
                        <el-form-item label="用户描述" prop="description">
                            <el-input v-model="ruleForm.description"></el-input>
                        </el-form-item>
                        <el-form-item label="开始时间" required>
                            <el-date-picker v-model="ruleForm.startDateTime" type="datetime" placeholder="选择日期时间"></el-date-picker>
                        </el-form-item>
                        <el-form-item label="执行周期" prop="interval">
                            <el-input type="number" v-model="ruleForm.interval" :min="1"></el-input>
                        </el-form-item>
                        <el-form-item>
                            <el-button type="primary" @click="submitForm('ruleForm')">提交</el-button>
                            <el-button @click="resetForm('ruleForm')">重置</el-button>
                        </el-form-item>
                    </el-form>
                </el-dialog>
            </div>
        </div>
        <div class="data-zone">
            <el-table
                ref="multipleTable"
                :data="tableDataPolicy"
                border
                tooltip-effect="dark"
                style="width: 100%"
                @selection-change="handleSelectionChange">
                <el-table-column
                    type="selection"
                    width="55"
                    :disabled="true">
                </el-table-column>
                <el-table-column
                    prop="id"
                    label="ID"
                    width="120">
                </el-table-column>
                <el-table-column
                    prop="description"
                    label="用户说明"
                    show-overflow-tooltip>
                </el-table-column>
                <el-table-column
                    prop="start_time"
                    label="开始时间"
                    width="240">
                </el-table-column>
                <el-table-column
                    prop="interval"
                    label="执行周期"
                    width="120">
                </el-table-column>
                <el-table-column
                        prop="interval"
                        label="执行周期"
                        width="120">
                </el-table-column>
                <el-table-column label="操作" width="180">>
                    <template scope="scope">
                        <el-button
                            size="small"
                            @click="handleEdit(scope.$index, scope.row)">编辑</el-button>
                        <el-button
                            size="small"
                            type="danger"
                            @click="handleDelete(scope.$index, scope.row)">删除</el-button>
                    </template>
                </el-table-column>
            </el-table>
            <div class="tab-pagination">
                <el-pagination
                        @size-change="handleSizeChange"
                        @current-change="handleCurrentChange"
                        :current-page="filter.page"
                        :page-sizes="[10, 15, 20, 30]"
                        :page-size="filter.per_page"
                        layout="total, sizes, prev, pager, next, jumper"
                        :total="total_rows">
                </el-pagination>
            </div>
        </div>
    </div>
</template>
<script>
export default {

    data() {
        return {
            input: '',
            //-----表单数据----
            tableDataPolicy:[],
            multipleSelection: [],
            //-----分页数据---
            filter: {
                per_page: 10,   //页大小
                page: 1   //当前页
            },
            total_rows: 0,
            dialogFormVisible: false,
            ruleForm: {
                description: '',
                startDate: '',
                startTime: '',
                interval: 1,
                startDateTime: ''
            },
            rules: {
                description: [
                    { required: true, message: '请输入用户描述信息', trigger: 'blur' },
                    { min: 5, max: 30, message: '长度在 5 到 30 个字符', trigger: 'blur' }
                ],
                startDateTime: [
                    { type: 'datetime', required: true, message: '请为用户选择开始时间', trigger: 'change' }
                ],
                interval: [
                    {  required: true, message: '请输入用户执行周期', trigger: 'blur' },
                    { min: 1, message: '周期必须为数值', trigger: 'blur' }
                ]
            }
        }
    },
    created() {
        // 组件创建完后获取数据，
        // 此时 data 已经被 observed 了
        this.fetchPolicyLists()
    },
    watch: {
        // 如果路由有变化，会再次执行该方法
        '$route': 'fetchPolicyLists'
    },
    methods: {
        //-----获取用户列表----
        fetchPolicyLists() {
            this.$http.get(this.GLOBAL.url+"/backup/policies").then(reponse => {
                var policies  = reponse.data.policies;
                this.total_rows = policies.length;
                this.filter.page = 1
                this.tableDataPolicy = policies;
            })
            .catch(function(response) {
                console.log(response);
            })
        },
        //-----新建用户----
        submitForm(formName) {
            this.$refs[formName].validate((valid) => {
                if (valid) {
                    alert('submit!');
                } else {
                    console.log('error submit!!');
                    return false;
                }
            });
        },
        resetForm(formName) {
            this.$refs[formName].resetFields();
        },
        //-----搜索用户
        searchUser() {
            console.log("查询")
        },
        //-----搜索用户
        deleteUser() {
            console.log("删除")
        },
        //-----表单----
        toggleSelection(rows) {
            if (rows) {
                rows.forEach(row => {
                    this.$refs.multipleTable.toggleRowSelection(row);
                });
            } else {
                this.$refs.multipleTable.clearSelection();
            }
        },
        handleSelectionChange(val) {
            this.multipleSelection = val;
        },
        //-----分页----
        handleSizeChange(val) {
            this.filter.per_page = val;
            this.fetchPolicyLists();
            console.log(`每页 ${val} 条`);
        },
        handleCurrentChange(val) {
            this.filter.page = val;
            this.fetchPolicyLists();
            console.log(`当前页: ${val}`);
        },
        //-----

    }
}


</script>
