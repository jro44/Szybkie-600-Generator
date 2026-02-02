import streamlit as st
import requests
from bs4 import BeautifulSoup
import random
from collections import Counter

# --- KONFIGURACJA SZYBKIE 600 ---
st.set_page_config(
    page_title="Szybkie 600 Smart System",
    page_icon="🚀",
    layout="centered"
)

# --- STYL (NIEBIESKI/CYFROWY) ---
st.markdown("""
    <style>
    .stApp { background-color: #0d1117; color: #c9d1d9; }
    .ball-600 {
        font-size: 20px; font-weight: bold; color: white;
        background: radial-gradient(circle at 30% 30%, #007bff, #004085); /* Niebieski */
        border: 2px solid #339af0;
        border-radius: 50%;
        width: 50px; height: 50px; display: inline-flex;
        justify-content: center; align-items: center;
        margin: 5px; box-shadow: 0 0 15px rgba(0, 123, 255, 0.4);
    }
    .metric-box {
        background-color: #161b22; padding: 12px; border-radius: 8px;
        text-align: center; border: 1px solid #30363d;
        color: #8b949e; margin-bottom: 10px;
    }
    h1 { color: #58a6ff !important; }
    .status-badge {
        font-weight: bold; font-size: 14px;
        padding: 5px 12px; border-radius: 15px;
        display: inline-block; margin-bottom: 10px;
        border: 1px solid;
    }
    </style>
    """, unsafe_allow_html=True)

# --- SCRAPER DANYCH (SZYBKIE 600) ---
@st.cache_data(ttl=180) # Odświeżaj co 3 minuty
def get_live_draws_600():
    url = "https://www.wynikilotto.net.pl/szybkie-600/wyniki/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        parsed_draws = []
        # Szukamy tabeli z wynikami
        rows = soup.find_all('tr')
        
        for row in rows:
            text = row.get_text(separator=' ')
            # Wyciągamy liczby
            import re
            numbers = re.findall(r'\b\d+\b', text)
            
            # Szybkie 600: 6 liczb z zakresu 1-32
            valid_nums = []
            for n in numbers:
                val = int(n)
                if 1 <= val <= 32:
                    valid_nums.append(val)
            
            # Wiersz powinien zawierać datę, numer i 6 liczb wyniku.
            # Zazwyczaj bierzemy ostatnie 6 liczb z wiersza
            if len(valid_nums) >= 6:
                draw_result = list(set(valid_nums[-6:])) # Ostatnie 6
                # Sprawdzenie poprawności (czy mamy 6 unikalnych liczb)
                if len(draw_result) == 6:
                    parsed_draws.append(draw_result)

        if not parsed_draws:
            return [], "Nie udało się pobrać tabeli."
            
        return parsed_draws, None

    except Exception as e:
        return [], f"Błąd połączenia: {str(e)}"

def get_hot_weights(draws):
    if not draws: return [1] * 32
    flat = [n for d in draws for n in d]
    c = Counter(flat)
    return [c.get(i, 1) for i in range(1, 33)]

# --- ALGORYTM SMART 600 ---
def generate_smart_600(weights):
    population = list(range(1, 33)) # Liczby 1-32
    
    for _ in range(5000):
        # 1. Losowanie ważone (Hot Numbers)
        stronger_weights = [w**1.4 for w in weights] # Mocniejsze wagi, bo mały zakres liczb
        
        candidates = set()
        while len(candidates) < 6:
            c = random.choices(population, weights=stronger_weights, k=1)[0]
            candidates.add(c)
        
        nums = sorted(list(candidates))
        
        # --- FILTRY SZYBKIE 600 ---
        
        # 1. Suma (Dla 6 z 32 średnia to 99. Celujemy w 75-125)
        s_sum = sum(nums)
        if not (75 <= s_sum <= 125):
            continue
            
        # 2. Parzystość (Unikamy 6:0 i 0:6)
        even = sum(1 for n in nums if n % 2 == 0)
        if even == 0 or even == 6:
            continue
            
        # 3. Ciągi (Max 2 liczby obok siebie, np. 5,6. Ale 5,6,7 odrzucamy)
        consecutive = 0
        max_cons = 0
        for i in range(len(nums)-1):
            if nums[i+1] == nums[i] + 1: consecutive += 1
            else: consecutive = 0
            max_cons = max(max_cons, consecutive)
        
        if max_cons >= 2:
            continue
            
        return nums, s_sum, even

    return nums, sum(nums), 0

# --- INTERFEJS ---
def main():
    st.title("🚀 Szybkie 600 Smart")
    
    with st.spinner("Pobieranie wyników LIVE..."):
        draws, error = get_live_draws_600()
        
    if draws:
        status_html = f"<div class='status-badge' style='color:#58a6ff; border-color:#58a6ff;'>🟢 ONLINE: {len(draws)} losowań</div>"
        weights = get_hot_weights(draws)
    else:
        status_html = f"<div class='status-badge' style='color:#ffa500; border-color:#ffa500;'>🟠 TRYB SYMULACJI ({error})</div>"
        weights = [1] * 32

    st.markdown(status_html, unsafe_allow_html=True)
    st.markdown("Algorytm analizuje wyniki co 4 minuty.")

    if st.button("GENERUJ TYP (6 liczb)", use_container_width=True):
        res, s_sum, ev = generate_smart_600(weights)
        
        st.divider()
        
        # Kule
        cols = st.columns(6)
        for i, n in enumerate(res):
            cols[i].markdown(f"<div class='ball-600'>{n}</div>", unsafe_allow_html=True)
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Statystyki
        c1, c2 = st.columns(2)
        c1.markdown(f"<div class='metric-box'>📐 Suma: <b>{s_sum}</b><br><small>(Norma: 75-125)</small></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='metric-box'>⚖️ Parzyste: <b>{ev}/6</b><br><small>(Balans)</small></div>", unsafe_allow_html=True)
        
        st.caption("System zoptymalizowany pod mały zakres liczb (1-32).")

if __name__ == "__main__":
    main()
