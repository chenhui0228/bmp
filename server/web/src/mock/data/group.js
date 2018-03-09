/**
 * Create by 01369634 on 2017/11/1
 */
import Mock from 'mockjs'

const Groups = []
for (let i = 0; i < 20; i++) {
  Groups.push(Mock.mock({
    id: Mock.Random.guid(),
    groupName: Mock.Random.cname(),
    description: Mock.Random.csentence(5,10),
    role: Mock.Random.cword(3)
  }))
}

export {Groups}
