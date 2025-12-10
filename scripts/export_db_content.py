import sqlite3
import os

# Database path
DB_PATH = "ai_learning.db"
OUTPUT_FILE = "data/debug_chapters_dump.txt"

def export_chapters():
    if not os.path.exists(DB_PATH):
        print(f"Error: Database file '{DB_PATH}' not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Query all chapters with their course titles
        query = """
            SELECT course.title, chapter.title, chapter."index", chapter.content_text
            FROM chapter
            JOIN course ON chapter.course_id = course.id
            ORDER BY course.id, chapter."index"
        """
        cursor.execute(query)
        rows = cursor.fetchall()

        if not rows:
            print("No chapters found in the database.")
            return

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            for course_title, chapter_title, chapter_index, content in rows:
                f.write(f"{'='*50}\n")
                f.write(f"Course: {course_title}\n")
                f.write(f"Chapter {chapter_index}: {chapter_title}\n")
                f.write(f"{'='*50}\n\n")
                f.write(f"{content}\n\n")
                f.write(f"{'-'*50}\n\n")

        print(f"Successfully exported {len(rows)} chapters to '{OUTPUT_FILE}'.")

    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)
    export_chapters()
