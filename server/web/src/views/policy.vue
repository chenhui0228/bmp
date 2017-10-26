//about.vue
<style type="text/css">
    .common-view {
        min-width: 320px;
        margin: 0.3rem 6rem;
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
    .tab-pagination {
        float: right;
        margin-top: 20px
    }
</style>
<template>
    <div class="common-view" v-loading.body="tabLoading" element-loading-text="拼命加载中">
        <div class="func-row row" >
            <div class="col-xs-12">
                <div class="form-inline pull-left">
                    <el-input v-model="input" placeholder="请输入要查询的备份策略名称" class="serach my-el-button-left" :disabled="true"></el-input>
                    <el-button type="primary" @click="searchPolicy" class="my-el-button-left" :disabled="true">查询</el-button>
                </div>
                <div class="form-inline pull-right">
                    <el-button type="primary" @click="newPolicy" class="my-el-button-right">新建</el-button>
                    <el-button type="primary" @click="deletePolicy" :disabled="true" class="my-el-button-right">批量删除</el-button>
                </div>
            </div>
        </div>
        <div class="tab-page">
            <div class="data-zone">
                    <el-table
                        ref="multipleTable"
                        :data="tableDataPolicy"
                        tooltip-effect="dark"
                        style="width: 100%"
                        @selection-change="handleSelectionChange">
                    <el-table-column
                            type="selection"
                            width="45rem"
                            :disabled="true">
                    </el-table-column>
                    <el-table-column
                            prop="name"
                            label="策略名称"
                            width="240rem">
                    </el-table-column>
                    <el-table-column
                            prop="description"
                            label="策略说明"
                            min-width="160rem"
                            show-overflow-tooltip>
                    </el-table-column>
                    <el-table-column
                            prop="start_time"
                            label="开始时间"
                            width="200rem"
                            :formatter="date2str">
                    </el-table-column>
                    <el-table-column
                            prop="interval"
                            label="执行周期(时)"
                            width="200rem">
                    </el-table-column>
                    <el-table-column
                            prop="created_at"
                            label="创建时间"
                            width="220rem"
                            :formatter="date2str"
                            show-overflow-tooltip>
                    </el-table-column>
                    <el-table-column
                            prop="updated_at"
                            label="更新时间"
                            width="220rem"
                            :formatter="date2str"
                            show-overflow-tooltip>
                    </el-table-column>
                    <el-table-column label="操作" width="120rem">
                        <template scope="scope">
                            <el-button type="text" icon="edit" @click="handleEdit(scope.$index, scope.row)"></el-button>
                            <el-button type="text" icon="delete" style="color: red" @click="confimDeleteMsgbox('handleDelete',scope.$index, scope.row)"></el-button>
                            <!--<el-button-->
                                    <!--size="small"-->
                                    <!--@click="handleEdit(scope.$index, scope.row)">编辑</el-button>-->
                            <!--<el-button-->
                                    <!--size="small"-->
                                    <!--type="danger"-->
                                    <!--@click="handleDelete(scope.$index, scope.row)">删除</el-button>-->
                        </template>
                    </el-table-column>
                </el-table>
            </div>
            <div class="el-dialog-modul">
                <el-dialog :title="policyFormTitle" :visible.sync="dialogNewPolicyFormVisible">
                    <el-form :model="policyForm" :rules="rules" ref="policyForm" label-width="120px" class="dremo-ruleForm">
                        <el-form-item label="策略名称" prop="name">
                            <el-input v-model="policyForm.name"></el-input>
                        </el-form-item>
                        <el-form-item label="策略描述" prop="description">
                            <el-input v-model="policyForm.description"></el-input>
                        </el-form-item>
                        <el-form-item label="开始时间" prop="start_time">
                            <el-date-picker v-model="policyForm.start_time" type="datetime" placeholder="选择日期时间"></el-date-picker>
                        </el-form-item>
                        <el-form-item label="执行周期(时)" prop="interval">
                            <el-input type="number" v-model="policyForm.interval" placeholder="请设置执行周期，必须为大于或者等于1的数值"></el-input>
                        </el-form-item>
                        <el-form-item>
                            <el-button type="primary" @click="submitPolicyForm('policyForm')">提交</el-button>
                            <el-button @click="resetForm('policyForm')">重置</el-button>
                        </el-form-item>
                    </el-form>
                </el-dialog>
            </div>
            <div class="tab-pagination" v-show="!tabLoading">
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
        var validateInterval = (rule, value, callback) => {
            var interval = /^[0-9]+$/;
            if (!interval.test(value) || (parseInt(value) < 1)){
                callback(new Error('输入格式不正确，请重新输入！'));
            }else{
                callback();
            }
        }
        var validateSaeTime = (rule, value, callback) => {
            var nTime = new Date(new Date().getTime() + 5*60*1000).getTime();
            //var tmp = new Date(value);
            var sTime = new Date(value).getTime();
            //sTime.setFullYear(tmp.getFullYear(), tmp.getMonth(), tmp.getDate());
            if (sTime < nTime && this.policySubmitMethod == "post") {
                callback(new Error('起始时间必须设置在当前时刻5分钟以后'));
            }else{
                callback();
            }
        };
        return {
            input: '',
            testtime: '',
            //-----表单数据----
            tableDataPolicy:[],
            multipleSelection: [],
            tabLoading: true,
            //-----分页数据---
            filter: {
                per_page: 10,   //页大小
                page: 1   //当前页
            },
            total_rows: 0,
            dialogNewPolicyFormVisible: false,
            policyFormTitle:  '新建策略',
            policySubmitMethod: 'post',
            policyForm: {
                id: 0,
                name: '',
                description: '',
                start_time: '',
                interval: 1,
                deleted: '',
            },
            rules: {
                name: [
                    { required: true, message: '请输入策略名称'},
                    { min: 5, max: 30, message: '长度在 5 到 30 个字符'}
                ],
                description: [
                    { required: true, message: '请输入策略描述信息'},
                    { min: 5, max: 100, message: '长度在 5 到 100 个字符'}
                ],
                start_time: [
                    { required: true, validator: validateSaeTime}
                ],
                interval: [
                    {  required: true, validator: validateInterval},
                ]
            }
        }
    },
    created() {
        // 组件创建完后获取数据，
        // 此时 data 已经被 observed 了
        this.fetchPolicyLists();
    },
    watch: {
        // 如果路由有变化，会再次执行该方法
        '$route': 'fetchPolicyLists'
    },
    methods: {
        date2str(row, column, cellValue){
            var date = new Date(row[column.property]);
            if (date == undefined) {
                return "";
            }
            var datetime = this.myDateFormat(date,"yyyy-MM-dd hh:mm:ss");
            return datetime;
        },
        initializePolicyForm(){
            this.policyForm = {
                'name': '',
                'description': '',
                'start_time': '',
                'interval': '',
                'deleted': '',
            };
            this.policyFormTitle = '新建策略';
            this.policySubmitMethod = 'post';
            console.log(this.policyForm);
        },
        //事件通知模块
        openNotify(title, msgtext, type){
            this.$notify({
                title: title,
                message: msgtext,
                type: type
            });
        },
        //事件消息模块
        openMsg(msgtext, type){
            this.$message({
                message: msgtext,
                type: type
            });
        },
        //-----新建策略----
        newPolicy(){
            this.dialogNewPolicyFormVisible = true;
            this.initializePolicyForm();
        },
        //-----获取策略列表----
        fetchPolicyLists() {
            this.tabLoading = true;
            var page_offset = this.filter.per_page * (this.filter.page - 1);
            this.$http.get(this.GLOBAL.url+"/backup/policies",{params: {limit: this.filter.per_page, offset: page_offset}}).then(reponse => {
                var policies  = reponse.data.policies;
                this.total_rows = reponse.data.total;
                this.filter.page = this.filter.page;
                this.filter.per_page = this.filter.per_page;
                this.tableDataPolicy = policies;
                this.tabLoading = false;
            })
            .catch(function(response) {
                console.log(response);
            })
        },
        //-----新建策略----
        submitPolicyForm(formName) {
            this.policyForm.start_time = new Date(this.policyForm.start_time).getTime();
            var appendstr = '';
            if(this.policySubmitMethod == 'put'){
                appendstr = '/'+this.policyForm.id;
            }
            this.$refs[formName].validate((valid) => {
                if (valid) {
                    this.axios.request({url: this.GLOBAL.url+"/backup/policies"+appendstr,data: this.policyForm, method: this.policySubmitMethod}).then(res => {
                        this.filter.page = 1;
                        this.fetchPolicyLists();
                        this.openMsg(this.policyFormTitle+'成功', 'success');
                        this.dialogNewPolicyFormVisible = false;
                    },err => {
                        console.log(err.response.status);
                        this.openMsg(this.policyFormTitle+'失败', 'error');
                    })
                    .catch(function(response) {
                        console.log(response);
                        this.openMsg(this.policyFormTitle+'异常', 'warning');
                    });
                } else {
                    this.openMsg('信息输入不正确，请检查格式！', 'error')
                    return false;
                }
            });
        },
        resetForm(formName) {
            this.$refs[formName].resetFields();
        },
        //-----搜索策略
        searchPolicy() {
            console.log("查询")
        },
        //-----搜索策略
        deletePolicy() {
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
        handleEdit(index, row) {
            this.policyFormTitle = '修改策略';
            this.policySubmitMethod = 'put';
            this.policyForm = row;
            //this.policyForm.start_time = new Date(this.policyForm.start_time);
            this.dialogNewPolicyFormVisible = true;
        },
        handleDelete(index, row) {
            this.axios.delete(this.GLOBAL.url+"/backup/policies/"+row.id).then(res => {
                var ds = res.data.code;
                var tips = '';
                if(ds == '200'){
                    this.fetchPolicyLists();
                    this.openMsg('删除成功', 'success');
                }else{
                    tips = res.data.tasks[0].name+' 等 '+res.data.tasks.length+" 个备份任务正在使用，请先删除任务"
                    this.openMsg('删除失败', 'error');
                    this.openNotify('失败提示',tips,'error');
                }
            },err => {
                console.log(err.res.status);
                this.tabLoading = false;
                this.openMsg('请求错误', 'warning')
            })
            .catch(function(res) {
                console.log(res);
            });
        },
        confimDeleteMsgbox(func, index, row){
            const h = this.$createElement;
            this.$msgbox({
                title: '重要提醒',
                message: h('p',{style: 'color: red'},'您确定要删除这个备份策略吗？'),
                type: 'warning',
                showCancelButton: true,
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                beforeClose: (action, instance, done) => {
                    if (action === 'confirm') {
                        this.handleDelete(index, row);
                        done();
                    } else {
                        done();
                    }
                }
            }).then(action => {
            });
        },
    }
}


</script>
