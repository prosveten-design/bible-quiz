import streamlit as st
import json
import random
import os
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
import io

# Конфигурация на страницата
st.set_page_config(page_title="Библейска Викторина", page_icon="📖")

# Регистриране на шрифт за PDF
try:
    pdfmetrics.registerFont(TTFont('Arial', 'arial.ttf'))
    FONT_NAME = 'Arial'
except:
    FONT_NAME = 'Helvetica'

# --- ФУНКЦИИ ---
def load_questions():
    if os.path.exists('questions.json'):
        try:
            with open('questions.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {int(k): v for k, v in data.items()}
        except: return None
    return None

def generate_pdf_bytes(name, score, max_score, history):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer)
    c.setFont(FONT_NAME, 16)
    c.drawString(50, 800, "ОФИЦИАЛЕН ОТЧЕТ ОТ БИБЛЕЙСКИ ТЕСТ")
    
    c.setFont(FONT_NAME, 12)
    c.drawString(50, 775, f"Ученик: {name}")
    c.drawString(50, 760, f"Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    c.drawString(50, 740, f"Резултат: {score} от {max_score} точки")
    c.line(50, 730, 550, 730)

    y = 700
    c.setFont(FONT_NAME, 10)
    for i, h in enumerate(history):
        if y < 100:
            c.showPage()
            y = 800
        status = "Верен" if h['is_right'] else "Грешен"
        q_text = f"{i+1}. {h['q'][:65]}... - {status}"
        c.drawString(50, y, q_text)
        y -= 20

    c.save()
    return buffer.getvalue()

# --- ОСНОВНО ПРИЛОЖЕНИЕ ---
def main():
    questions_db = load_questions()

    if not questions_db:
        st.error("Файлът 'questions.json' липсва или е повреден!")
        return

    # Инициализация на всички променливи в session_state
    if 'step' not in st.session_state:
        st.session_state.step = "intro"
        st.session_state.score = 0
        st.session_state.history = []
        st.session_state.current_q_idx = 0
        st.session_state.selected_qs = []
        st.session_state.user_name = "" # Инициализираме тук, за да няма AttributeError

    # --- ЕКРАН 1: ВХОД ---
    if st.session_state.step == "intro":
        st.header("📖 Библейска Викторина")
        
        # Използваме обикновена променлива за името и я прехвърляме в сесията при бутон
        name_input = st.text_input("Въведете вашето име:")
        level = st.selectbox("Изберете ниво на трудност:", sorted(list(questions_db.keys())))
        
        if st.button("Започни теста"):
            if name_input.strip():
                st.session_state.user_name = name_input
                all_qs = questions_db[level]
                st.session_state.selected_qs = random.sample(all_qs, min(len(all_qs), 5))
                st.session_state.step = "quiz"
                st.rerun()
            else:
                st.warning("Моля, въведете име преди да започнете!")

    # --- ЕКРАН 2: ТЕСТ ---
    elif st.session_state.step == "quiz":
        q_idx = st.session_state.current_q_idx
        q_data = st.session_state.selected_qs[q_idx]

        st.info(f"Ученик: {st.session_state.user_name} | Въпрос {q_idx + 1} от {len(st.session_state.selected_qs)}")
        st.progress((q_idx) / len(st.session_state.selected_qs))
        
        st.subheader(q_data[0])
        choice = st.radio("Изберете отговор:", q_data[1], key=f"radio_{q_idx}")

        if st.button("Потвърди и продължи ➡️"):
            is_right = (q_data[1].index(choice) == q_data[2])
            if is_right:
                st.session_state.score += 10
            
            st.session_state.history.append({
                "q": q_data[0],
                "is_right": is_right
            })

            if q_idx + 1 < len(st.session_state.selected_qs):
                st.session_state.current_q_idx += 1
                st.rerun()
            else:
                st.session_state.step = "finish"
                st.rerun()

    # --- ЕКРАН 3: ФИНАЛ ---
    elif st.session_state.step == "finish":
        st.balloons()
        st.header("🎉 Браво!")
        max_p = len(st.session_state.selected_qs) * 10
        st.metric("Краен резултат", f"{st.session_state.score} от {max_p} точки")

        # Генериране на PDF
        pdf_bytes = generate_pdf_bytes(
            st.session_state.user_name, 
            st.session_state.score, 
            max_p, 
            st.session_state.history
        )

        st.download_button(
            label="📥 Изтегли твоя сертификат (PDF)",
            data=pdf_bytes,
            file_name=f"Rezultat_{st.session_state.user_name}.pdf",
            mime="application/pdf"
        )

        if st.button("Нов тест 🔄"):
            # Изчистване на сесията за ново стартиране
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

if __name__ == "__main__":
    main()