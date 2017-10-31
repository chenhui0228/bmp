//about.vue
<style type="text/css" scoped>
    .common-view {
        min-width: 320px;
        /*margin: 0.3rem 6rem;*/
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
    <div class="common-view" >
        <div class="func-row row" >
            <div class="col-xs-12">
                这是一个任务
            </div>
        </div>

    </div>
</template>
<script>
export default {
    data() {

        return {
        }
    },
    created() {

    },
    watch: {
        // 如果路由有变化，会再次执行该方法

    },
    beforeDestroy() {
        clearInterval(this.intervalTask)
    },
    methods: {

    }
}


</script>
