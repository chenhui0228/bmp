//about.vue
<style type="text/css" scoped>
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
        width: 28rem;
    }
    .tab-pagination {
        float: right;
        margin-top: 20px
    }
    .detail{
    margin: 0 18px;
  }
  .detail-item{
    flex: 1;
    margin-top: 1px;
    /*font-size: 0.22rem;*/
    height: 2.4rem;
    line-height: 2.4rem;
    border-bottom: 1px solid #ccc;
    white-space: nowrap;
    overflow: hidden;
    text-overflow:ellipsis;
  }
  .detail-item .item-key{
    float: left;
    /*width: rem;*/
    width: 120px;
    font-size: 1rem;
    text-align: right;
  }
  .detail-item .item-value{
    float: left;
    /*width: 3.2rem;*/
    font-size: 1rem;
    text-align: left;
    white-space: nowrap;
    overflow: hidden;
    text-overflow:ellipsis;
  }
  .el-dialog .el-dialog--my-small {
    width: 35%;
  }
  .el-form-item__label {
    /*width: 120px;*/
  }
</style>
<template>
    <div class="common-view" v-loading.body="tabLoading" element-loading-text="拼命加载中">
        <div class="func-row row" >
            <div class="col-xs-12">
                <div class="form-inline pull-left">
                    <el-input v-model="searchCond" @blur="validateSearchCond" placeholder="格式如：worker=worker" class="serach my-el-button-left"></el-input>
                    <el-button type="primary" @click="searchTask" class="my-el-button-left">查询</el-button>
                    <el-button type="primary" @click="searchTaskMore" class="my-el-button-left">高级查询</el-button>
                    <el-button v-show="searchCond != '' || searchModel.name != '' || searchModel.policy_name != '' || searchModel.worker_name != '' ||
                                        searchModel.deleted || searchModel.policy_id != '' || searchModel.worker_id != ''"
                               type="primary" @click="initializeSearchCond" class="my-el-button-left">清空查询条件</el-button>
                </div>
                <div class="form-inline pull-right">
                    <el-button type="primary" @click="newTask" class="my-el-button-right">新建</el-button>
                    <el-button type="primary" @click="workerInfo" class="my-el-button-right">作业机</el-button>
                    <el-button type="primary" @click="deleteTasks" :disabled="true" class="my-el-button-right">批量删除</el-button>
                </div>
            </div>
        </div>
        <div class="tab-page" >
            <div class="data-zone">
                <el-table
                        ref="multipleTable"
                        :data="tableDataTask"
                        tooltip-effect="dark"
                        style="width: 100%"
                        @selection-change="handleSelectionChange"
                        @row-dblclick="taskStateDetail">
                    <el-table-column
                            type="selection"
                            width="45rem"
                            :disabled="true">
                    </el-table-column>
                    <el-table-column
                            prop="task.name"
                            label="任务名"
                            width="220rem"
                            show-overflow-tooltip>
                    </el-table-column>
                    <el-table-column
                            prop="task.description"
                            label="任务描述"
                            min-width="160rem"
                            show-overflow-tooltip>
                    </el-table-column>
                    <el-table-column
                            prop="task.source"
                            label="备份源地址"
                            width="160rem"
                            show-overflow-tooltip>
                    </el-table-column>
                    <el-table-column
                            prop="task.destination"
                            label="备份目的地"
                            width="220rem"
                            show-overflow-tooltip>
                    </el-table-column>
                    <el-table-column
                            prop="task.duration"
                            label="保存时间(天)"
                            width="130rem"
                            show-overflow-tooltip>
                    </el-table-column>
                    <el-table-column
                        label="开始时间"
                        width="180rem"
                        show-overflow-tooltip>
                        <template scope="scope">
                            <span>{{ scope.row.task.start_time | dateStampFormat }}</span>
                        </template>
                    </el-table-column>
                    <el-table-column
                            label="执行周期（时）"
                            width="180rem"
                            show-overflow-tooltip>
                        <template scope="scope">
                            <span>{{ scope.row.task.interval }}</span>
                        </template>
                    </el-table-column>
                    <!--<el-table-column-->
                            <!--label="创建时间"-->
                            <!--width="180rem"-->
                            <!--show-overflow-tooltip>-->
                        <!--<template scope="scope">-->
                            <!--<span>{{ scope.row.task.created_at | dateStampFormat }}</span>-->
                        <!--</template>-->
                    <!--</el-table-column>-->
                    <!--<el-table-column-->
                            <!--label="更新时间"-->
                            <!--width="180rem"-->
                            <!--show-overflow-tooltip>-->
                        <!--<template scope="scope">-->
                            <!--<span>{{ scope.row.task.updated_at | dateStampFormat }}</span>-->
                        <!--</template>-->
                    <!--</el-table-column>-->
                    <el-table-column
                            v-if="gdeleted"
                            label="删除时间"
                            width="180rem"
                            show-overflow-tooltip>
                        <template scope="scope">
                            <span>{{ scope.row.task.deleted_at | dateStampFormat }}</span>
                        </template>
                    </el-table-column>
                    <el-table-column
                            v-if="!gdeleted"
                            label="任务进度"
                            width="180rem">
                        <template scope="scope">
                            <span v-if="scope.row.state && scope.row.state.state == 'success'" style="color: green">已完成</span>
                            <span v-else-if="scope.row.state && scope.row.state.state == 'start'" style="color: blue">执行中...</span>
                            <span v-else-if="scope.row.state && scope.row.state.state == 'failed'" style="color: red">失败</span>
                            <el-progress v-else-if="scope.row.state" :percentage="parseInt(scope.row.state.state)"></el-progress>
                            <span v-else style="color: #F7AD01">未开始</span>
                        </template>
                    </el-table-column>
                    <el-table-column label="操作" width="120rem">
                        <template scope="scope">
                            <el-button type="text" icon="information" @click="taskDetail(scope.$index, scope.row.task)"></el-button>
                            <el-button v-if="!gdeleted" type="text" icon="edit" @click="handleEdit(scope.$index, scope.row.task)"></el-button>
                            <el-button v-if="!gdeleted" type="text" icon="delete" style="color: red" @click="confimDeleteMsgbox('handleDelete',scope.$index, scope.row.task, scope._self.confimTaskDeleteMsg)"></el-button>
                        </template>
                    </el-table-column>
                </el-table>
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
        <div class="elrement-ui-dialog-modul">
            <el-dialog :title="taskFormTitle" :visible.sync="dialogNewTaskFormVisible">
                <el-form :model="taskForm" :rules="taskRules" ref="taskForm" label-width="120px" class="dremo-ruleForm">
                    <el-form-item label="任务名称" prop="name">
                        <el-input v-model="taskForm.name"></el-input>
                    </el-form-item>
                    <el-form-item label="任务描述" prop="description">
                        <el-input v-model="taskForm.description"></el-input>
                    </el-form-item>
                    <!--<el-form-item label="关联策略" prop="policy_id">-->
                        <!--<el-select v-model="taskForm.policy_id" placeholder="请选择任务执行策略">-->
                            <!--<el-option v-for="policy in policies"  :label="policy.name" :value="policy.id" :key="policy.id"></el-option>-->
                        <!--</el-select>-->
                        <!--<div><span v-for="policy in policies" v-if="taskForm.policy_id == policy.id"style="">{{ policy.description }}</span></div>-->
                    <!--</el-form-item>-->
                    <el-form-item label="开始时间" prop="start_time">
                        <el-date-picker v-model="taskForm.start_time" type="datetime" placeholder="选择日期时间"></el-date-picker>
                    </el-form-item>
                    <el-form-item label="执行周期(时)" prop="interval">
                        <el-input type="number" v-model="taskForm.interval" placeholder="请设置执行周期，必须为大于或者等于1的数值"></el-input>
                    </el-form-item>
                    <el-form-item label="选择作业机" prop="worker_id">
                        <el-select v-model="taskForm.worker_id" placeholder="请选择任务作业机">
                            <el-option v-for="worker in workers"  :label="worker.name" :value="worker.id" :key="worker.id"></el-option>
                        </el-select>
                        <div><span v-for="worker in workers" v-if="taskForm.worker_id == worker.id"style="">IP: {{ worker.ip }}</span></div>
                    </el-form-item>
                    <el-form-item label="备份源地址" prop="source">
                        <el-input type="text" v-model="taskForm.source" placeholder="格式：目录名以 / 分割，目录名可以包含字符有“-”，“_”，“.”以及数值和字母，注意备份目录以“/”结束，文件无需加“/”，如 /A/B/"></el-input>
                    </el-form-item>
                    <el-form-item label="备份目的地" prop="destination">
                        <el-input type="text" v-model="taskForm.destination" placeholder="格式：卷名[IP]:目录名, 目录名以 / 分割，目录名可以包含字母、数值、点号及下划线以“/”结束，，如 glusterfs:/A/"></el-input>
                    </el-form-item>
                    <el-form-item label="备份保存时间" prop="saetime">
                        <el-date-picker
                                v-model="taskForm.saetime"
                                type="daterange"
                                align="right"
                                placeholder="选择日期范围"
                                :picker-options="pickerOptions">
                        </el-date-picker>
                    </el-form-item>
                    <el-form-item>
                        <el-button type="primary" @click="submitTaskForm('taskForm')">提交</el-button>
                        <el-button @click="resetTaskForm('taskForm')">重置</el-button>
                    </el-form-item>
                </el-form>
            </el-dialog>
            <el-dialog title="任务详情" :visible.sync="dialogTaskDetailFormVisible">
                <div class="detail">
                    <div class="detail-item">
                        <div class="item-key">任务名称&nbsp:</div>
                        <div class="item-value">&nbsp{{ taskDetailForm.task.name }}</div>
                    </div>
                    <div class="detail-item">
                        <div class="item-key">任务详情&nbsp:</div>
                        <div class="item-value">&nbsp{{ taskDetailForm.task.description }}</div>
                    </div>
                    <div class="detail-item">
                        <div class="item-key">备份源地址&nbsp:</div>
                        <div class="item-value">&nbsp{{ taskDetailForm.task.source }}</div>
                    </div>
                    <div class="detail-item">
                        <div class="item-key">备份目的地&nbsp:</div>
                        <div class="item-value">&nbsp{{ taskDetailForm.task.destination }}</div>
                    </div>
                    <div class="detail-item">
                        <div class="item-key">备份保留时间(天)&nbsp:</div>
                        <div class="item-value">&nbsp{{ taskDetailForm.task.duration }}</div>
                    </div>
                    <div class="detail-item">
                        <div class="item-key">备份开始时间&nbsp:</div>
                        <div class="item-value">&nbsp{{ taskDetailForm.task.start_time | timeStamp2datetime }}</div>
                    </div>
                    <div class="detail-item">
                        <div class="item-key">备份周期(时)&nbsp:</div>
                        <div class="item-value">&nbsp{{ taskDetailForm.task.interval }}</div>
                    </div>
                    <div class="detail-item">
                        <div class="item-key">工作机&nbsp:</div>
                        <div class="item-value">&nbsp{{ taskDetailForm.worker.name }}</div>
                    </div>
                    <div class="detail-item">
                        <div class="item-key">创建时间&nbsp:</div>
                        <div class="item-value">&nbsp{{ taskDetailForm.task.created_at | timeStamp2datetime }}</div>
                    </div>
                    <div class="detail-item">
                        <div class="item-key">最近更新&nbsp:</div>
                        <div class="item-value">&nbsp{{ taskDetailForm.task.updated_at | timeStamp2datetime }}</div>
                    </div>
                    <!--<div class="detail-item">-->
                        <!--<div class="item-key">任务用户&nbsp:</div>-->
                        <!--<div class="item-value">&nbsp{{ taskDetailForm.user.name }}</div>-->
                    <!--</div>-->
                </div>
            </el-dialog>
            <el-dialog title="作业机" :visible.sync="dialogTableWorkerVisible" size="my-small">
                <el-table :data="workers"
                          border
                          max-height="250" style="width: 540px; argin: auto;">
                    <el-table-column property="name" label="主机名" width="120" placeholder="请输入作业机的hostname"></el-table-column>
                    <el-table-column property="ip" label="IP"></el-table-column>
                    <el-table-column label="操作" width="80">
                        <template scope="scope">
                            <el-button type="text" icon="delete" style="color: red" @click="confimDeleteMsgbox('deleteWorker',scope.$index, scope.row, _self.confimWorkerDeleteMsg)"></el-button>
                            <!--<el-button-->
                                    <!--size="small"-->
                                    <!--type="danger"-->
                                    <!--@click="deleteWorker(scope.$index, scope.row)">删除</el-button>-->
                        </template>
                    </el-table-column>
                    <!--<el-table-column property="host" label="地址"></el-table-column>-->
                </el-table>

                <div style="text-align: center;">
                    <el-button type="text" @click="dialogNewWorkerFormVisible = true" class="my-el-button-right" style="margin-right: auto; margin-left: auto; float:none">添加作业机</el-button>
                </div>
                <div v-if="dialogNewWorkerFormVisible">
                    <el-form :model="worker" style="margin-top:40px" :rules="workerRules" ref="worker">
                        <el-form-item label="主机名" :label-width="formLabelWidth" prop="name">
                            <el-input v-model="worker.name" auto-complete="off"></el-input>
                        </el-form-item>
                        <el-form-item label="IP" :label-width="formLabelWidth" prop="ip">
                            <el-input v-model="worker.ip" auto-complete="off"></el-input>
                        </el-form-item>
                    </el-form>
                    <div slot="footer" class="dialog-footer">
                        <el-button @click="dialogNewWorkerFormVisible = false">取 消</el-button>
                        <el-button type="primary" @click="submitWorkerForm('worker')">确 定</el-button>
                    </div>
                </div>
            </el-dialog>
            <el-dialog title="高级查询" :visible.sync="dialogSearchModelFormVisible" size="tiny">
                <el-form ref="searchModel" :model="searchModel">
                    <!--<el-form-item label="关联策略">-->
                        <!--<el-select v-model="searchModel.policy_id" placeholder="请选择任务执行策略">-->
                            <!--<el-option v-for="policy in policies"  :label="policy.name" :value="policy.id" :key="policy.id"></el-option>-->
                        <!--</el-select>-->
                    <!--</el-form-item>-->
                    <el-form-item label="选择作业机">
                        <el-select v-model="searchModel.worker_id" placeholder="请选择任务作业机">
                            <el-option v-for="worker in workers"  :label="worker.name" :value="worker.id" :key="worker.id"></el-option>
                        </el-select>
                    </el-form-item>
                    <el-form-item label="已删除">
                        <el-switch on-text="" off-text="" v-model="searchModel.deleted"></el-switch>
                    </el-form-item>
                    <el-form-item style="text-align: center;">
                        <el-button type="primary" @click="submitSearchTaskForm">提交</el-button>
                        <el-button @click="resetSearchTaskForm">重置</el-button>
                    </el-form-item>
                </el-form>
            </el-dialog>
            <el-dialog :title="currTaskStateTabTitle" :visible.sync="dialogTaskStateDetailTableVisible">
                <el-table :data="taskStates"
                          border
                          style="argin: auto;">
                    <el-table-column label="开始时间" width="180">
                        <template scope="scope">
                            <span>{{ scope.row.start_time | dateStampFormat }}</span>
                        </template>
                    </el-table-column>
                    <el-table-column label="结束时间" width="180">
                        <template scope="scope">
                            <span>{{ scope.row.end_time | dateStampFormat }}</span>
                        </template>
                    </el-table-column>
                    <el-table-column label="总大小" width="120">
                        <template scope="scope">
                            <span>{{ scope.row.total_size | Bytes }}</span>
                        </template>
                    </el-table-column>
                    <el-table-column label="已备份" width="120">
                        <template scope="scope">
                            <span>{{ scope.row.current_size | Bytes }}</span>
                        </template>
                    </el-table-column>
                    <!--<el-table-column label="创建时间" width="180">-->
                        <!--<template scope="scope">-->
                            <!--<span>{{ scope.row.created_at | dateStampFormat }}</span>-->
                        <!--</template>-->
                    <!--</el-table-column>-->
                    <el-table-column label="更新时间" width="180">
                        <template scope="scope">
                            <span>{{ scope.row.updated_at | dateStampFormat }}</span>
                        </template>
                    </el-table-column>
                    <el-table-column label="任务状态" min-width="180">
                        <template scope="scope">
                            <span v-if="scope.row && scope.row.state == 'success'" style="color: green">已完成</span>
                            <span v-else-if="scope.row && scope.row.state == 'start'" style="color: blue">执行中...</span>
                            <span v-else-if="scope.row && scope.row.state == 'failed'" style="color: red">失败</span>
                            <el-progress v-else-if="scope.row" :percentage="parseInt(scope.row.state)"></el-progress>
                            <span v-else style="color: #F7AD01">未开始</span>
                        </template>
                    </el-table-column>
                    <!--<el-table-column property="host" label="地址"></el-table-column>-->
                </el-table>
                <el-pagination
                        @size-change="taskStateHandleSizeChange"
                        @current-change="taskStateHandleCurrentChange"
                        :current-page="taskStateFilter.page"
                        :page-sizes="[10, 15]"
                        :page-size="taskStateFilter.per_page"
                        layout="total, sizes, prev, pager, next, jumper"
                        :total="taskState_total_rows">
                </el-pagination>
            </el-dialog>
        </div>
    </div>
