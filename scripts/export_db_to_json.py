import sqlite3
import json
import os

# Database path
DB_PATH = "ai_learning.db"
OUTPUT_FILE = "data/debug_db_dump.json"

def export_db_to_json():
    if not os.path.exists(DB_PATH):
        print(f"Error: Database file '{DB_PATH}' not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row # Access columns by name
    cursor = conn.cursor()

    try:
        # 1. Fetch Courses
        cursor.execute("SELECT * FROM course")
        courses = [dict(row) for row in cursor.fetchall()]

        for course in courses:
            course_id = course["id"]
            
            # 2. Fetch Chapters for each Course
            cursor.execute('SELECT * FROM chapter WHERE course_id = ? ORDER BY "index"', (course_id,))
            chapters = [dict(row) for row in cursor.fetchall()]
            
            for chapter in chapters:
                chapter_id = chapter["id"]
                
                # 3. Fetch Quizzes for each Chapter
                cursor.execute("SELECT * FROM quiz WHERE chapter_id = ?", (chapter_id,))
                quizzes = [dict(row) for row in cursor.fetchall()]
                
                for quiz in quizzes:
                    quiz_id = quiz["id"]
                    
                    # 4. Fetch Questions for each Quiz
                    cursor.execute("SELECT * FROM question WHERE quiz_id = ?", (quiz_id,))
                    questions = [dict(row) for row in cursor.fetchall()]
                    
                    # Parse options_json if it exists
                    for q in questions:
                        if q.get("options_json"):
                            try:
                                q["options"] = json.loads(q["options_json"])
                            except:
                                q["options"] = q["options_json"] # Keep as string if fail
                        # Remove raw json string to be cleaner
                        # q.pop("options_json", None) 
                    
                    quiz["questions"] = questions
                
                chapter["quizzes"] = quizzes
            
            course["chapters"] = chapters

        # Write to JSON file
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(courses, f, ensure_ascii=False, indent=2)

        print(f"Successfully exported database to '{OUTPUT_FILE}'.")

    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    export_db_to_json()
