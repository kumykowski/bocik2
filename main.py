import os
import json
import sys
import logging
import time

# Upewnij się, że w tym samym folderze masz plik instaling_client.py
from instaling_client import InstalingClient

logging.basicConfig(
    filename='main_debug.log',
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)

def load_accounts(file_path='accounts.json'):
    """Wczytuje dane kont z pliku JSON."""
    if not os.path.exists(file_path):
        logging.error(f"Plik z kontami '{file_path}' nie istnieje.")
        print(f"Plik z danymi kont '{file_path}' nie istnieje.")
        sys.exit(1)
    
    with open(file_path, 'r', encoding='utf-8') as f:
        try:
            accounts = json.load(f)
            logging.info(f"Wczytano {len(accounts)} konto/kont(a) z '{file_path}'.")
            return accounts
        except json.JSONDecodeError:
            logging.error("Plik accounts.json nie jest poprawnym JSON-em.")
            print("Błąd: Plik z danymi kont nie jest poprawnym plikiem JSON.")
            sys.exit(1)

def load_solved_words(file_path='solved_words.json'):
    """Wczytuje wcześniej rozwiązane słówka z pliku JSON."""
    if not os.path.exists(file_path):
        logging.info(f"Plik '{file_path}' nie istnieje. Zaczynamy od pustej listy.")
        return []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            logging.info(f"Wczytano {len(data)} rozwiązanych słówek z '{file_path}'.")
            return data
    except (json.JSONDecodeError, OSError):
        logging.error(f"Plik '{file_path}' jest niepoprawny. Zwracam pustą listę.")
        return []

def save_solved_words(solved_words, file_path='solved_words.json'):
    """
    Zapisuje rozwiązane słówka wprost do pliku JSON (bez plików tymczasowych).
    """
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(solved_words, f, ensure_ascii=False, indent=4)
        logging.info(f"Zapisano {len(solved_words)} słówek do '{file_path}'.")
        print(f"Zapisano {len(solved_words)} rozwiązanych słówek do pliku '{file_path}'.")
    except Exception as e:
        logging.error(f"Nie udało się zapisać słówek do '{file_path}': {e}")
        print(f"Błąd przy zapisie do '{file_path}': {e}")

def save_session_result(email, workdays, file_path='session_results.json'):
    """Zapisuje wynik sesji (workdays) do pliku JSON."""
    session_result = {
        'email': email,
        'workdays': workdays,
        'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
    }
    # Ładujemy dotychczasowe wyniki
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                results = json.load(f)
        except (json.JSONDecodeError, OSError):
            results = []
    else:
        results = []
    
    results.append(session_result)
    # Zapisujemy zaktualizowaną listę
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=4)
        logging.info(f"Zapisano wynik sesji dla '{email}' do '{file_path}'.")
        print(f"Zapisano wynik sesji dla '{email}' do pliku '{file_path}'.")
    except Exception as e:
        logging.error(f"Nie udało się zapisać wyniku sesji dla '{email}': {e}")
        print(f"Błąd przy zapisie wyniku sesji dla '{email}': {e}")

def process_account(account):
    email = account.get('email')
    password = account.get('password')

    if not email or not password:
        logging.warning("Brakuje emaila lub hasła. Pomijam konto.")
        print("Ostrzeżenie: Brak emaila lub hasła dla jednego z kont. Pomijam...")
        return

    chance = 20
    min_delay = 1
    max_delay = 1
    client = InstalingClient(chance=chance, min_delay=min_delay, max_delay=max_delay)

    try:
        client.login(email=email, password=password)
        print(f"Zalogowano pomyślnie jako '{email}'.")

        # ─────────────────────────────────────────────────
        # Nowość: jeśli sesja ukończona -> pomijamy solve_quiz()
        if client.session_completed:
            print(f"Dzisiejsza sesja dla '{email}' jest już wykonana. Pomijam solve_quiz().")
            workdays = None
        else:
            workdays = client.solve_quiz()
            print(f"Liczba dni pracy w tym tygodniu dla '{email}': {workdays}")
        # ─────────────────────────────────────────────────

        new_words = client.solved_words
        if new_words:
            current_solved = load_solved_words('solved_words.json')
            existing_ids = {str(item['word_id']) for item in current_solved}
            added_count = 0

            for w in new_words:
                wid = str(w['word_id'])
                if wid not in existing_ids:
                    current_solved.append(w)
                    existing_ids.add(wid)
                    added_count += 1

            print(f"Dodano {added_count} nowych słówek do solved_words.json.")
            save_solved_words(current_solved, 'solved_words.json')
        else:
            print(f"Brak nowych słówek do zapisania dla '{email}'.")

        save_session_result(email, workdays, 'session_results.json')

    except Exception as e:
        logging.error(f"Błąd przy procesowaniu konta '{email}': {e}")
        print(f"Błąd (konto: {email}): {e}")
        
def main():
    accounts = load_accounts('accounts.json')

    # Sekwencyjnie przechodzimy przez każde konto
    for acc in accounts:
        process_account(acc)

if __name__ == "__main__":
    main()
    print("Koniec programu - wychodzę.")
    sys.exit(0)
