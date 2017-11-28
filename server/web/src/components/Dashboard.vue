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
    border:1px solid #333744;
    border-radius:4px;overflow:hidden;
    margin: 3px 3px;
    height: 280px;
    /*background-color: #333744*/
  }
  .bar-card-title{
    font-size:16px;
    font-weight:bold;
    font-family: 'Avenir', Helvetica, Arial, sans-serif;
    /*color:#FFFFFF;*/
  }

  .chart-container .el-col .bar-card-item-value{
    font-family: 'Avenir', Helvetica, Arial, sans-serif;
    font-size: 38px;
    font-weight:bold;
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
  .chart-container .el-col .bar-card-info-key{
    color:#36A9CE;
    font-size: 14px;
    text-align: right;
    padding: 15px 0px;
    line-height:100%
  }
  .chart-container .el-col .bar-card-info-value{
    color:#36A9CE;
    font-size: 14px;
    padding: 15px 0px;
    line-height:100%;
    text-align: left;
  }

</style>

<script>
  import echarts from 'echarts'
  import { reqGetTaskList, reqGetVolumeList, reqGetWorkerList, reqGetPolicyList, reqGetGroupList, reqGetSummaries } from '../api/api';
  export default {
    data() {
      return {
          sysUserName: '',
          role: '',
          chartBackupSummary: '',
          chartRecoverySummary: '',
          chartWorkerSummary: '',
          intervalTask: '',
          sumaries: {
            task_num: 0,
            user_num: 0,
            worker_num: 0,
            group_num: 0,
            volume_num: 0
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
          }
      };
    },
    methods: {
      chartBackupSummaryFunc(data){
        this.backupTaskSummary.total = 0;
        if(data.waiting != null){
          this.backupTaskSummary.currWaiting = data.waiting;
          this.backupTaskSummary.total = this.backupTaskSummary.total + this.backupTaskSummary.currWaiting;
        }
        if(data.running_w != null){
          this.backupTaskSummary.currRunning = this.backupTaskSummary.currRunning + data.running_w;
          this.backupTaskSummary.total = this.backupTaskSummary.total + this.backupTaskSummary.currRunning;
        }
        if(data.running_s != null){
          this.backupTaskSummary.currRunning = this.backupTaskSummary.currRunning + data.running_s;
          this.backupTaskSummary.total = this.backupTaskSummary.total + this.backupTaskSummary.currRunning;
        }
        if(data.stopped !=null ){
          this.backupTaskSummary.currStopped = data.stopped;
          this.backupTaskSummary.total = this.backupTaskSummary.total + this.backupTaskSummary.currStopped;
        }
        if(data.end != null){
          this.backupTaskSummary.currEnd = data.end;
          this.backupTaskSummary.total = this.backupTaskSummary.total + this.backupTaskSummary.currEnd;
        }
        this.chartBackupSummary.setOption({
          tooltip : {
            trigger: 'item',
            formatter: "{a} <br/>{b} : {c} ({d}%)"
          },
          legend: {
            orient: 'vertical',
            left: 'left',
            textStyle: {
            },
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
              center: ['60%','65%'],
              data: [
                {value: this.backupTaskSummary.currWaiting, name: '等待中',itemStyle: {normal: {color: '#f7c410'}}},
                {value: this.backupTaskSummary.currRunning, name: '执行中',itemStyle: {normal: {color: 'blue'}}},
                {value: this.backupTaskSummary.currStopped, name: '已停止',itemStyle: {normal: {color: 'red'}}},
                {value: this.backupTaskSummary.currEnd, name: '已完成',itemStyle: {normal: {color: 'green'}}}
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
      },
      chartRecoverySummaryFunc(data){
        this.recoveryTaskSummary.total = 0;
        if(data.waiting != null){
          this.recoveryTaskSummary.currWaiting = data.waiting;
          this.recoveryTaskSummary.total = this.recoveryTaskSummary.total + this.recoveryTaskSummary.currWaiting;
        }
        if(data.running_w != null){
          this.recoveryTaskSummary.currRunning = this.recoveryTaskSummary.currRunning + data.running_w;
          this.recoveryTaskSummary.total = this.recoveryTaskSummary.total + this.recoveryTaskSummary.currRunning;
        }
        if(data.running_s != null){
          this.recoveryTaskSummary.currRunning = this.recoveryTaskSummary.currRunning + data.running_s;
          this.recoveryTaskSummary.total = this.recoveryTaskSummary.total + this.recoveryTaskSummary.currRunning;
        }
        if(data.stopped !=null ){
          this.recoveryTaskSummary.currStopped = data.stopped;
          this.recoveryTaskSummary.total = this.recoveryTaskSummary.total + this.recoveryTaskSummary.currStopped;
        }
        if(data.end != null){
          this.recoveryTaskSummary.currEnd = data.end;
          this.recoveryTaskSummary.total = this.recoveryTaskSummary.total + this.recoveryTaskSummary.currEnd;
        }
        this.chartRecoverySummary.setOption({
          tooltip : {
            trigger: 'item',
            formatter: "{a} <br/>{b} : {c} ({d}%)"
          },
          legend: {
            orient: 'vertical',
            left: 'left',
            textStyle: {
            },
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
              center: ['60%','65%'],
              data: [
                {value: this.recoveryTaskSummary.currWaiting, name: '等待中',itemStyle: {normal: {color: '#f7c410'}}},
                {value: this.recoveryTaskSummary.currRunning, name: '执行中',itemStyle: {normal: {color: 'blue'}}},
                {value: this.recoveryTaskSummary.currStopped, name: '已停止',itemStyle: {normal: {color: 'red'}}},
                {value: this.recoveryTaskSummary.currEnd, name: '已完成',itemStyle: {normal: {color: 'green'}}}
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
      },
      chartWorkerSummaryFunc(data){
        if(data.total != null){
          this.workerSummary.total = data.total;
        }
        if(data.Active != null){
          this.workerSummary.currActive = data.Active;
        }
        if(data.Offline != null){
          this.workerSummary.currOffline = data.Offline;
        }
        this.chartWorkerSummary.setOption({
          tooltip : {
            trigger: 'item',
            formatter: "{a} <br/>{b} : {c} ({d}%)"
          },
          legend: {
            orient: 'vertical',
            left: 'left',
            textStyle: {
            },
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
              center: ['60%','65%'],
              data: [
                {value: this.workerSummary.currActive, name: '在线',itemStyle: {normal: {color: 'green'}}},
                {value: this.workerSummary.currOffline, name: '掉线',itemStyle: {normal: {color: 'red'}}},
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
      },
      getSummaries(){
        let params = {
          user: this.sysUserName,
        };
        reqGetSummaries(params).then(res => {
          this.sumaries.task_num = res.data.tasks.total;
          this.sumaries.worker_num = res.data.workers.total;
          this.sumaries.user_num = res.data.users.total;
          this.sumaries.group_num = res.data.groups.total;
          if(res.data.tasks.backup != null){
            this.chartBackupSummaryFunc(res.data.tasks.backup);
          }
          if(res.data.tasks.recover != null){
            this.chartRecoverySummaryFunc(res.data.tasks.recover);
          }
          if(res.data.workers != null){
            this.chartWorkerSummaryFunc(res.data.workers);
          }
        },err => {
          if (err.response.status == 401) {
            this.$message({
              message: "请重新登陆",
              type: 'error'
            });
            sessionStorage.removeItem('access-user');
            this.$router.push({ path: '/' });
          } else {
            this.$message({
              message: "请求异常",
              type: 'error'
            });
          }
        });
      }
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
      this.getSummaries();
      this.intervalTask = setInterval(() => {
        this.getSummaries();
      },30000);
    }
  }

</script>
