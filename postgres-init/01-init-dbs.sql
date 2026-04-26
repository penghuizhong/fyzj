-- 1. 创建两个物理隔离的数据库
CREATE DATABASE db_business;
CREATE DATABASE db_agent;

-- 2. 切换到 db_agent 库激活向量插件
\c db_agent
CREATE EXTENSION IF NOT EXISTS vector;
