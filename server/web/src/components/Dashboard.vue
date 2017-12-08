<template>
  <el-row class="warp">
    <el-col :span="24" class="warp-breadcrum">
      <el-breadcrumb separator="/">
        <el-breadcrumb-item :to="{ path: '/' }"><b>首页</b></el-breadcrumb-item>
      </el-breadcrumb>
    </el-col>
    <el-tabs style="margin-top:34px">
    </el-tabs>
    <el-col :span="24" class="warp-main">
      <section class="chart-container">
        <el-row>
          <el-col :span="5" class="bar-card">
            <el-row>
              <el-col :span="24" class="bar-card-title">
                统计数据
              </el-col>
              <el-col :span="24" class="bar-card-container">
                <el-row>
                  <el-col :span="6" class="bar-card-item-value">
                    {{ sumaries.task_num }}
                  </el-col>
                  <el-col :span="6" class="bar-card-item-msg">
                    个任务
                  </el-col>
                  <el-col :span="6" class="bar-card-item-value">
                    {{ sumaries.worker_num }}
                  </el-col>
                  <el-col :span="6" class="bar-card-item-msg">
                    个客户端
                  </el-col>
                </el-row>
                <el-row>
                  <el-col :span="6" class="bar-card-item-value">
                    {{ sumaries.user_num }}
                  </el-col>
                  <el-col :span="6" class="bar-card-item-msg">
                    个用户
                  </el-col>
                  <el-col :span="6" class="bar-card-item-value">
                    {{ sumaries.group_num }}
                  </el-col>
                  <el-col :span="6" class="bar-card-item-msg">
                    个组
                  </el-col>
                </el-row>
              </el-col>
            </el-row>
          </el-col>
          <el-col :span="6" class="bar-card">
            <el-row>
              <el-col :span="24" class="bar-card-title">
                备份任务
              </el-col>
              <el-col :span="14" style="border-right:1px solid #ddd;">
                <div id="chartBackupSummary" style="width:100%; height:200px;"></div>
              </el-col>
              <el-col :span="8" class="bar-card-right" style="margin-left: 20px; line-height: 100%; padding: 25px 0px;">
                <section>
                  <el-row>
                    <el-col :span="16" class="bar-card-info-key">
                      任务总数：
                    </el-col>
                    <el-col :span="8" class="bar-card-info-value">
                      {{ backupTaskSummary.total }}
                    </el-col>
                  </el-row>
                  <el-row>
                    <el-col :span="16" class="bar-card-info-key">
                      任务等待数：
                    </el-col>
                    <el-col :span="8" class="bar-card-info-value">
                      {{ backupTaskSummary.currWaiting }}
                    </el-col>
                  </el-row>
                  <el-row>
                    <el-col :span="16" class="bar-card-info-key">
                      任务执行数：
                    </el-col>
                    <el-col :span="8" class="bar-card-info-value">
                      {{ backupTaskSummary.currRunning }}
                    </el-col>
                  </el-row>
                  <el-row>
                    <el-col :span="16" class="bar-card-info-key">
                      任务停止数：
                    </el-col>
                    <el-col :span="8" class="bar-card-info-value">
                      {{ backupTaskSummary.currStopped }}
                    </el-col>
                  </el-row>
                </section>
              </el-col>
            </el-row>
          </el-col>
          <el-col :span="6" class="bar-card">
            <el-row>
              <el-col :span="24" class="bar-card-title">
                备份恢复任务
              </el-col>
              <el-col :span="14" class="bar-card-left" style="border-right:1px solid #ddd;">
                <div id="chartRecoverySummary" style="width:100%; height:200px;"></div>
              </el-col>
              <el-col :span="8" class="bar-card-right" style="margin-left: 20px; line-height: 100%; padding: 25px 0px;">
                <section>
                  <el-row>
                    <el-col :span="16" class="bar-card-info-key">
                      任务总数：
                    </el-col>
                    <el-col :span="8" class="bar-card-info-value">
                      {{ recoveryTaskSummary.total }}
                    </el-col>
                  </el-row>
                  <el-row>
                    <el-col :span="16" class="bar-card-info-key">
                      任务等待数：
                    </el-col>
                    <el-col :span="8" class="bar-card-info-value">
                      {{ recoveryTaskSummary.currWaiting }}
                    </el-col>
                  </el-row>
                  <el-row>
                    <el-col :span="16" class="bar-card-info-key">
                      任务执行数：
                    </el-col>
                    <el-col :span="8" class="bar-card-info-value">
                      {{ recoveryTaskSummary.currRunning }}
                    </el-col>
                  </el-row>
                  <el-row>
                    <el-col :span="16" class="bar-card-info-key">
                      任务停止数：
                    </el-col>
                    <el-col :span="8" class="bar-card-info-value">
                      {{ recoveryTaskSummary.currStopped }}
                    </el-col>
                  </el-row>
                </section>
              </el-col>
            </el-row>
          </el-col>
          <el-col :span="6" class="bar-card">
            <el-row>
              <el-col :span="24" class="bar-card-title">
                客户端
              </el-col>
              <el-col :span="14" style="border-right:1px solid #ddd;">
                <div id="chartWorkerSummary" style="width:100%; height:200px;"></div>
              </el-col>
              <el-col :span="8" class="bar-card-right" style="margin-left: 20px; line-height: 100%; padding: 25px 0px;">
                <section>
                  <el-row>
                    <el-col :span="16" class="bar-card-info-key">
                      客户端总数：
                    </el-col>
                    <el-col :span="8" class="bar-card-info-value">
                      {{ workerSummary.total }}
                    </el-col>
                  </el-row>
                  <el-row>
                    <el-col :span="16" class="bar-card-info-key">
                      服务在线：
                    </el-col>
                    <el-col :span="8" class="bar-card-info-value">
                      {{ workerSummary.currActive }}
                    </el-col>
                  </el-row>
                  <el-row>
                    <el-col :span="16" class="bar-card-info-key">
                      服务异常：
                    </el-col>
                    <el-col :span="8" class="bar-card-info-value">
                      {{ workerSummary.currOffline }}
                    </el-col>
                  </el-row>
                </section>
              </el-col>
            </el-row>
          </el-col>
        </el-row>
      </section>

      <el-col :span="24">
        <el-col :span="15">
          <div id="chartTaskStateSummary" class="divTaskState" v-if="!isTaskStateDataNull"></div>
          <!--<div class="divTaskState" v-if="isTaskStateDataNull">暂无数据</div>-->
        </el-col>
        <el-col :span="8">
          <div
            style="margin:5px 15px; padding:10px 10px 0px; width: 100%; height: 470px; border: 1px solid #1f2d3d;border-radius:5px">
            <el-table :data="OplogList" highlight-current-row style="width: 100%;" max-height="470">
              <el-table-column prop="username" label="用户名" width="100rem">
              </el-table-column>
              <el-table-column prop="created_at" label="时间" width="180rem" show-overflow-tooltip>
                <template slot-scope="scope">
                  <span>{{ scope.row.created_at | dateStampFormat }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="message" label="日志">
              </el-table-column>
            </el-table>
          </div>
        </el-col>
      </el-col>

    </el-col>

  </el-row>
</template>
<style>
  .time {
    font-size: 13px;
    color: #999;
  }

  .bottom {
    margin-top: 13px;
    line-height: 12px;
  }

  .image {
    width: 100%;
    display: block;
  }

  .clearfix:before,
  .clearfix:after {
    display: table;
    content: "";
  }

  .clearfix:after {
    clear: both
  }

  .chart-container {
    width: 100%;
  }

  .chart-container .el-col {
    padding: 10px 5px;
  }

  .bar-card {
    border: 1px solid #333744;
    border-radius: 4px;
    overflow: hidden;
    margin: 5px 5px;
    height: 280px;
    /*background-color: #333744*/
  }

  .bar-card-title {
    font-size: 16px;
    font-weight: bold;
    font-family: 'Avenir', Helvetica, Arial, sans-serif;
    /*color:#FFFFFF;*/
  }

  .chart-container .el-col .bar-card-item-value {
    font-family: 'Avenir', Helvetica, Arial, sans-serif;
    font-size: 38px;
    font-weight: bold;
    text-align: right;
    margin: 10px 0px;
    color: #1d90e6;
  }

  .chart-container .el-col .bar-card-item-msg {
    font-family: 'Avenir', Helvetica, Arial, sans-serif;
    font-size: 14px;
    line-height: 100%;
    padding: 40px 5px;
  }

  .el-col .el-col-8 .bar-card-right {
    margin-left: 20px;
    line-height: 100%;
    padding: 25px 0px;
  }

  .chart-container .el-col .bar-card-info-key {
    color: #36A9CE;
    font-size: 14px;
    text-align: right;
    padding: 15px 0px;
    line-height: 100%
  }

  .chart-container .el-col .bar-card-info-value {
    color: #36A9CE;
    font-size: 14px;
    padding: 15px 0px;
    line-height: 100%;
    text-align: left;
  }

  .divTaskState {
    margin: 5px;
    width: 100%;
    height: 480px;
    border: 1px solid #1f2d3d;
    border-radius: 5px
  }
</style>

<script>
  import echarts from 'echarts'
  import {
    reqGetTaskList,
    reqGetVolumeList,
    reqGetWorkerList,
    reqGetPolicyList,
    reqGetGroupList,
    reqGetSummaries,
    reqGetOplogList
  } from '../api/api';

  export default {
    data() {
      return {
        sysUserName: '',
        role: '',
        chartBackupSummary: '',
        chartRecoverySummary: '',
        chartWorkerSummary: '',
        chartTaskStateSummary: '',
        intervalTask: '',
        sumaries: {
          task_num: 0,
          user_num: 0,
          worker_num: 0,
          group_num: 0,
          volume_num: 0,
          taskstate_num: 0,
        },
        backupTaskSummary: {
          total: 0,
          currWaiting: 0,
          currStopped: 0,
          currRunning: 0,
          currEnd: 0

        },
        recoveryTaskSummary: {
          total: 0,
          currWaiting: 0,
          currStopped: 0,
          currRunning: 0,
          currEnd: 0
        },
        workerSummary: {
          total: 0,
          currActive: 0,
          currOffline: 0,
        },
        //状态
        isTaskStateDataNull: false,
        state_time_start: 0,
        state_time_end: 0,
        taskStateSummary: {
          total: 0,
          taskname: [],
          success: [],
          failed: [],
          running: [],
          unknown: [],
        },
        OplogList: [],
      };
    },
    methods: {
      initializeBackupTaskSummary() {
        this.backupTaskSummary = {
          total: 0,
          currWaiting: 0,
          currStopped: 0,
          currRunning: 0,
          currEnd: 0

        }
      },
      initializeRecoveryTaskSummary() {
        this.recoveryTaskSummary = {
          total: 0,
          currWaiting: 0,
          currStopped: 0,
          currRunning: 0,
          currEnd: 0

        }
      },
      initializeWorkerSummary() {
        this.workerSummary = {
          total: 0,
          currActive: 0,
          currOffline: 0,
        }
      },
      initializeTaskStateSummary(data) {
        this.taskStateSummary.taskname = [];
        this.taskStateSummary.success = [];
        this.taskStateSummary.failed = [];
        this.taskStateSummary.running = [];
        this.taskStateSummary.unknown = [];
        this.taskStateSummary.total = data.total;
        for (var i in data) {
          if (typeof(data[i].name) !== "undefined") {
            this.taskStateSummary.taskname.push(data[i].name);
          }
          if (typeof(data[i]) !== 'number') {
            if (typeof(data[i].success) !== "undefined") {
              this.taskStateSummary.success.push(data[i].success);
            } else {
              this.taskStateSummary.success.push(0);
            }
            if (typeof(data[i].runing) !== "undefined") {
              this.taskStateSummary.running.push(data[i].runing);
            } else {
              this.taskStateSummary.running.push(0);
            }
            if (typeof(data[i].failed) !== "undefined") {
              this.taskStateSummary.failed.push(data[i].failed);
            } else {
              this.taskStateSummary.failed.push(0);
            }
            if (typeof(data[i].null) !== "undefined") {
              this.taskStateSummary.unknown.push(data[i].null);
            } else {
              this.taskStateSummary.unknown.push(0);
            }
          }
        }
        // console.log(this.taskStateSummary)
      },
      chartBackupSummaryFunc(data) {
        this.initializeBackupTaskSummary();
        if (data.waiting != null) {
          this.backupTaskSummary.currWaiting = data.waiting;
          this.backupTaskSummary.total = this.backupTaskSummary.total + this.backupTaskSummary.currWaiting;
        }
        if (data.running_w != null) {
          this.backupTaskSummary.currRunning = this.backupTaskSummary.currRunning + data.running_w;
          this.backupTaskSummary.total = this.backupTaskSummary.total + this.backupTaskSummary.currRunning;
        }
        if (data.running_s != null) {
          this.backupTaskSummary.currRunning = this.backupTaskSummary.currRunning + data.running_s;
          this.backupTaskSummary.total = this.backupTaskSummary.total + this.backupTaskSummary.currRunning;
        }
        if (data.stopped != null) {
          this.backupTaskSummary.currStopped = data.stopped;
          this.backupTaskSummary.total = this.backupTaskSummary.total + this.backupTaskSummary.currStopped;
        }
        if (data.end != null) {
          this.backupTaskSummary.currEnd = data.end;
          this.backupTaskSummary.total = this.backupTaskSummary.total + this.backupTaskSummary.currEnd;
        }
        this.chartBackupSummary.setOption({
          tooltip: {
            trigger: 'item',
            formatter: "{a} <br/>{b} : {c} ({d}%)"
          },
          legend: {
            orient: 'vertical',
            left: 'left',
            textStyle: {},
            data: [
              {
                name: '等待中',
                icon: 'circle',
              },
              {
                name: '执行中',
                icon: 'circle',
              },
              {
                name: '已停止',
                icon: 'circle',
              },
              {
                name: '已完成',
                icon: 'circle',
              }
            ]
          },
          series: [
            {
              name: '任务状态',
              type: 'pie',
              radius: ['40%', '55%'],
              center: ['60%', '65%'],
              data: [
                {value: this.backupTaskSummary.currWaiting, name: '等待中', itemStyle: {normal: {color: '#f7c410'}}},
                {value: this.backupTaskSummary.currRunning, name: '执行中', itemStyle: {normal: {color: '#00BFFF'}}},
                {value: this.backupTaskSummary.currStopped, name: '已停止', itemStyle: {normal: {color: '#FF4500'}}},
                {value: this.backupTaskSummary.currEnd, name: '已完成', itemStyle: {normal: {color: '#98F898'}}}
              ],
              itemStyle: {
                emphasis: {
                  shadowBlur: 10,
                  shadowOffsetX: 0,
                  shadowColor: 'rgba(0, 0, 0, 0.5)'
                }
              },
              label: {
                normal: {
                  show: false,
                  position: 'center'
                },
              },
              labelLine: {
                normal: {
                  show: false
                }
              },
            }
          ]
        });
        window.onresize = this.chartBackupSummary.resize;
      },
      chartRecoverySummaryFunc(data) {
        this.initializeRecoveryTaskSummary();
        if (data.waiting != null) {
          this.recoveryTaskSummary.currWaiting = data.waiting;
          this.recoveryTaskSummary.total = this.recoveryTaskSummary.total + this.recoveryTaskSummary.currWaiting;
        }
        if (data.running_w != null) {
          this.recoveryTaskSummary.currRunning = this.recoveryTaskSummary.currRunning + data.running_w;
          this.recoveryTaskSummary.total = this.recoveryTaskSummary.total + this.recoveryTaskSummary.currRunning;
        }
        if (data.running_s != null) {
          this.recoveryTaskSummary.currRunning = this.recoveryTaskSummary.currRunning + data.running_s;
          this.recoveryTaskSummary.total = this.recoveryTaskSummary.total + this.recoveryTaskSummary.currRunning;
        }
        if (data.stopped != null) {
          this.recoveryTaskSummary.currStopped = data.stopped;
          this.recoveryTaskSummary.total = this.recoveryTaskSummary.total + this.recoveryTaskSummary.currStopped;
        }
        if (data.end != null) {
          this.recoveryTaskSummary.currEnd = data.end;
          this.recoveryTaskSummary.total = this.recoveryTaskSummary.total + this.recoveryTaskSummary.currEnd;
        }
        this.chartRecoverySummary.setOption({
          tooltip: {
            trigger: 'item',
            formatter: "{a} <br/>{b} : {c} ({d}%)"
          },
          legend: {
            orient: 'vertical',
            left: 'left',
            textStyle: {},
            data: [
              {
                name: '等待中',
                icon: 'circle',
              },
              {
                name: '执行中',
                icon: 'circle',
              },
              {
                name: '已停止',
                icon: 'circle',
              },
              {
                name: '已完成',
                icon: 'circle',
              }
            ]
          },
          series: [
            {
              name: '任务状态',
              type: 'pie',
              radius: ['40%', '55%'],
              center: ['60%', '65%'],
              data: [
                {value: this.recoveryTaskSummary.currWaiting, name: '等待中', itemStyle: {normal: {color: '#f7c410'}}},
                {value: this.recoveryTaskSummary.currRunning, name: '执行中', itemStyle: {normal: {color: '#00BFFF'}}},
                {value: this.recoveryTaskSummary.currStopped, name: '已停止', itemStyle: {normal: {color: '#FF4500'}}},
                {value: this.recoveryTaskSummary.currEnd, name: '已完成', itemStyle: {normal: {color: '#98F898'}}}
              ],
              itemStyle: {
                emphasis: {
                  shadowBlur: 10,
                  shadowOffsetX: 0,
                  shadowColor: 'rgba(0, 0, 0, 0.5)'
                }
              },
              label: {
                normal: {
                  show: false,
                  position: 'center'
                },
              },
              labelLine: {
                normal: {
                  show: false
                }
              },
            }
          ]
        });
        window.onresize = this.chartRecoverySummary.resize;
      },
      chartWorkerSummaryFunc(data) {
        this.initializeWorkerSummary();
        if (data.total != null) {
          this.workerSummary.total = data.total;
        }
        if (data.Active != null) {
          this.workerSummary.currActive = data.Active;
        }
        if (data.Offline != null) {
          this.workerSummary.currOffline = data.Offline;
        }
        this.chartWorkerSummary.setOption({
          tooltip: {
            trigger: 'item',
            formatter: "{a} <br/>{b} : {c} ({d}%)"
          },
          legend: {
            orient: 'vertical',
            left: 'left',
            textStyle: {},
            data: [
              {
                name: '在线',
                icon: 'circle',
              },
              {
                name: '掉线',
                icon: 'circle',
              }
            ]
          },
          series: [
            {
              name: '客户端状态',
              type: 'pie',
              radius: ['40%', '55%'],
              center: ['60%', '65%'],
              data: [
                {value: this.workerSummary.currActive, name: '在线', itemStyle: {normal: {color: '#98F898'}}},
                {value: this.workerSummary.currOffline, name: '掉线', itemStyle: {normal: {color: '#FF4500'}}},
              ],
              itemStyle: {
                emphasis: {
                  shadowBlur: 10,
                  shadowOffsetX: 0,
                  shadowColor: 'rgba(0, 0, 0, 0.5)'
                }
              },
              label: {
                normal: {
                  show: false,
                  position: 'center'
                },
              },
              labelLine: {
                normal: {
                  show: false
                }
              },
            }
          ]
        });
        window.onresize = this.chartWorkerSummary.resize;
      },
      chartTaskStateSummaryFunc(data) {
        this.initializeTaskStateSummary(data);
        // if (this.taskStateSummary.taskname.length !== 0) {
        //   this.isTaskStateDataNull = false;
          this.chartTaskStateSummary.setOption({
            tooltip: {
              trigger: 'axis',
              axisPointer: {            // 坐标轴指示器，坐标轴触发有效
                type: 'shadow'        // 默认为直线，可选为：'line' | 'shadow'
              }
            },
            title: {
              show: true,
              text: '任务执行状况概览',
            },
            legend: {
              data: ['成功', '执行中', '失败', '未知']
            },
            color: ['#98F898', '#00BFFF', '#FF4500', 'grey'],

            grid: {
              left: '3%',
              right: '4%',
              bottom: '20%',
              containLabel: true
            },
            xAxis: {
              type: 'category',
              data: this.taskStateSummary.taskname,
              axisLabel: {
                interval: 0,//横轴信息全部显示
                rotate: -20,//-30度角倾斜显示
              }
            },
            yAxis: {
              show: true,
              type: 'value',
              minInterval: 1
            },
            toolbox: {
              show: true,
              itemSize: 20,
              feature: {
                dataZoom: {
                  show: true,
                  yAxisIndex: false,
                  title: {
                    zoom: '选择缩放区域',
                    back: '返回上一次缩放状态',
                  },
                },
                restore: {
                  show:true,
                  title: '取消缩放'
                },
                myshowToday: {
                  show: true,
                  title: '今天',
                  icon: '<svg>' +
                  '<symbol id="icon-day01" viewBox="0 0 1024 1024">' +
                  '<path d="M854.35374 265.833461c0-38.809911-22.189372-56.839543-57.190537-56.839543l-28.304649-2.574638 0 24.445762c0 40.500413-33.377178 73.317843-74.513064 73.317843-41.166585 0-74.531484-32.81743-74.531484-73.317843l0-24.445762L403.055241 206.41928l0 24.445762c0 40.500413-33.380248 73.317843-74.514087 73.317843-41.167608 0-74.53046-32.81743-74.53046-73.317843l0-24.445762-27.812439 2.574638c-27.438932 0-57.204863 29.839609-57.204863 56.839543 0 0 0 451.081559 0 549.298488 0 45.409213 36.9741 75.760474 71.045079 75.760474 51.232848 0 450.361151-0.014326 538.057469-0.014326 38.931684 0 76.910671-27.267017 76.910671-70.838372C855.005586 691.809225 854.35374 265.833461 854.35374 265.833461zM818.523697 782.317589c0 50.593282-15.544021 70.685899-59.498092 70.685899-114.238834 0-380.15109 0-494.705102 0-36.868699 0-57.173141-19.296485-57.173141-56.839543 0-125.126812-1.954515-428.66399-1.954515-428.66399l613.595886 0C818.788733 367.499955 818.523697 656.972812 818.523697 782.317589z"  ></path>' +
                  '<path d="M327.746044 279.753495c27.018354 0 48.907896-21.554922 48.907896-48.131207l0-50.406017c0-26.576285-21.889543-48.109718-48.907896-48.109718-26.998911 0-48.904827 21.533432-48.904827 48.109718l0 50.406017C278.841218 258.198573 300.747133 279.753495 327.746044 279.753495z"  ></path>' +
                  '<path d="M693.570847 279.753495c26.999934 0 48.88743-21.554922 48.88743-48.131207l0-50.406017c0-26.576285-21.88852-48.109718-48.88743-48.109718-27.018354 0-48.925293 21.533432-48.925293 48.109718l0 50.406017C644.646578 258.198573 666.552493 279.753495 693.570847 279.753495z"  ></path>' +
                  '<path d="M481.809909 733.00958c0 0.054235 0.004093 0.106424 0.004093 0.157589l0 0.303922 0.007163 0c0.24764 16.458857 13.659091 29.726022 30.176276 29.726022 16.518209 0 29.927613-13.267165 30.175253-29.726022l0.016373 0L542.189068 486.666008l-0.007163 0c0.001023-0.033769 0.00307-0.066515 0.00307-0.101307 0-16.671705-13.514805-30.187533-30.187533-30.187533-16.671705 0-30.187533 13.515828-30.187533 30.187533 0 0.053212 0.004093 0.105401 0.004093 0.157589l0 246.127653C481.814002 732.905202 481.809909 732.957391 481.809909 733.00958z"  ></path></symbol>' +
                  '</svg>',
                  onclick: () => {
                    this.getTaskStatesByDuration(0)
                  },
                },
                myshowOneWeek: {
                  show: true,
                  title: '一周(默认)',
                  icon: '<svg>' +
                  '<symbol id="icon-day07" viewBox="0 0 1024 1024">' +
                  '<path d="M421.072593 507.547595c0.146333 0 0.289596-0.008186 0.434905-0.011256l122.408911 0-95.504144 214.338646 0.10847 0.069585c-1.680269 3.62762-2.62478 7.66661-2.62478 11.927657 0 15.697517 12.724813 28.420283 28.421306 28.420283 10.42749 0 19.539009-5.617951 24.483624-13.990642l0.004093 0.00614 0.032746-0.069585c0.916882-1.562589 1.689479-3.219321 2.298346-4.956895l125.649721-270.882454 0.033769-0.069585c0.911766-1.529843 1.444908-3.309372 1.444908-5.217838 0-5.64865-4.583388-10.226922-10.240225-10.229992l0 0L421.665087 456.881658c-0.197498-0.004093-0.393973-0.01535-0.592494-0.01535-13.994736 0-25.340131 11.346419-25.340131 25.341155S407.078881 507.547595 421.072593 507.547595z"  ></path>' +
                  '<path d="M693.570847 279.753495c26.999934 0 48.88743-21.554922 48.88743-48.131207l0-50.406017c0-26.576285-21.88852-48.109718-48.88743-48.109718-27.018354 0-48.925293 21.533432-48.925293 48.109718l0 50.406017C644.646578 258.198573 666.552493 279.753495 693.570847 279.753495z"  ></path>' +
                  '<path d="M327.746044 279.753495c27.018354 0 48.907896-21.554922 48.907896-48.131207l0-50.406017c0-26.576285-21.889543-48.109718-48.907896-48.109718-26.998911 0-48.904827 21.533432-48.904827 48.109718l0 50.406017C278.841218 258.198573 300.747133 279.753495 327.746044 279.753495z"  ></path>' +
                  '<path d="M854.35374 265.833461c0-38.809911-22.189372-56.839543-57.190537-56.839543l-28.304649-2.574638 0 24.445762c0 40.500413-33.377178 73.317843-74.513064 73.317843-41.166585 0-74.531484-32.81743-74.531484-73.317843l0-24.445762L403.055241 206.41928l0 24.445762c0 40.500413-33.380248 73.317843-74.514087 73.317843-41.167608 0-74.53046-32.81743-74.53046-73.317843l0-24.445762-27.812439 2.574638c-27.438932 0-57.204863 29.839609-57.204863 56.839543 0 0 0 451.081559 0 549.298488 0 45.409213 36.9741 75.760474 71.045079 75.760474 51.232848 0 450.361151-0.014326 538.057469-0.014326 38.931684 0 76.910671-27.267017 76.910671-70.838372C855.005586 691.809225 854.35374 265.833461 854.35374 265.833461zM818.523697 782.317589c0 50.593282-15.544021 70.685899-59.498092 70.685899-114.238834 0-380.15109 0-494.705102 0-36.868699 0-57.173141-19.296485-57.173141-56.839543 0-125.126812-1.954515-428.66399-1.954515-428.66399l613.595886 0C818.788733 367.499955 818.523697 656.972812 818.523697 782.317589z"  ></path>' +
                  '</symbol>' +
                  '</svg>',
                  onclick: () => {
                    this.getTaskStatesByDuration(7)
                  },
                },
                myshowOneMonth: {
                  show: true,
                  title: '一个月',
                  icon: '<svg>' +
                  '<symbol id="icon-day31" viewBox="0 0 1024 1024">' +
                  '<path d="M598.469885 733.720777c0 0.039909 0.00307 0.079818 0.00307 0.119727l0 0.341784 0.00921 0c0.24764 16.458857 13.658068 29.726022 30.175253 29.726022 16.517185 0 29.927613-13.267165 30.175253-29.726022l0.01535 0L658.848021 487.37823l-0.00614 0c0.001023-0.033769 0.00307-0.066515 0.00307-0.101307 0-16.671705-13.515828-30.187533-30.187533-30.187533-16.672728 0-30.187533 13.515828-30.187533 30.187533 0 0.039909 0.00307 0.078795 0.00307 0.118704l0 246.207471C598.472955 733.643006 598.469885 733.680868 598.469885 733.720777z" fill="#1296db" ></path>' +
                  '<path d="M423.383218 704.556551c-9.240455 7.695263-21.784142 11.598152-37.282115 11.598152-17.733896 0-36.094056-3.795443-54.796-11.308557-0.106424-0.041956-0.200568-0.060375-0.299829-0.090051-2.951215-1.165546-6.164397-1.814322-9.531074-1.814322-14.32731 0-25.940812 11.612479-25.940812 25.940812 0 10.637268 6.404873 19.774369 15.566534 23.777543 0.013303 0.014326 0.020466 0.027629 0.044002 0.037862 24.072255 10.044774 49.308009 15.133675 75.068719 15.133675 32.072463 0 59.07342-8.93551 80.252789-26.559912 21.456684-17.859763 32.335453-40.792055 32.335453-68.159356 0-11.036357-1.882883-21.644973-5.596462-31.532157-3.737114-9.945513-9.085936-18.570961-15.897062-25.640983-5.046946-5.230118-12.19474-9.872858-21.325701-13.858636 11.33107-6.611581 20.058848-14.248516 26.02063-22.790052 7.751544-11.104919 11.682064-24.855084 11.682064-40.869826 0-26.351158-10.044774-47.451732-29.854958-62.717414-19.408025-14.953573-46.051849-22.536272-79.19162-22.536272-24.562419 0-47.589878 4.468778-68.443835 13.282514l-3.124154 1.321088 0.025583 0.094144c-8.951883 3.415796-15.312754 12.07706-15.312754 22.230304 0 13.140275 10.651594 23.790846 23.791869 23.790846 4.212952 0 8.167007-1.099031 11.599176-3.019777 0.291642 0.038886 0.573051 0.020466 0.840134-0.073678 16.120143-5.650697 31.099299-8.506744 44.674479-8.506744 16.786315 0 30.43415 3.821025 40.564881 11.356652 9.801227 7.291057 14.56574 16.477276 14.56574 28.080545 0 12.94073-4.868891 22.500457-14.883989 29.224602-9.110495 6.118348-22.211884 9.621125-39.020712 10.451026-0.041956 0.002047-0.076748 0.016373-0.11461 0.025583-12.95301 1.136893-23.113417 12.003382-23.113417 25.25315 0 13.580297 10.676154 24.666796 24.093744 25.326828 18.629289 2.222621 26.627451 4.187369 30.039153 5.500271 5.371334 2.078335 10.351766 5.374404 14.803147 9.795087 7.580652 7.882528 11.266601 16.817014 11.266601 27.309996C436.89086 687.190021 432.472224 696.986131 423.383218 704.556551z" fill="#1296db" ></path>' +
                  '<path d="M854.35374 265.834484c0-38.810934-22.189372-56.840566-57.190537-56.840566l-28.304649-2.574638 0 24.445762c0 40.500413-33.377178 73.317843-74.513064 73.317843-41.166585 0-74.531484-32.81743-74.531484-73.317843l0-24.445762L403.055241 206.41928l0 24.445762c0 40.500413-33.380248 73.317843-74.514087 73.317843-41.167608 0-74.53046-32.81743-74.53046-73.317843l0-24.445762-27.812439 2.574638c-27.438932 0-57.204863 29.839609-57.204863 56.840566 0 0 0 451.080535 0 549.297464 0 45.409213 36.9741 75.760474 71.045079 75.760474 51.232848 0 450.361151-0.014326 538.057469-0.014326 38.931684 0 76.910671-27.267017 76.910671-70.838372C855.005586 691.809225 854.35374 265.834484 854.35374 265.834484zM818.523697 782.317589c0 50.593282-15.544021 70.685899-59.498092 70.685899-114.238834 0-380.15109 0-494.705102 0-36.868699 0-57.173141-19.296485-57.173141-56.839543 0-125.126812-1.954515-428.66399-1.954515-428.66399l613.595886 0C818.788733 367.499955 818.523697 656.972812 818.523697 782.317589z" fill="#1296db" ></path>' +
                  '<path d="M693.570847 279.753495c26.999934 0 48.88743-21.554922 48.88743-48.131207l0-50.406017c0-26.576285-21.88852-48.109718-48.88743-48.109718-27.018354 0-48.925293 21.533432-48.925293 48.109718l0 50.406017C644.646578 258.198573 666.552493 279.753495 693.570847 279.753495z" fill="#1296db" ></path><path d="M327.746044 279.753495c27.018354 0 48.907896-21.554922 48.907896-48.131207l0-50.406017c0-26.576285-21.889543-48.109718-48.907896-48.109718-26.998911 0-48.904827 21.533432-48.904827 48.109718l0 50.406017C278.841218 258.198573 300.747133 279.753495 327.746044 279.753495z" fill="#1296db" ></path>' +
                  '</symbol>' +
                  '</svg>',
                  onclick: () => {
                    this.getTaskStatesByDuration(30)
                  },
                },
                myshowAll: {
                  show: true,
                  title: '所有数据',
                  icon: '<svg>' +
                  '<symbol id="icon-A" viewBox="0 0 1024 1024">' +
                  '<path d="M645.287167 940.200432l-84.270288-99.395778H237.879294c-97.246835 0-176.369893-73.076342-176.369893-162.891927V245.700935c0-89.796142 79.122035-162.854065 176.369893-162.854065H785.073864c97.236602 0 176.349427 73.057923 176.349427 162.854065v432.212815c0 89.815585-79.112826 162.891927-176.349427 162.891928h-61.661362v-40.000016h61.661362c75.1864 0 136.348388-55.127552 136.348388-122.891912V245.700935c0-67.744917-61.163011-122.853026-136.348388-122.853026H237.879294c-75.195609 0-136.368854 55.108109-136.368854 122.853026v432.212815c0 67.76436 61.173245 122.891911 136.368854 122.891912H579.553047l96.241948 113.535822-30.507828 25.858948z"  ></path>' +
                  '<path d="M583.439564 564.863998H438.975335L401.738245 669.583015l-50.254567-0.067538 135.186935-359.506911h55.079456l130.177852 359.506911-52.764738-0.108471-35.723619-104.543008z m-129.874953-43.055608h112.158453L512.619612 363.358635l-59.055001 158.449755z"  ></path>' +
                  '</symbol>' +
                  '</svg>',
                  onclick: () => {
                    this.getTaskStatesByDuration('all');
                  },
                },
              },
              right: 43,
            },
            series: [
              {
                name: '成功',
                type: 'bar',
                stack: '总数',
                label: {
                  normal: {
                    show: false,
                    position: 'inside'
                  }
                },
                data: this.taskStateSummary.success
              },
              {
                name: '执行中',
                type: 'bar',
                stack: '总数',
                label: {
                  normal: {
                    show: false,
                    position: 'inside'
                  }
                },
                data: this.taskStateSummary.running
              },

              {
                name: '失败',
                type: 'bar',
                stack: '总数',
                label: {
                  normal: {
                    show: false,
                    position: 'inside'
                  }
                },
                data: this.taskStateSummary.failed
              },
              {
                name: '未知',
                type: 'bar',
                stack: '总数',
                label: {
                  normal: {
                    show: false,
                    position: 'inside'
                  }
                },
                data: this.taskStateSummary.unknown
              },
            ]
          });
        // }else{
        //   this.isTaskStateDataNull = true;
        // }
        window.onresize = this.chartTaskStateSummary.resize;
      },
      getSummaries() {
        let params = {};
        if (this.state_time_start === 0 && this.state_time_end === 0) {
          params = {
            user: this.sysUserName,
          };
        } else {
          params = {
            user: this.sysUserName,
            state_time_start: this.state_time_start,
            // state_time_end: this.state_time_end
          };
        }
        reqGetSummaries(params).then(res => {
          // console.log(res.data.users);
          this.sumaries.task_num = res.data.tasks.total;
          this.sumaries.user_num = res.data.users.total;
          this.sumaries.group_num = res.data.groups.total;
          this.sumaries.worker_num = res.data.workers.total;
          if (res.data.tasks.backup != null) {
            this.chartBackupSummaryFunc(res.data.tasks.backup);
          }
          if (res.data.tasks.recover != null) {
            this.chartRecoverySummaryFunc(res.data.tasks.recover);
          }
          if (res.data.workers != null) {
            this.chartWorkerSummaryFunc(res.data.workers);
          }
          if (res.data.backupstates != null) {
            this.sumaries.taskstate_num = res.data.backupstates.total;
            this.chartTaskStateSummaryFunc(res.data.backupstates);
          }
        }, err => {
          if (err.response.status == 401) {
            this.$message({
              message: "请重新登陆",
              type: 'error'
            });
            sessionStorage.removeItem('access-user');
            this.$router.push({path: '/'});
          } else {
            this.$message({
              message: "请求异常",
              type: 'error'
            });
          }
        });
      },
      getTaskStatesByDuration: function (duration) {
        this.chartTaskStateSummary.dispatchAction({
          type: 'restore'
        });
        if(duration === 'all'){
          this.state_time_start = 0;
          this.state_time_end = 0;
        }else {
          let now = new Date();
          let start = now.getFullYear() + "-" + (now.getMonth() + 1) + "-" + (now.getDate()) + ' 00:00:00';
          // let end = now.getFullYear()+"-"+(now.getMonth()+1)+"-"+(now.getDate()) + ' 23:59:59';
          this.state_time_start = Date.parse(new Date(start)) / 1000 - duration * 24 * 3600;
        }
        this.getSummaries();
      },
      getOplogList: function () {
        let para = {
          user: this.sysUserName,
          limit: 10,
          offset: 0,
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
            this.$router.push({path: '/login'});
          } else {
            this.$message({
              message: "获取数据失败",
              type: 'error'
            });
          }
        })
      },
    },
    beforeDestroy() {
      clearInterval(this.intervalTask)
    },
    mounted() {
      var accessInfo = sessionStorage.getItem('access-user');
      if (accessInfo) {
        accessInfo = JSON.parse(accessInfo);
        this.sysUserName = accessInfo.username;
        this.role = accessInfo.role;
        //this.getRoles(this.sysUserName);
        //this.getGroups(this.sysUserName);
      } else {
        this.$router.push('/login');
      }
      this.chartBackupSummary = echarts.init(document.getElementById('chartBackupSummary'));
      this.chartRecoverySummary = echarts.init(document.getElementById('chartRecoverySummary'));
      this.chartWorkerSummary = echarts.init(document.getElementById('chartWorkerSummary'));
      this.chartTaskStateSummary = echarts.init(document.getElementById('chartTaskStateSummary'));
      this.getTaskStatesByDuration(7);
      this.getOplogList();
      this.intervalTask = setInterval(() => {
        this.getSummaries();
        this.getOplogList();
      }, 30000);
    }
  }

</script>
