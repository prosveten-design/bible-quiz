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

# Конфигурация
st.set_page_config(page_title="Библейска Викторина", page_icon="📖")

# --- ШРИФТ ---
def register_fonts():
    for name in ["arial.ttf", "Arial.ttf", "ARIAL.TTF"]:
        if os.path.exists(name):
            try:
                pdfmetrics.registerFont(TTFont('ArialCustom', name))
                return 'ArialCustom'
            except: continue
    return 'Helvetica'

FONT_NAME = register_fonts()

# --- PDF ГЕНЕРАТОР (ДВЕ КОЛОНИ) ---
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

def generate_pdf_bytes(name, score, max_score, history):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer)
    c.setFont(FONT_NAME, 16)
    c.drawString(50, 800, "ОФИЦИАЛЕН ОТЧЕТ ОТ БИБЛЕЙСКИ ТЕСТ")
    c.setFont(FONT_NAME, 12)
    c.drawString(50, 775, f"Ученик: {name} | Резултат: {score}/{max_score}")
    c.line(50, 765, 550, 765)

    col1_x, col2_x, y, cur_x = 50, 310, 730, 50
    for i, h in enumerate(history):
        if y < 120:
            if cur_x == col1_x: cur_x, y = col2_x, 730
            else: c.showPage(); cur_x, y = col1_x, 800
        
        c.setFont(FONT_NAME, 9)
        c.drawString(cur_x, y, f"{i+1}. {h['q'][:50]}")
        y -= 12
        c.setFont(FONT_NAME, 8)
        for idx, opt in enumerate(h['options']):
            status = None
            if idx == h['user_idx']: status = "correct" if h['is_right'] else "wrong"
            elif idx == h['correct_idx'] and not h['is_right']: status = "correct"
            draw_box(c, cur_x + 10, y, status)
            c.drawString(cur_x + 25, y, opt[:35])
            y -= 11
        y -= 8
    c.save()
    return buffer.getvalue()

# --- ЛОГИКА ---
def load_questions():
    if os.path.exists('questions.json'):
        with open('questions.json', 'r', encoding='utf-8') as f:
            return {int(k): v for k, v in json.load(f).items()}
    return None

def main():
    questions_db = load_questions()
    if not questions_db:
        st.error("Липсва questions.json!")
        return

    if 'step' not in st.session_state:
        st.session_state.update({
            'step': 'intro', 'score': 0, 'history': [], 
            'current_q_idx': 0, 'selected_qs': [], 'user_name': ''
        })

    if st.session_state.step == "intro":
        st.title("📖 Библейска Викторина")
        name = st.text_input("Вашето име:")
        level = st.selectbox("Ниво:", sorted(list(questions_db.keys())))
        num_q = st.slider("Брой въпроси:", 5, 20, 10)
        
        if st.button("Започни"):
            if name:
                st.session_state.user_name = name
                all_qs = questions_db[level]
                random.shuffle(all_qs)
                st.session_state.selected_qs = all_qs[:min(len(all_qs), num_q)]
                st.session_state.step = "quiz"
                st.rerun()

    elif st.session_state.step == "quiz":
        idx = st.session_state.current_q_idx
        q_data = st.session_state.selected_qs[idx]

        st.write(f"Въпрос {idx+1} от {len(st.session_state.selected_qs)}")
        st.subheader(q_data[0])
        
        # Ключова промяна: Радио бутонът НЕ се нулира
        choice = st.radio("Изберете:", q_data[1], key=f"q_{idx}")

        if st.button("Следващ ➡️"):
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
        st.header("Край!")
        max_p = len(st.session_state.selected_qs) * 10
        st.success(f"{st.session_state.user_name}, резултат: {st.session_state.score} / {max_p}")
        
        pdf = generate_pdf_bytes(st.session_state.user_name, st.session_state.score, max_p, st.session_state.history)
        st.download_button("📥 PDF Отчет", data=pdf, file_name="Report.pdf")
        
        if st.button("Нов тест"):
            for k in list(st.session_state.keys()): del st.session_state[k]
            st.rerun()

if __name__ == "__main__":
    main()