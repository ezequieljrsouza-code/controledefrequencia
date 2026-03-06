import streamlit as st
import google.generativeai as genai
import PIL.Image
import json
import base64

# Configuração da página
st.set_page_config(page_title="Controle de Frequência - Ezequiel Miranda", page_icon="📝", layout="centered")

# Estilo CSS para melhorar a aparência
st.markdown("""
    <style>
    .main {
        background-color: #f8fafc;
    }
    .stButton>button {
        width: 100%;
        border-radius: 10px;
    }
    .attendance-row {
        padding: 10px;
        border-bottom: 1px solid #e2e8f0;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    </style>
    """, unsafe_allow_html=True)

# Inicialização da API Gemini
# Nota: No Streamlit Cloud, adicione sua chave em "Secrets"
API_KEY = "" 
genai.configure(api_key=API_KEY)

# Inicialização do estado da sessão
if 'names' not in st.session_state:
    st.session_state.names = []
if 'attendance' not in st.session_state:
    st.session_state.attendance = {}

def process_image(uploaded_file):
    """Processa a imagem usando Gemini para extrair nomes."""
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        img = PIL.Image.open(uploaded_file)
        
        prompt = "Analise esta imagem de uma lista de nomes. Extraia apenas os nomes completos das pessoas. Retorne os nomes separados por vírgula. Ignore cabeçalhos como 'Nome' ou 'Produtivo'."
        
        response = model.generate_content([prompt, img])
        text = response.text
        
        if text:
            extracted = [n.strip() for n in text.split(',') if len(n.strip()) > 3]
            # Limpeza de duplicados e palavras-chave indesejadas
            extracted = [n for n in extracted if "PRODUTIVO" not in n.upper() and "NOME" not in n.upper()]
            
            new_names = sorted(list(set(st.session_state.names + extracted)))
            st.session_state.names = new_names
            
            # Inicializa presença para novos nomes
            for name in extracted:
                if name not in st.session_state.attendance:
                    st.session_state.attendance[name] = {"status": "Presente", "justification": ""}
            return True
    except Exception as e:
        st.error(f"Erro ao processar imagem: {e}")
        return False

# Interface do Utilizador
st.title("📝 Controle de Frequência")
st.subheader(f"Responsável: Ezequiel Miranda (Marituba/PA)")

# Upload de Ficheiro
with st.expander("📷 Carregar Lista de Nomes (Imagem)", expanded=not st.session_state.names):
    uploaded_file = st.file_uploader("Suba a foto da lista de produtividade", type=["png", "jpg", "jpeg"])
    if uploaded_file is not None:
        if st.button("Processar Imagem"):
            with st.spinner("A extrair nomes com IA..."):
                if process_image(uploaded_file):
                    st.success("Nomes extraídos com sucesso!")
                    st.rerun()

# Botão para limpar lista
if st.session_state.names:
    if st.sidebar.button("🗑️ Limpar Toda a Lista"):
        st.session_state.names = []
        st.session_state.attendance = {}
        st.rerun()

# Lista de Chamada
if st.session_state.names:
    st.write("---")
    st.info(f"Total de pessoas: {len(st.session_state.names)}")
    
    for name in st.session_state.names:
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.markdown(f"**{name.upper()}**")
            
        with col2:
            current_status = st.session_state.attendance[name]["status"]
            status_idx = 0 if current_status == "Presente" else 1
            
            status = st.radio(
                f"Status para {name}",
                ["Presente", "ABS"],
                index=status_idx,
                key=f"status_{name}",
                label_visibility="collapsed",
                horizontal=True
            )
            st.session_state.attendance[name]["status"] = status
            
        with col3:
            if status == "ABS":
                just = st.selectbox(
                    f"Justificativa para {name}",
                    ["Injustificado", "Atestado", "Declaração"],
                    key=f"just_{name}",
                    label_visibility="collapsed"
                )
                st.session_state.attendance[name]["justification"] = just
            else:
                st.session_state.attendance[name]["justification"] = ""
                st.write("-")

    # Botão de Exportação
    st.write("---")
    if st.button("💾 Gerar Relatório (JSON/Texto)"):
        report = {
            "responsavel": "Ezequiel Miranda",
            "dados": st.session_state.attendance
        }
        json_string = json.dumps(report, indent=4, ensure_ascii=False)
        st.download_button(
            label="Descarregar Relatório",
            file_name="frequencia_marituba.json",
            mime="application/json",
            data=json_string
        )

else:
    st.warning("Aguardando carregamento de nomes via imagem.")
