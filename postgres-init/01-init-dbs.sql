-- 1. 创建两个物理隔离的数据库
CREATE DATABASE casdoor;
-- 2. 切换到 fyzj 库激活向量插件
\c fyzj
CREATE EXTENSION IF NOT EXISTS vector;
