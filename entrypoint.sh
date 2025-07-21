#!/bin/bash
set -e

# 将当前目录添加到PYTHONPATH，以便Flask能找到test_platform模块
export PYTHONPATH=$PYTHONPATH:.

# 设置FLASK_APP环境变量，指向新的管理文件
export FLASK_APP=manage.py
MIGRATIONS_DIR="migrations"

# 使用-d参数明确指定迁移目录，消除路径歧义
if [ ! -d "$MIGRATIONS_DIR/versions" ]; then
  echo "Migrations directory not found. Initializing database..."
  flask db init -d $MIGRATIONS_DIR
  flask db migrate -m "Initial database setup" -d $MIGRATIONS_DIR
  flask db upgrade -d $MIGRATIONS_DIR
else
  echo "Migrations directory found. Applying any new migrations..."
  flask db upgrade -d $MIGRATIONS_DIR
fi

# 执行 supervisord，它将根据配置文件启动并管理所有服务
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf 