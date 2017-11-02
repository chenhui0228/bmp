/**
 * Created by 01107267 on 2017/10/31.
 */
import Mock from 'mockjs'
const LoginUsers = []

LoginUsers.push(Mock.mock({
  id: Mock.Random.guid(),
  name: 'test',
  password: '123456',
  role: 0,
  group: 0,
  created_at: Mock.Random.datetime('T')
}))

const Users = []
for (let i = 0; i < 16; i++) {
  Users.push(Mock.mock({
    id: Mock.Random.guid(),
    name: Mock.Random.word(),
    password: '123456',
    role: Mock.Random.integer(1,4),
    group: Mock.Random.integer(1,5),
    created_at: Mock.Random.datetime('T')
  }))
}

export {LoginUsers, Users}
