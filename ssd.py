import json
import tempfile
import os

data = [
  {"word_id": "1", "word": "abc"},
  {"word_id": "2", "word": "def"},
  {"word_id": "3", "word": "kółko i krzyżyk"}
]

folder = "C:/temp"  # Upewnij się, że istnieje i masz uprawnienia
tmpfile = None
try:
    with tempfile.NamedTemporaryFile('w', encoding='utf-8', dir=folder, delete=False) as f:
        tmpfile = f.name
        print("TMP FILE =", tmpfile)
        json.dump(data, f, ensure_ascii=False, indent=4)
        print("Po json.dump")

except Exception as e:
    print("Exception w zapisie do pliku tymczasowego:", e)

if tmpfile and os.path.exists(tmpfile):
    print("TMP FILE istnieje. Próba rename.")
    final_path = os.path.join(folder, "test_solved_words.json")
    if os.path.exists(final_path):
        print("Usuwam stary", final_path)
        os.remove(final_path)

    os.rename(tmpfile, final_path)
    print("Plik tymczasowy przeniesiony na", final_path)
