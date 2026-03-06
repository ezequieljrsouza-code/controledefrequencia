import streamlit as st
import google.generativeai as genai
import PIL.Image
import json

# Configuração da página
st.set_page_config(page_title="Controle de Frequência - Ezequiel Miranda", page_icon="📝", layout="wide")

# Estilo CSS para melhorar a interface
st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    .stRadio > div { flex-direction: row; align-items: center; }
    .stRadio label { margin-right: 15px; }
    div[data-testid="column"] {
        padding: 10px;
        border-bottom: 1px solid #eee;
    }
    </style>
    """, unsafe_allow_html=True)

# Configuração da API Gemini (Insira sua chave aqui ou nos Secrets do Streamlit)
API_KEY = "SUA_CHAVE_AQUI" 
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
            # Limpeza e formatação dos nomes
            extracted = [n.strip().upper() for n in text.split(',') if len(n.strip()) > 3]
            # Remove termos que não são nomes
            extracted = [n for n in extracted if "PRODUTIVO" not in n and "NOME" not in n]
            
            # Atualiza a lista global sem duplicados
            new_names = sorted(list(set(st.session_state.names + extracted)))
            st.session_state.names = new_names
            
            # Inicializa o dicionário de presença
            for name in extracted:
                if name not in st.session_state.attendance:
                    st.session_state.attendance[name] = {"status": "Presente", "justification": "N/A"}
            return True
    except Exception as e:
        st.error(f"Erro ao processar imagem: {e}")
        return False

# --- INTERFACE ---
st.title("📝 Controle de Frequência")
st.subheader(f"Responsável: Ezequiel Miranda (Marituba/PA)")

# Upload de Arquivo
with st.expander("📷 Carregar Lista de Nomes (Imagem)", expanded=not st.session_state.names):
    uploaded_file = st.file_uploader("Suba a foto da lista de produtividade", type=["png", "jpg", "jpeg"])
    if uploaded_file:
        if st.button("🚀 Processar e Gerar Lista"):
            with st.spinner("A extrair nomes com IA..."):
                if process_image(uploaded_file):
                    st.success("Nomes extraídos com sucesso!")
                    st.rerun()

# Barra Lateral
if st.session_state.names:
    if st.sidebar.button("🗑️ Limpar Tudo"):
        st.session_state.names = []
        st.session_state.attendance = {}
        st.rerun()

# --- LISTA DE CHAMADA ---
if st.session_state.names:
    st.write("---")
    header_col1, header_col2, header_col3 = st.columns([2, 1, 1])
    header_col1.subheader("Nome do Colaborador")
    header_col2.subheader("Presença")
    header_col3.subheader("Justificativa (se ABS)")

    for name in st.session_state.names:
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.markdown(f"**{name}**")
            
        with col2:
            # Define o índice baseado no que já está salvo
            current_status = st.session_state.attendance[name]["status"]
            status_options = ["Presente", "ABS"]
            default_idx = status_options.index(current_status) if current_status in status_options else 0
            
            status = st.radio(
                "Status",
                status_options,
                index=default_idx,
                key=f"status_{name}",
                label_visibility="collapsed",
                horizontal=True
            )
            st.session_state.attendance[name]["status"] = status
            
        with col3:
            if status == "ABS":
                # Lista suspensa conforme solicitado
                just_options = ["Injustificado", "Atestado", "Declaração"]
                current_just = st.session_state.attendance[name].get("justification", "Injustificado")
                # Garante que o index seja válido
                just_idx = just_options.index(current_just) if current_just in just_options else 0
                
                just = st.selectbox(
                    "Motivo",
                    just_options,
                    index=just_idx,
                    key=f"just_{name}",
                    label_visibility="collapsed"
                )
                st.session_state.attendance[name]["justification"] = just
            else:
                st.session_state.attendance[name]["justification"] = "N/A"
                st.write("✅")

    # --- EXPORTAÇÃO ---
    st.write("---")
    if st.button("💾 Finalizar e Gerar Relatório"):
        report = {
            "responsavel": "Ezequiel Miranda",
            "unidade": "Marituba/PA",
            "total_colaboradores": len(st.session_state.names),
            "dados": st.session_state.attendance
        }
        json_string = json.dumps(report, indent=4, ensure_ascii=False)
        
        st.download_button(
            label="⬇️ Baixar Relatório (JSON)",
            file_name=f"frequencia_{name}.json",
            mime="application/json",
            data=json_string
        )
        st.json(report)

else:
    st.info("Aguardando o upload da imagem para gerar a lista de presença.")
