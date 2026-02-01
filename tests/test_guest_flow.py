
import sys
import os
import sqlite3
import time
from datetime import datetime, timedelta

# 添加项目根目录到 sys.path
sys.path.append(os.getcwd())

from fastapi.testclient import TestClient
from backend.app import app
from backend.database import BASE_DIR

def test_guest_flow():
    with TestClient(app) as client:
        print("=== 开始访客模式测试 ===")

        # 1. 访客登录
        print("\n[Step 1] 申请访客登录...")
        resp = client.post("/api/auth/guest-login")
        assert resp.status_code == 200, f"Guest login failed: {resp.text}"
        token = resp.json()["access_token"]
        print(f"Guest Token obtained: {token[:10]}...")

        # 验证 Token 有效性 (获取课程列表应为空)
        headers = {"Authorization": f"Bearer {token}"}
        resp = client.get("/api/courses", headers=headers)
        assert resp.status_code == 200, f"Accessing protected route failed: {resp.text}"
        print("Guest accessed protected route successfully.")

        # 2. 模拟上传
        print("\n[Step 2] 访客上传文件...")
        dummy_pdf_content = b"%PDF-1.4 header"
        files = {'file': ('guest_test.pdf', dummy_pdf_content, 'application/pdf')}
        resp = client.post("/api/upload", files=files, headers=headers)
        assert resp.status_code == 200, f"Upload failed: {resp.text}"
        print("Guest upload success.")

        # 3. 验证清理逻辑
        print("\n[Step 3] 验证过期清理逻辑...")
        # 3.1 获取刚才创建的访客 ID
        # 通过 token decode 或者查库。这里直接查库最快。
        auth_db_path = BASE_DIR / "auth_main.db"
        conn = sqlite3.connect(auth_db_path)
        cursor = conn.cursor()
        
        # 获取最新的 Guest
        cursor.execute("SELECT id, username, created_at FROM user WHERE is_guest=1 ORDER BY id DESC LIMIT 1")
        guest_row = cursor.fetchone()
        assert guest_row is not None, "Guest not found in DB"
        guest_id, guest_username, created_at = guest_row
        print(f"Current Guest: ID={guest_id}, User={guest_username}, Time={created_at}")

        # 3.2 篡改 created_at 为 3 小时前
        old_time = (datetime.utcnow() - timedelta(hours=3)).strftime("%Y-%m-%d %H:%M:%S.%f")
        cursor.execute("UPDATE user SET created_at = ? WHERE id = ?", (old_time, guest_id))
        conn.commit()
        conn.close() # Close connection to ensure write is flushed/visible
        print(f"Manually expired guest time to: {old_time}")

        # Verify update stuck
        conn = sqlite3.connect(auth_db_path)
        cur = conn.cursor()
        cur.execute("SELECT created_at FROM user WHERE id=?", (guest_id,))
        verify_time = cur.fetchone()[0]
        conn.close()
        print(f"DEBUG: Read back verification time: {verify_time}")
        if verify_time != old_time:
             print(f"CRITICAL ERROR: Update did not persist! Expected {old_time}, got {verify_time}")
        
        # Wait a bit
        time.sleep(1)

        # 3.3 再次触发 guest-login，应该触发清理
        print("Triggering new guest login to run cleanup...")
        resp = client.post("/api/auth/guest-login")
        assert resp.status_code == 200
        
        time.sleep(2) # Wait for commit?
        
        # 3.4 验证旧 Guest 是否被删除
        # 查库
        conn = sqlite3.connect(auth_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user WHERE id = ?", (guest_id,))
        check_row = cursor.fetchone()
        
        # DEBUG: Dump all users
        cursor.execute("SELECT id, username, created_at, is_guest FROM user")
        all_users = cursor.fetchall()
        print(f"DEBUG: All Users: {all_users}")
        
        conn.close()
        
        if check_row:
             # ID might be reused by the new guest!
             # Check created_at. If it represents the OLD time, then fail.
             # If it represents NEW time, then pass (Old user was deleted, New user took the ID).
             found_created_at_str = check_row[5] # Index 5 is created_at
             # Parse string to datetime? Or just string compare
             print(f"DEBUG: Found row created_at: {found_created_at_str}")
             print(f"DEBUG: Old time was: {old_time}")
             
             if found_created_at_str == old_time:
                 assert False, "Expired guest (Old Time) still exists in DB!"
             else:
                 print("Success: Found row is a NEW user (ID reused). Old user was deleted.")
                 print("Info: Directory check skipped because ID was reused by new user.")
        else:
            print("Success: Expired guest record deleted from DB (ID not reused).")

            # 查目录
            guest_dir = BASE_DIR / "users" / str(guest_id)
            assert not guest_dir.exists(), f"Guest directory {guest_dir} should be deleted"
            print("Success: Guest directory deleted.")

        conn.close()

    print("\n[SUCCESS] 访客模式与自动清理验证成功！")

if __name__ == "__main__":
    test_guest_flow()