</template>
<script>
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
        var validateBackupSAddr = (rule, value, callback) => {
            var addr = /^\/[-.\w]+([/]{1}[-\w]+)*[-.\w\/]$/
            if (!addr.test(value)) {
                callback(new Error('输入格式不正确，请重新输入！'));
            }else{
                callback();
            }
        };
        var validateBackupDAddr = (rule, value, callback) => {
            //var addr = /^\w+:([/]{1}\w+)*\/$/
            var addr = /^\w[-.\w]+:([/]{1}[-.\w]+)*\/$/
            if (!addr.test(value)) {
                callback(new Error('输入格式不正确，请重新输入！'));
            }else{
                callback();
            }
        };
        var validateSaeTime = (rule, value, callback) => {
            if (value == "") {
                callback();
            }
            var nTime = new Date();
            var sTime = new Date(value[0]);
            var tmp = new Date(sTime);
            sTime = new Date(nTime);
            sTime.setFullYear(tmp.getFullYear(), tmp.getMonth(), tmp.getDate());
            if (sTime < nTime && this.taskFormSubmitMethod == "post") {
                callback(new Error('起始日期必须至少为今天'));
            }else{
                callback();
            }
        };
        var validateInterval = (rule, value, callback) => {
            var interval = /^[0-9]+$/;
            if (!interval.test(value) || (parseInt(value) < 1)){
                callback(new Error('输入格式不正确，请重新输入！'));
            }else{
                callback();
            }
        };
        var validateTime = (rule, value, callback) => {
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
            //-----保存时间选择----
            pickerOptions: {
                shortcuts: [{
                    text: '保存一周',
                    onClick(picker) {
                        const end = new Date();
                        const start = new Date();
                        end.setTime(start.getTime() + 3600 * 1000 * 24 * 7);
                        picker.$emit('pick', [start, end]);
                    }
                }, {
                    text: '保存一个月',
                    onClick(picker) {
                        const end = new Date();
                        const start = new Date();
                        end.setTime(start.getTime() + 3600 * 1000 * 24 * 30);
                        picker.$emit('pick', [start, end]);
                    }
                }, {
                    text: '保存三个月',
                    onClick(picker) {
                        const end = new Date();
                        const start = new Date();
                        end.setTime(start.getTime() + 3600 * 1000 * 24 * 90);
                        picker.$emit('pick', [start, end]);
                    }
                }]
            },
            //-----作业机----
            worker: {
                name: '',
                ip: '0.0.0.0',
                id: 0,
                port: '',
            },
            workers: [],
            //-----表单数据----
            tableDataTask: [],
            multipleSelection: [],
            taskStates: [],
            //-----分页数据---
            tabLoading: true,
            filter: {
                per_page: 10,   //页大小
                page: 1   //当前页
            },
            total_rows: 0,
            taskStateFilter:{
                per_page: 10,   //页大小
                page: 1   //当前页
            },
            taskState_total_rows: 0,
            //-----搜索条件----
            searchModel: {
                worker_name: '',
                worker_id: '',
                name: '',
                policy_name: '',
                policy_id: '',
                deleted: false,
            },
            searchCond: '',
            gdeleted: false,
            //-----策略列表----
            policies: [],
            policyTips: '',
            formLabelWidth: '120',
            taskFormTitle: '新建任务',
            taskFormSubmitMethod: 'post',
            currTaskStateTabTitle: '',
            currTaskRow: '',
            dialogTaskDetailFormVisible: false,
            dialogNewTaskFormVisible: false,
            dialogTableWorkerVisible: false,
            dialogNewWorkerFormVisible: false,
            dialogSearchModelFormVisible: false,
            dialogTaskStateDetailTableVisible: false,
            confimTaskDeleteMsg: '您确定要删除这个备份任务吗？',
            confimWorkerDeleteMsg: '您确定要删除这个作业机吗？',
            intervalTask: '',
            taskDetailForm: {
                task: {},
                policy: {},
                worker: {},
                user: {}
            },
            taskForm: {
                //id: 0,
                name: '',
                description: '',
                user_id: 1,
                policy_id: '',
                worker_id: '',
                source: '',
                destination: '',
                duration: '',
                created_at: '',
                updated_at: '',
                start_time: '',
                interval: '',
                saetime: ''
            },
            workerRules: {
                name: [
                    { required: true, message: '请输入作业机的主机名', trigger: 'blur' },
                ],
                ip: [
                    {required: true, validator: validateIp, trigger: 'blur'}
                ]
            },
            taskRules: {
                name: [
                    { required: true, message: '请输入具有意义任务名称'},
                    { min: 5, max: 30, message: '长度在 5 到 30 个字符'}
                ],
                description: [
                    { required: true, message: '请输入任务描述信息'},
                    { min: 5, max: 100, message: '长度在 5 到 100 个字符'}
                ],
                policy_id: [
                    {required: true, message: '请为任务选择执行策略'}
                ],
                worker_id: [
                    {required: true, message: '请选择执行任务的工作机'}
                ],
                source:[
                    {required: true, validator: validateBackupSAddr,}
                ],
                destination: [
                    {required: true, validator: validateBackupDAddr,}
                ],
                start_time: [
                    { required: true, validator: validateTime}
                ],
                interval: [
                    {  required: true, validator: validateInterval}
                ],
                saetime: [
                    {required: true, validator: validateSaeTime,}
                ]
            }
        }
    },
    created() {
        // 组件创建完后获取数据，
        // 此时 data 已经被 observed 了
        this.fetchTaskLists(),
        this.getPolicies(),
        this.getWorkers(),
        this.getUser(),
        this.initializeSearchCond(),
        this.intervalTask = setInterval(() => {
            this.fetchTaskLists();
        },15000)
    },
    watch: {
        // 如果路由有变化，会再次执行该方法
        '$route': ['fetchTaskLists','getPolicies','getWorkers','initializeSearchCond']
    },
    beforeDestroy() {
        clearInterval(this.intervalTask)
    },
    methods: {
        //----时间格式化----
        date2str(row, column, cellValue){
            var date = new Date(row.task[column.property]);
            if (row.task[column.property] == 0 || row.task[column.property] == '0' || date == undefined){
                return "-";
            }
            var datetime = this.myDateFormat(date,"yyyy-MM-dd hh:mm:ss");
            return datetime;
        },
        //-----展开做业机对话框----
        workerInfo(){
            this.dialogTableWorkerVisible = true;
            this.dialogNewWorkerFormVisible = false;
        },
        //-----校验搜索输入格式-----
        validateSearchCond(){
            var test = /^policy=|worker=[-_\w]+(;(policy=|worker=)[-_.\w]+){0,}$/;
            if (this.searchCond != ''){
                if(!test.test(this.searchCond)) {
                    this.openMsg("请输入正确的格式，不要包含除数字，字母，“-”，“_”,“.”之外的其他字符","error");
                    this.searchCond = '';
                }
            }
        },
        //-----条件搜索格式化----
        formatSearchCond(){
            var conds = this.searchCond.split(";");
            for (var i = 0; i < conds.length; i++){
                var key = conds[i].split("=")[0];
                var value = conds[i].split("=")[1];
                if (key == "policy"){
                    this.searchModel.policy_name = value;
                }
                if (key == "worker"){
                    this.searchModel.worker_name = value;
                }
            }
        },
        //-----计算时间差----
        getDateDiff(startTime, endTime, diffType) {
            var sTime =new Date(startTime); //开始时间
            var eTime =new Date(endTime); //结束时间
            var timeType =1;
            switch (diffType) {
                case"second":
                    timeType =1000;
                break;
                case"minute":
                    timeType =1000*60;
                break;
                case"hour":
                    timeType =1000*3600;
                break;
                case"day":
                    timeType =1000*3600*24;
                break;
                default:
                break;
            }
            return parseInt((eTime.getTime() - sTime.getTime()) / parseInt(timeType));
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
        initializeTaskForm() {
            this.taskForm = {
                'name': '',
                'description': '',
                'user_id': '',
                'policy_id': '',
                'worker_id': '',
                'source': '',
                'destination': '',
                'duration': '',
                'created_at': '',
                'updated_at': '',
                'start_time': '',
                'interval': '',
                'saetime': ''
            };
            this.taskFormTitle = '新建任务';
            this.taskFormSubmitMethod = 'post';
            console.log(this.taskForm);
        },
        initializeSearchCond(){
            this.searchModel = {
                'worker_name': '',
                'worker_id': '',
                'name': '',
                'policy_name': '',
                'policy_id': '',
                'deleted': false,
            };
            this.searchCond = '';
            this.gdeleted = false;
            this.fetchTaskLists();
        },
        //-----获取用户-----
        getUser() {

        },
        //-----获取作业机----
        getWorkers() {
            this.$http.get(this.GLOBAL.url+"/backup/workers").then(response => {
                this.workers  = response.data.workers;
                /**for(var i = 0; i < this.workers.length; i++){
                    this.workers[i].id = this.workers[i].id.toString();
                }*/
                /*this.tabLoading = false;*/
            },err => {
                if(err.status){
                    //alert(err.status);
                }
            })
            .catch(function(response) {
                console.log(response);
            })

        },
        //-----获取策略列表
        getPolicies() {
            this.$http.get(this.GLOBAL.url+"/backup/policies").then(response => {
                this.policies  = response.data.policies;
                /**for(var i = 0; i < this.policies.length; i++){
                    this.policies[i].id = this.policies[i].id.toString();
                }*/
                /*this.tabLoading = false;*/
            })
            .catch(function(response) {
                console.log(response);
            })
        },
        //-----获取任务列表----
        fetchTaskLists() {
            this.tabLoading = true;
            var page_offset = this.filter.per_page * (this.filter.page - 1);
            var datas = {
                limit: this.filter.per_page,
                offset: page_offset,
                worker_id: this.searchModel.worker_id,
                worker_name: this.searchModel.worker_name,
                policy_id: this.searchModel.policy_id,
                policy_name: this.searchModel.policy_name,
                name: this.searchModel.name,
            };
            if(this.searchModel.deleted){
                datas.deleted = 'True';
                this.gdeleted = true;
            }
            this.$http.get(this.GLOBAL.url+"/backup/tasks/detail", {
                params: datas,
                timeout: 3000
            }).then(res => {
                //var tasks  = res.data.tasks;
                this.total_rows = res.data.total;
                this.filter.page = this.filter.page;
                this.filter.per_page = this.filter.per_page;
                this.tableDataTask = res.data.tasks;
                //this.tableDataTask = this.removeRowFromDTask(tasks);
                this.tabLoading = false;
            },err => {
                console.log(err.response.status);
                this.tabLoading = false;
                if (err.response.status == 404){
                    this.openMsg('您要的结果不存在', 'warning');
                    this.initializeSearchCond();
                    this.tableDataTask = [];
                }else{
                    this.openMsg('请求错误', 'warning');
                }
            })
            .catch(function(response) {
                console.log(response);
            });
        },
        //-----去未删除的任务表记录
        removeRowFromDTask(tasks){
            for(var i = 0; i < tasks.length; i++){
                if(tasks[i].deleted != 'deleted' && this.gdeleted){
                    tasks.splice(i,1);
                    i = i - 1;
                }
            }
            return tasks;
        },
        //-----新建任务----
        newTask(){
            this.initializeTaskForm();
            this.dialogNewTaskFormVisible = true;
        },
        //-----新建作业机----
        submitWorkerForm(formName) {
            this.$refs[formName].validate((valid) => {
                if (valid){
                    this.axios.post(this.GLOBAL.url+"/backup/workers",this.worker).then(res => {
                                this.openMsg('新增作业机成功', 'success');
                                this.getWorkers();
                                this.dialogNewWorkerFormVisible = false;
                            },err => {
                                console.log(err.response.status);
                                this.openMsg('新增作业机失败', 'error');
                            })
                            .catch(function(response) {
                                console.log(response);
                                this.openMsg('新增作业机异常', 'warning');
                        });
                }else{
                    this.openMsg('信息输入不正确，请检查格式！', 'error')
                    /*this.initializeTaskForm();*/
                    return false;
                }
            })
        },
        //-----提交新建任务----
        submitTaskForm(formName) {
            this.taskForm.duration = this.getDateDiff(this.taskForm.saetime[0], this.taskForm.saetime[1], 'day');
            this.taskForm.start_time = new Date(this.taskForm.start_time).getTime();
            //this.$refs.taskForm.validate((valid) => {
            var appendstr = '';
            this.$refs[formName].validate((valid) => {
                if (valid) {
                    if(this.taskFormSubmitMethod == 'put') {
                        appendstr = '/'+this.taskForm.id
                        //this.taskForm.policy_id = parseInt(this.taskForm.policy_id);
                        //this.taskForm.worker_id = parseInt(this.taskForm.worker_id);
                        this.axios.put(this.GLOBAL.url+"/backup/tasks"+appendstr,this.taskForm).then(res => {
                                this.filter.page = 1;
                                this.fetchTaskLists();
                                this.openMsg(this.taskFormTitle+'成功', 'success');
                                this.dialogNewTaskFormVisible = false;
                            },err => {
                                console.log(err.response.status);
                                this.openMsg(this.taskFormTitle+'失败', 'error');
                            })
                            .catch(function(response) {
                                console.log(response);
                                this.openMsg(this.taskFormTitle+'异常', 'warning');
                        });
                    }else{
                        this.axios.post(this.GLOBAL.url+"/backup/tasks",this.taskForm).then(res => {
                                this.filter.page = 1;
                                this.fetchTaskLists();
                                this.openMsg(this.taskFormTitle+'成功', 'success');
                                this.dialogNewTaskFormVisible = false;
                            },err => {
                                console.log(err.response.status);
                                this.openMsg(this.taskFormTitle+'失败', 'error');
                            })
                            .catch(function(response) {
                                console.log(response);
                                this.openMsg(this.taskFormTitle+'异常', 'warning');
                        });
                    }
                    //this.initializeTaskForm();
                } else {
                    this.openMsg('信息输入不正确，请检查格式！', 'error')
                    /*this.initializeTaskForm();*/
                    return false;
                }
            });
        },
        resetTaskForm(formName) {
            this.$refs[formName].resetFields();
        },

        //-----搜索任务
        searchTask() {
            console.log("查询");
            this.formatSearchCond();
            this.fetchTaskLists();
        },
        searchTaskMore(){
            this.dialogSearchModelFormVisible = true;
        },
        submitSearchTaskForm(){
            this.fetchTaskLists();
            this.dialogSearchModelFormVisible = false;
        },
        resetSearchTaskForm(){
            this.searchModel = {
                'worker_name': '',
                'worker_id': '',
                'name': '',
                'policy_name': '',
                'policy_id': '',
                'deleted': false,
            };
            this.searchCond = '';
        },
        //-----删除任务
        deleteTasks() {
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
        taskStateDetail(row) {
            this.taskStateFilter.per_page = 10;
            this.taskStateFilter.page = 1;
            this.currTaskRow = row.task.id;
            this.getTaskStates(this.currTaskRow);
            this.currTaskStateTabTitle = row.task.name;
        },
        getTaskStates(task_id){
            var page_offset = this.taskStateFilter.per_page * (this.taskStateFilter.page - 1);
            this.$http.get(this.GLOBAL.url+"/backup/backupstates",{
                params: {
                    limit: this.taskStateFilter.per_page,
                    offset: page_offset,
                    task_id: task_id,
                }
            }).then(res => {
                this.taskStates = res.data.states;
                this.dialogTaskStateDetailTableVisible = true;
                this.taskState_total_rows = res.data.total;
                this.taskStateFilter.page = this.taskStateFilter.page;
                this.taskStateFilter.per_page = this.taskStateFilter.per_page;
            },err => {
                console.log(err.response.status);
                this.tabLoading = false;
                this.openMsg('请求错误', 'warning')
            })
            .catch(function(response) {
                console.log(response);
            });
        },
        //-----分页----
        handleSizeChange(val) {
            this.filter.per_page = val;
            this.fetchTaskLists();
            console.log(`每页 ${val} 条`);
        },
        handleCurrentChange(val) {
            this.filter.page = val;
            this.fetchTaskLists();
            console.log(`当前页: ${val}`);
        },
        taskStateHandleSizeChange(val) {
            this.taskStateFilter.per_page = val;
            this.getTaskStates(this.currTaskRow);
            console.log(`每页 ${val} 条`);
        },
        taskStateHandleCurrentChange(val) {
            this.taskStateFilter.page = val;
            this.getTaskStates(this.currTaskRow);
            console.log(`当前页: ${val}`);
        },
        //-----操作任务记录----
        taskDetail(index, row) {
            this.$http.get(this.GLOBAL.url+"/backup/tasks/"+row.id).then(res => {
                this.dialogTaskDetailFormVisible = true;
                this.taskDetailForm = res.data;
            },err => {
                console.log(err.response.status);
                this.tabLoading = false;
                this.openMsg('请求错误', 'warning')
            })
            .catch(function(response) {
                console.log(response);
            });
            console.log(index, row);
        },
        handleEdit(index, row) {
            this.taskFormTitle = '修改任务';
            this.taskFormSubmitMethod = 'put';
            var startTime = new Date(row.created_at);
            var endTime = new Date(row.created_at + row.duration*24*3600*1000)
            this.taskForm = row;
            //this.taskForm.policy_id = this.taskForm.policy_id.toString();
            //this.taskForm.worker_id = this.taskForm.worker_id.toString();
            this.taskForm.saetime = new Array();
            this.taskForm.saetime[0] = startTime;
            this.taskForm.saetime[1] = endTime;
            this.dialogNewTaskFormVisible = true;
        },
        handleDelete(index, row) {
            this.axios.delete(this.GLOBAL.url+"/backup/tasks/"+row.id).then(res => {
                this.fetchTaskLists();
                this.openMsg('删除成功', 'success')
            },err => {
                console.log(err.res.status);
                this.tabLoading = false;
                this.openMsg('删除失败', 'error')
            })
            .catch(function(res) {
                console.log(res);
                this.openMsg('请求异常', 'warning')
            });
            console.log(index, row);
        },
        deleteWorker(index, row) {
            this.axios.delete(this.GLOBAL.url+"/backup/workers/"+row.id).then(res => {
                var ds = res.data.code;
                var tips = '';
                if(ds == '200'){
                    this.getWorkers();
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
            console.log(index, row);
        },
        confimDeleteMsgbox(func, index, row, mymsg){
            const h = this.$createElement;
            this.$msgbox({
                title: '重要提醒',
                message: h('p',{style: 'color: red'}, mymsg),
                type: 'warning',
                showCancelButton: true,
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                beforeClose: (action, instance, done) => {
                    if (action === 'confirm') {
                        if(func == 'handleDelete'){
                            this.handleDelete(index, row);
                        }else if(func == 'deleteWorker'){
                            this.deleteWorker(index, row);
                        }
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
