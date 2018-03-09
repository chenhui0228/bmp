require('./check-versions')()

process.env.NODE_ENV = 'production'

//实现node.js 命令行环境的 loading效果， 和显示各种状态的图标等
var ora = require('ora')
//rimraf 删除输出目录 类似于linux中的rm -rf命令
var rm = require('rimraf')
//clean-webpack-plugin
//处理文件路径
var path = require('path')
//颜色插件
var chalk = require('chalk')
var webpack = require('webpack')
var config = require('../config')
var webpackConfig = require('./webpack.prod.conf')

var spinner = ora('building for production...')
spinner.start()

rm(path.join(config.build.assetsRoot, config.build.assetsSubDirectory), err => {
  if (err) throw err
  webpack(webpackConfig, function (err, stats) {
    spinner.stop()
    if (err) throw err
    process.stdout.write(stats.toString({
      colors: true,
      modules: false,
      children: false,
      chunks: false,
      chunkModules: false
    }) + '\n\n')

    console.log(chalk.cyan('  Build complete.\n'))
    console.log(chalk.yellow(
      '  Tip: built files are meant to be served over an HTTP server.\n' +
      '  Opening index.html over file:// won\'t work.\n'
    ))
  })
})
