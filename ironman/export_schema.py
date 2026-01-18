#!/usr/bin/env python3
"""
导出数据库schema到SQL文件
用于创建GitHub项目的数据库初始化脚本

使用方法：
1. 将此文件保存为 export_schema.py
2. 放到 G:\ironman\ 目录
3. 运行: python export_schema.py
4. 复制生成的 schema_ironman.sql 和 schema_irongroup.sql 内容给Claude
"""

import sqlite3
import os

def export_schema(db_path, output_file):
    """导出数据库schema"""
    if not os.path.exists(db_path):
        print(f"❌ 错误：数据库文件不存在 {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 获取所有表名
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"-- Database Schema: {os.path.basename(db_path)}\n")
            f.write(f"-- Tables: {len(tables)}\n\n")
            
            for table in tables:
                # 获取建表语句
                cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (table,))
                create_sql = cursor.fetchone()[0]
                
                f.write(f"-- Table: {table}\n")
                f.write(create_sql + ";\n\n")
        
        conn.close()
        print(f"✓ Schema导出成功: {output_file}")
        print(f"  包含 {len(tables)} 个表: {', '.join(tables)}")
        return True
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("="*60)
    print("数据库Schema导出工具")
    print("="*60)
    
    # 导出ironman数据库
    print("\n[1/2] 导出ironman.db...")
    ironman_success = export_schema(
        'G:/ironman/ironman.db',
        'G:/ironman/schema_ironman.sql'
    )
    
    # 导出irongroup数据库  
    print("\n[2/2] 导出irongroup.db...")
    irongroup_success = export_schema(
        'G:/irongroup/irongroup.db',
        'G:/irongroup/schema_irongroup.sql'
    )
    
    print("\n" + "="*60)
    if ironman_success and irongroup_success:
        print("✓ 所有schema导出完成！")
        print("\n导出文件：")
        print("  - G:/ironman/schema_ironman.sql")
        print("  - G:/irongroup/schema_irongroup.sql")
        print("\n【下一步】请将这两个SQL文件的内容复制给Claude")
        print("="*60)
    else:
        print("⚠️  部分导出失败，请检查数据库路径。")
        print("="*60)

if __name__ == '__main__':
    main()
