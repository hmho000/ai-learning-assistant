import requests
import time

base_url = "http://127.0.0.1:8000/api"

def test_flow():
    # 1. Upload
    print("Uploading...")
    files = {'file': open('test.pdf', 'rb')}
    resp = requests.post(f"{base_url}/upload", files=files)
    data = resp.json()
    print("Upload response:", data)
    course_id = data['course_id']
    
    # 2. Generate
    print(f"Triggering generation for course {course_id}...")
    resp = requests.post(f"{base_url}/generate/{course_id}")
    print("Generate response:", resp.json())
    
    # 3. Poll for results
    print("Polling for results...")
    for i in range(10):
        time.sleep(2)
        resp = requests.get(f"{base_url}/courses/{course_id}/chapters")
        chapters = resp.json()
        print(f"Attempt {i+1}: Found {len(chapters)} chapters")
        
        if chapters:
            chapter_id = chapters[0]['id']
            resp = requests.get(f"{base_url}/chapters/{chapter_id}/quiz")
            quizzes = resp.json()
            print(f"  Found {len(quizzes)} quizzes for chapter {chapter_id}")
            if quizzes:
                print("  Success! Quiz generated.")
                break

if __name__ == "__main__":
    test_flow()
