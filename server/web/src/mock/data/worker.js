/**
 * Create by 01369634 on 2017/11/3
 */

import Mock from 'mockjs'

const Workers = []
for (let i = 0; i < 20; i++) {
  Workers.push(Mock.mock({
    id: Mock.Random.guid(),
    workername: Mock.Random.name(),
    ip: Mock.Random.ip(),
    workertype: Mock.Random.integer(1,4),
    user: Mock.Random.name(),
    description: Mock.Random.csentence(5,10),
  }))
}

export {Workers}
