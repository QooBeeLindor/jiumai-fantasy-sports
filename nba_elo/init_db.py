# init_db.py
import sqlite3
import os

def init_database():
    """初始化NBA ELO数据库"""
    
    # 数据库文件路径
    db_path = 'nba_elo.db'
    schema_path = '../data/schema_nba_elo.sql'
    
    # 如果数据库已存在，询问是否覆盖
    if os.path.exists(db_path):
        response = input(f'数据库 {db_path} 已存在，是否覆盖？(y/n): ')
        if response.lower() != 'y':
            print('取消操作')
            return
        os.remove(db_path)
        print(f'已删除旧数据库：{db_path}')
    
    # 读取SQL文件
    print(f'读取schema文件：{schema_path}')
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema_sql = f.read()
    
    # 连接数据库并执行SQL
    print(f'创建数据库：{db_path}')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 执行所有SQL语句
        cursor.executescript(schema_sql)
        conn.commit()
        print('✅ 数据库初始化成功！')
        
        # 验证表是否创建
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f'\n已创建的表：')
        for table in tables:
            print(f'  - {table[0]}')
        
        # 验证联赛数据
        cursor.execute("SELECT COUNT(*) FROM leagues;")
        league_count = cursor.fetchone()[0]
        print(f'\n初始化数据：')
        print(f'  - 联赛数量: {league_count}')
        
    except Exception as e:
        print(f'❌ 错误：{e}')
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    init_database()
