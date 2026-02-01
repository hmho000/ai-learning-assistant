
import sys
import os
from pathlib import Path

# 添加项目根目录到 sys.path
sys.path.append(os.getcwd())

from fastapi.testclient import TestClient
from backend.app import app
from backend.database import get_user_db_path, BASE_DIR
import shutil

# 清理测试数据
def cleanup(user_ids):
    for uid in user_ids:
        path = get_user_db_path(uid).parent
        if path.exists():
            shutil.rmtree(path)
            print(f"Cleaned up user {uid} directory: {path}")
    
    # 清理 auth db 中的用户（这也比较麻烦，因为我们没有直接删除用户的接口）
    # 这里我们主要依赖每次运行使用新的用户名，或者手动清理 'data/auth_main.db'
    # 为了简单演示，我们不删除 auth_main.db 中的记录，只验证流程
    pass

def test_auth_flow():
    # 确保 httpx 安装了，否则 TestClient 可能会报错 (FastAPI 新版依赖 httpx)
    try:
        import httpx
    except ImportError:
        print("Installing httpx for TestClient...")
        os.system("pip install httpx")

    with TestClient(app) as client:
        print("=== 开始多用户认证与隔离测试 ===")

        # 1. 注册 用户 A
        username_a = "test_user_a_v1"
        pwd_a = "password_a"
        print(f"\n[Step 1] 注册用户 A: {username_a}")
        
        resp = client.post("/api/auth/register", json={"username": username_a, "password": pwd_a})
        if resp.status_code == 400 and "already registered" in resp.text:
             print("Warning: User A already exists, trying login...")
             resp = client.post("/api/auth/token", data={"username": username_a, "password": pwd_a})
        
        assert resp.status_code == 200, f"Register/Login A failed: {resp.text}"
        token_a = resp.json()["access_token"]
        print("User A Token obtained.")

        # 2. 注册 用户 B
        username_b = "test_user_b_v1"
        pwd_b = "password_b"
        print(f"\n[Step 2] 注册用户 B: {username_b}")
        
        resp = client.post("/api/auth/register", json={"username": username_b, "password": pwd_b})
        if resp.status_code == 400 and "already registered" in resp.text:
             print("Warning: User B already exists, trying login...")
             resp = client.post("/api/auth/token", data={"username": username_b, "password": pwd_b})

        assert resp.status_code == 200, f"Register/Login B failed: {resp.text}"
        token_b = resp.json()["access_token"]
        print("User B Token obtained.")

        # 3. 验证数据库文件隔离
        # 解析 token 获取 user_id (简单做)
        # 也可以通过 API 如果有 me 接口。没有的话直接看目录
        # 我们假设 user_id 是自增的。
        # 检查 data/users 目录下是否有两个文件夹
        users_dir = BASE_DIR / "users"
        subdirs = [d for d in users_dir.iterdir() if d.is_dir()]
        print(f"\n[Step 3] 检查文件系统隔离: {users_dir}")
        print(f"User directories found: {[d.name for d in subdirs]}")
        assert len(subdirs) >= 2, "Should have at least 2 user directories"
        
        # 4. 用户 A 上传/创建一个课程
        # 此时我们没有真实的 PDF，可以尝试上传一个 dummy pdf
        print(f"\n[Step 4] 用户 A 上传文件")
        dummy_pdf_content = b"%PDF-1.4 header"
        files = {'file': ('test_a.pdf', dummy_pdf_content, 'application/pdf')}
        headers_a = {"Authorization": f"Bearer {token_a}"}
        
        resp = client.post("/api/upload", files=files, headers=headers_a)
        assert resp.status_code == 200, f"Upload failed: {resp.text}"
        print("User A upload success.")

        # 验证 User A 能看到课程
        resp = client.get("/api/courses", headers=headers_a)
        courses_a = resp.json()
        print(f"User A courses: {len(courses_a)}")
        assert len(courses_a) >= 1, "User A should see the uploaded course"

        # 5. 验证 用户 B 看不到 A 的课程
        print(f"\n[Step 5] 用户 B 检查列表 (期望为空或不包含 A 的主要课程)")
        headers_b = {"Authorization": f"Bearer {token_b}"}
        resp = client.get("/api/courses", headers=headers_b)
        courses_b = resp.json()
        print(f"User B courses: {len(courses_b)}")

        # 严格来说 B 应该是 0，或者至少不包含 A 的那个
        # 我们可以对比两个列表
        # 如果是新建库，B 应该是 0
        if len(courses_b) == 0:
            print("Success: User B sees no courses.")
        else:
            # 如果 B 之前有数据，确保不包含 A 的刚上传的文件
            titles_b = [c['title'] for c in courses_b]
            assert "test_a" not in titles_b, "User B should NOT see 'test_a'"
            print("Success: User B does not see User A's course.")

        print("\n[SUCCESS] 测试通过：多用户隔离验证成功！")

if __name__ == "__main__":
    test_auth_flow()
