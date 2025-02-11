import requests
from bs4 import BeautifulSoup
import time
import random
from urllib.parse import urlparse, parse_qs
import re
import string
import json
import logging

logging.basicConfig(
    filename='instaling_client_debug.log',
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)

class InstalingClient:
    def __init__(self, chance=20, min_delay=1, max_delay=1):
        self.base_url = "https://instaling.pl"
        self.session = requests.Session()
        self.student_id = None
        self.session_completed = False
        self.chance = min(chance, 25)
        self.solved_words = []
        self.min_delay = min_delay
        self.max_delay = max_delay
        logging.info(f"[Init] chance={self.chance}, delay=[{self.min_delay},{self.max_delay}]")

    def login(self, email, password):
        login_url = f"{self.base_url}/teacher.php?page=teacherActions"
        data = {'action': 'login','from':'','log_email':email,'log_password':password}
        resp = self.session.post(login_url, data=data)
        resp.raise_for_status()

        parsed = urlparse(resp.url)
        query = parse_qs(parsed.query)
        if "student_id" in query:
            self.student_id = query["student_id"][0]
            logging.info(f"Zalogowano student_id={self.student_id}")
        else:
            raise ValueError("Nieprawidłowe dane logowania")

        soup = BeautifulSoup(resp.text, 'html.parser')
        sc = soup.find('h4', string='Dzisiejsza sesja wykonana')
        self.session_completed = bool(sc)

    def initiate_session(self):
        if not self.student_id:
            raise ValueError("Brak student_id. Zaloguj się najpierw.")

        url = f"{self.base_url}/ling2/server/actions/init_session.php"
        data = {'child_id':self.student_id,'repeat':'','start':'','end':''}
        r = self.session.post(url, data=data)
        r.raise_for_status()

    def solve_quiz(self):
        """Pętla: generowanie kolejnych słówek i wysyłanie odpowiedzi."""
        self.initiate_session()
        to_repeat = self.get_words_to_repeat()

        misspell_count = 0
        while True:
            delay = random.uniform(self.min_delay, self.max_delay)
            print(f"Czekam {delay:.2f}s...")
            time.sleep(delay)

            url = f"{self.base_url}/ling2/server/actions/generate_next_word.php"
            data = {'child_id':self.student_id,'date':int(time.time()*1000)}
            resp = self.session.post(url, data=data)
            resp.raise_for_status()

            if "Dni pracy w tym tygodniu" in resp.text:
                m = re.search(r"Dni pracy w tym tygodniu:\s*(\d+)", resp.text)
                if m:
                    print("Sesja zakończona.")
                    return m.group(1)
                break

            try:
                wdata = resp.json()
            except:
                continue

            word_id = wdata.get('id')
            pl_translation = self.get_polish_translation(word_id, to_repeat)

            # Losowo robimy błąd
            if misspell_count < 3 and random.randint(1, 100) > self.chance:
                wrong = self.misspell_word(pl_translation)
                res = self.save_answer(word_id, wrong)
                misspell_count += 1
                print(f"(BŁĄD) ID={word_id} => {wrong}")
            else:
                res = self.save_answer(word_id, pl_translation)
                print(f"(OK) ID={word_id} => {pl_translation}")

                if res:
                    grade = res.get('grade')
                    if grade == 1:
                        self.solved_words.append({'word_id':word_id,'word':pl_translation})

        return None

    def misspell_word(self, word):
        if len(word)<2: return word
        choice = random.randint(0,2)
        if choice==0:
            pos = random.randint(0,len(word)-1)
            return word[:pos]+word[pos+1:]
        elif choice==1:
            return word + random.choice(string.ascii_lowercase)
        else:
            if len(word)<3:
                return word
            pos = random.randint(0,len(word)-2)
            return word[:pos] + word[pos+1]+ word[pos]+ word[pos+2:]

    def get_words_to_repeat(self, group_id=0, limit=300):
        if not self.student_id:
            raise ValueError("Brak student_id. Zaloguj się najpierw.")

        url = f"{self.base_url}/learning/repeat_words_ajax.php"
        params = {"action":"getWordsToRepeat","student_id":self.student_id,"group_id":group_id,"limit":limit}
        r = self.session.get(url, params=params)
        r.raise_for_status()
        return r.json()

    def get_polish_translation(self, word_id, words_to_repeat):
        wid = str(word_id)
        for w in words_to_repeat:
            if str(w.get('word_id')) == wid:
                return w.get('word')
        return "Default Polish Translation"

    def save_answer(self, word_id, polish_translation):
        url = f"{self.base_url}/ling2/server/actions/save_answer.php"
        data = {'child_id':self.student_id,'word_id':word_id,'answer':polish_translation}
        try:
            resp = self.session.post(url, data=data)
            resp.raise_for_status()
            return resp.json()
        except:
            return None
