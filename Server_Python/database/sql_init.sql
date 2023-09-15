--用户表
CREATE TABLE t_user (
  id INTEGER PRIMARY KEY,
  username TEXT NOT NULL, -- 用户名
  password TEXT NOT NULL, -- 密码
  email TEXT, -- 邮箱
  phone TEXT, -- 邮箱
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- 创建时间
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP -- 更新时间
);

PRAGMA table_info('user');

--token_connection 表，每个连接都会分配一个 token_connection，每个用户最多分配1个token_connection
--独立建表是为了以后能多端登录
--CREATE TABLE t_user_token(
--  id INTEGER PRIMARY KEY AUTOINCREMENT,
--  user_id INTEGER NOT NULL, --已登录用户的 ID: 表示，与 users 表中的 id 字段相对应。
--  token_connection TEXT NOT NULL, --表示用户所使用的 token_connection。
--  expiration DATETIME NOT NULL, --表示 token_connection 的有效期限。在插入记录时，可以通过使用 DATETIME('now', '+1 hour') 来将其设置为当前时间加上一个小时。
--  FOREIGN KEY (user_id) REFERENCES t_users(id) ON DELETE CASCADE --user_id 字段的外键约束可以确保该值与 users 表中的有效 ID 相匹配。ON DELETE CASCADE 参数将确保当用户从 users 表中删除时，也将从 user_token_connection 表中删除相应的映射。
--);

--每次登录，都会 分配一个 user_token_connection，为期一小时
--insert into t_user_token_connection(id, connect_id, user_id, token_connection, expiration)
--values(.next, token_connectionid, userid, token_connection, expiration)

--某连接每次发送聊天消息(无论针对于多 tab 聊天中的哪个 tab)都会 重置 token_connection 有效期 为一小时
--UPDATE t_user_token_connection SET expiration = DATETIME('now', '+1 hour') WHERE token_connection = 'your_token_connection_value';

--token_connection过期，用户登出时，清理该用户的 token_connection
--DELETE FROM t_user_token_connection WHERE expiration <= datetime('now');

--登录限制逻辑
--1. 在建立连接之前，先查询该用户是否已经存在两个有效的连接，如果存在两个有效的连接，则需要删除近期最不活跃的那个连接。
--具体做法为： 
--select id from t_user_token_connection where user_id = :用户id order by expiration; --查询该用户的所有连接，并按照有效期从小到大排序。
--DELETE FROM t_user_token_connection WHERE user_id = :用户id AND expiration <= datetime('now');-- 删除该用户有效期最小的连接，释放该连接的 token_connection。
--Insert --建立新的连接，生成新的 token_connection 并将该连接信息插入到连接表中。

-- 每个 userid, 最多可以有三个 chat_id, 用来标记三个独立的对话
--CREATE TABLE t_user_chatid(
--  id INTEGER PRIMARY KEY AUTOINCREMENT,
--  user_id INTEGER NOT NULL, --已登录用户的 ID: 表示，与 users 表中的 id 字段相对应。
--  chat_id TEXT NOT NULL, --聊天tab的 ID
--  FOREIGN KEY (user_id) REFERENCES t_users(id) ON DELETE CASCADE --user_id 字段的外键约束可以确保该值与 users 表中的有效 ID 相匹配。ON DELETE CASCADE 参数将确保当用户从 users 表中删除时，也将从 user_token_connection 表中删除相应的映射。
--);

