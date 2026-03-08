import streamlit as st
import google.generativeai as genai
import PIL.Image
import json
from datetime import datetime

# Configuração da Página
st.set_page_config(page_title="Frequência - Ezequiel Miranda", page_icon="📝")

# Configuração da API
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
except Exception:
    st.error("⚠️ Configure a GEMINI_API_KEY nos Secrets.")
    st.stop()

if 'attendance' not in st.session_state:
    st.session_state.attendance = {}

def process_image(uploaded_file):
    try:
        # Usando a versão 8b para economizar cota e evitar erro 429
        model = genai.GenerativeModel('gemini-1.5-flash-8b')
        img = PIL.Image.open(uploaded_file)
        
        prompt = """
        Extraia da tabela: Nome (coluna 1) e Status (coluna 2).
        Retorne APENAS um JSON: [{"nome": "NOME", "categoria": "SIM ou PULMÃO"}]
        """
        
        response = model.generate_content([prompt, img])
        txt = response.text
        start, end = txt.find('['), txt.rfind(']') + 1
        data = json.loads(txt[start:end])
        
        for item in data:
            nome = item.get("nome", "").strip().upper()
            if len(nome) > 2 and nome not in st.session_state.attendance:
                st.session_state.attendance[nome] = {
                    "categoria": item.get("categoria", "SIM").strip().upper(),
                    "status": "Presente", "justification": ""
                }
        return True
    except Exception as e:
        if "429" in str(e):
            st.error("Limite de uso atingido. Aguarde 60 segundos e tente novamente.")
        else:
            st.error(f"Erro: {e}")
        return False

st.title("📝 Controle de Frequência")
st.caption("Analista: Ezequiel Miranda")

uploaded_file = st.file_uploader("Suba a imagem", type=["png", "jpg", "jpeg"])
if uploaded_file and st.button("Processar"):
    with st.spinner("Lendo..."):
        if process_image(uploaded_file):
            st.success("Sucesso!")
            st.rerun()

if st.session_state.attendance:
    nomes = sorted(st.session_state.attendance.keys())
    for n in nomes:
        d = st.session_state.attendance[n]
        c1, c2, c3 = st.columns([2, 1, 1.5])
        with c1:
            st.write(f"**{n}** {'🫁' if 'PULM' in d['categoria'] else ''}")
        with c2:
            st.session_state.attendance[n]["status"] = st.radio(f"S_{n}", ["Presente", "ABS"], key=f"s_{n}", label_visibility="collapsed", horizontal=True)
        with c3:
            if st.session_state.attendance[n]["status"] == "ABS":
                st.session_state.attendance[n]["justification"] = st.selectbox(f"J_{n}", ["Injustificado", "Atestado", "Declaração"], key=f"j_{n}", label_visibility="collapsed")

    if st.button("📋 Gerar Relatório"):
        hoje = datetime.now().strftime("%d/%m")
        na, pulm = [], []
        for n in nomes:
            d = st.session_state.attendance[n]
            if d["status"] == "ABS":
                txt = f"- {n} {'❌ ' if 'PULM' in d['categoria'] else ''}( {d['justification']})"
                if "PULM" in d["categoria"]: pulm.append(txt)
                else: na.append(txt)
        
        rel = f"ABS ({hoje})\n\nN/A\n" + ("\n".join(na) if na else "Nenhum")
        rel += f"\n\nPulmões 🫁\n" + ("\n".join(pulm) if pulm else "Nenhum")
        st.code(rel, language="text")

if st.sidebar.button("Limpar"):
    st.session_state.attendance = {}
    st.rerun()
