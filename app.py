import streamlit as st
import google.generativeai as genai
import PIL.Image
import json
from datetime import datetime

# Configuração da página - Ezequiel Miranda
st.set_page_config(page_title="Controle de Frequência", page_icon="📝")

# Tenta carregar a chave dos Secrets do Streamlit
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
except Exception:
    st.error("Erro: A chave 'GEMINI_API_KEY' não foi encontrada nos Secrets do Streamlit.")
    st.stop()

if 'attendance' not in st.session_state:
    st.session_state.attendance = {}

def process_image(uploaded_file):
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        img = PIL.Image.open(uploaded_file)
        
        prompt = """
        Analise a tabela. Extraia os nomes (coluna 1) e o status (coluna 2 - PRODUTIVO?).
        Retorne um JSON puro: [{"nome": "NOME", "categoria": "SIM ou PULMÃO"}].
        Ignore o cabeçalho.
        """
        
        response = model.generate_content([prompt, img])
        text = response.text.replace("```json", "").replace("```", "").strip()
        data = json.loads(text)
        
        for item in data:
            nome = item["nome"].strip().upper()
            if len(nome) < 3: continue
            
            if nome not in st.session_state.attendance:
                st.session_state.attendance[nome] = {
                    "categoria": item["categoria"].strip().upper(),
                    "status": "Presente", 
                    "justification": ""
                }
        return True
    except Exception as e:
        st.error(f"Erro na IA: {e}")
        return False

st.title("📝 Controle de Frequência")
st.subheader("Responsável: Ezequiel Miranda")

# Upload
uploaded_file = st.file_uploader("Suba a imagem da lista", type=["png", "jpg", "jpeg"])
if uploaded_file and st.button("Processar Lista"):
    if process_image(uploaded_file):
        st.success("Lista carregada!")

# Lista de Chamada
if st.session_state.attendance:
    st.write("---")
    for name in sorted(st.session_state.attendance.keys()):
        dados = st.session_state.attendance[name]
        col1, col2, col3 = st.columns([2, 1, 1.5])
        
        with col1:
            tag = " 🫁" if "PULM" in dados["categoria"] else ""
            st.markdown(f"**{name}**{tag}")
            
        with col2:
            status = st.radio(f"S_{name}", ["Presente", "ABS"], horizontal=True, 
                              key=f"s_{name}", label_visibility="collapsed")
            st.session_state.attendance[name]["status"] = status
            
        with col3:
            if status == "ABS":
                just = st.selectbox(f"J_{name}", ["Injustificado", "Atestado", "Declaração", "Suspensão"],
                                    key=f"j_{name}", label_visibility="collapsed")
                st.session_state.attendance[name]["justification"] = just

    # Gerar Relatório Formatado
    if st.button("Gerar Relatório para WhatsApp"):
        hoje = datetime.now().strftime("%d/%m")
        na, pulm = [], []
        
        for n, d in st.session_state.attendance.items():
            if d["status"] == "ABS":
                txt = f"- {n} {'❌ ' if 'PULM' in d['categoria'] else ''}( {d['justification']})"
                if "PULM" in d["categoria"]: pulm.append(txt)
                else: na.append(txt)

        rel = f"ABS ({hoje})\n\nN/A\n" + ("\n".join(na) if na else "Nenhum")
        rel += f"\n\nPulmões 🫁\n" + ("\n".join(pulm) if pulm else "Nenhum")
        rel += f"\n\nABS real: {len(na)}"
        
        st.code(rel, language="text")

if st.sidebar.button("Limpar Dados"):
    st.session_state.attendance = {}
    st.rerun()
