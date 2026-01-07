import streamlit as st
import json
import random
import os
import io
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors

# Конфигурация на страницата
st.set_page_config(page_title="Библейска Викторина", page_icon="📖", layout="centered")

# --- ЗАРЕЖДАНЕ НА ШРИФТ ---
def register_fonts():
    possible_names = ["arial.ttf", "Arial.ttf", "ARIAL.TTF"]
    for name in possible_names:
        if os.path.exists(name):
            try:
                pdfmetrics.registerFont(TTFont('ArialCustom', name))
                return 'ArialCustom'
            except: continue
    return 'Helvetica'

FONT_NAME = register_fonts()

# --- ФУНКЦИИ ЗА PDF ДИЗАЙН ---
def draw_box(c, x, y, status):
    c.setLineWidth(0.5)
    c.setStrokeColor(colors.black)
    c.rect(x, y, 8, 8)
    if status == "correct":
        c.setStrokeColor(colors.green)
        c.line(x+1, y+4, x+3, y+1)
        c.line(x+3, y+1, x+7, y+7)
    elif status == "wrong":
        c.setStrokeColor(colors.red)
        c.line(x+2, y+2, x+6, y+6)
        c.line(x+2, y+6, x+6, y+2)
    c.setStrokeColor(colors.black)

def generate_pdf_bytes(name, score, max_score, history):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer)
    
    # Заглавие
    c.setFont(FONT_NAME, 16)
    c.drawString(50, 800, "ОФИЦИАЛЕН ОТЧЕТ ОТ БИБЛЕЙСКИ ТЕСТ")
    
    # Информация
    c.setFont(FONT_NAME, 12)
    c.drawString(50, 775, f"Ученик: {name}")
    c.drawString(50, 760, f"Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    
    perc = (score / max_score) * 100 if max_score > 0 else 0
    grade_col = colors.darkgreen if perc >= 70 else colors.red
    
    c.setFont(FONT_NAME, 14)
    c.setFillColor(grade_col)
    c.drawString(50, 740, f"ОБЩ РЕЗУЛТАТ: {score} от {max_score} т. ({perc:.0f}%)")
    c.setFillColor(colors.black)
    c.line(50, 730, 550, 730)

    # Двуколонен изглед
    col1_x, col2_x, y, cur_x = 50, 310, 700, 50

    for i, h in enumerate(history):
        if y < 120:
            if cur_x == col1_x:
                cur_x, y = col2_x, 700
            else:
                c.showPage()
                cur_x, y = col1_x, 800
        
        c.setFont(FONT_NAME, 9)
        q_txt = f"{i+1}. {h['q'][:55]}"
        c.drawString(cur_x, y, q_txt)
        y -= 12
        
        c.setFont(FONT_NAME, 8)
        for idx, opt in enumerate(h['options']):
            status = None
            if idx == h['user_idx']:
                status = "correct" if h['is_right'] else "wrong"
            elif idx == h['correct_idx'] and not h['is_right']:
                status = "correct"
            
            draw_box(c, cur_x + 10, y, status)
            c.drawString(cur_x + 25, y, opt[:40])
            y -= 11
        y -= 8 

    if y < 80: c.showPage(); y = 800
    y -= 40
    c.line(350, y, 530, y)
    c.setFont(FONT_NAME, 8)
    c.drawString(380, y - 12, "Подпис / Проверяващ")
    
    c.save()
    return buffer.getvalue()

# --- ЛОГИКА ЗА ЗАРЕЖДАНЕ ---
def load_questions():
    if os.path.exists('questions.json'):
        try:
            with open('questions.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {int(k): v for k, v in data.items()}
        except: return None
    return None

# --- ГЛАВНО ПРИЛОЖЕНИЕ ---
def main():
    questions_db = load_questions()
    if not questions_db:
        st.error("Въпросите не могат да бъдат заредени!")
        return

    if 'step' not in st.session_state:
        st.session_state.step = "intro"
        st.session_state.score = 0
        st.session_state.history = []
        st.session_state.current_q_idx = 0
        st.session_state.selected_qs = []
        st.session_state.user_name = ""

    if st.session_state.step == "intro":
        st.title("📖 Библейска Викторина")
        name_in = st.text_input("Вашето име:")
        level = st.selectbox("Изберете ниво:", sorted(list(questions_db.keys())))
        num_q = st.slider("Брой въпроси за теста:", 5, 20, 10)
        
        if st.button("Започни теста"):
            if name_in:
                st.session_state.user_name = name_in
                all_qs = questions_db[level]
                
                # ТУК Е КЛЮЧЪТ: Разбъркваме всичко преди избор
                temp_qs = all_qs.copy()
                random.shuffle(temp_qs)
                
                st.session_state.selected_qs = random.sample(temp_qs, min(len(temp_qs), num_q))
                st.session_state.step = "quiz"
                st.rerun()
            else:
                st.warning("Въведете име!")

    elif st.session_state.step == "quiz":
        idx = st.session_state.current_q_idx
        q_data = st.session_state.selected_qs[idx]

        st.write(f"Ученик: **{st.session_state.user_name}** | Въпрос {idx+1} от {len(st.session_state.selected_qs)}")
        st.progress((idx)/len(st.session_state.selected_qs))
        st.subheader(q_data[0])
        
        choice = st.radio("Изберете отговор:", q_data[1], key=f"r_{idx}_{random.randint(0,9999)}")

        if st.button("Следващ въпрос ➡️"):
            user_idx = q_data[1].index(choice)
            is_right = (user_idx == q_data[2])
            if is_right: st.session_state.score += 10
            
            st.session_state.history.append({
                "q": q_data[0], "options": q_data[1], "user_idx": user_idx,
                "correct_idx": q_data[2], "is_right": is_right
            })
            
            if idx + 1 < len(st.session_state.selected_qs):
                st.session_state.current_q_idx += 1
                st.rerun()
            else:
                st.session_state.step = "finish"
                st.rerun()

    elif st.session_state.step == "finish":
        st.balloons()
        st.header("Край на теста!")
        max_p = len(st.session_state.selected_qs) * 10
        st.metric("Твоят резултат", f"{st.session_state.score} / {max_p}")

        pdf_bytes = generate_pdf_bytes(st.session_state.user_name, st.session_state.score, max_p, st.session_state.history)
        
        st.download_button("📥 Изтегли PDF Отчет", data=pdf_bytes, file_name=f"Report_{st.session_state.user_name}.pdf")
        
        if st.button("🔄 Нов тест"):
            for k in list(st.session_state.keys()): del st.session_state[k]
            st.rerun()

if __name__ == "__main__":
    main()