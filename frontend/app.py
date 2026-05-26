import streamlit as st
import pandas as pd
import requests
from datetime import datetime

import os

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(page_title="RM Comportamental", page_icon="🌳", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    .stApp { background-color: #f4f7f6; color: #2b2d42; }
    h1, h2, h3 { color: #2a9d8f; font-family: 'Inter', sans-serif; }
    [data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #e9ecef; }
    .stButton>button { background-color: #2a9d8f; color: white; border-radius: 8px; border: none; transition: 0.3s; }
    .stButton>button:hover { background-color: #21867a; color: white; transform: scale(1.02); }
    .btn-red>button { background-color: #e76f51; font-size: 18px; padding: 15px; }
    .btn-green>button { background-color: #2a9d8f; font-size: 18px; padding: 15px; }
    </style>
""", unsafe_allow_html=True)

# Helper functions to talk to API
def get_data(endpoint):
    try:
        r = requests.get(f"{API_URL}/{endpoint}", timeout=2)
        return r.json() if r.status_code == 200 else []
    except Exception:
        return []

def post_data(endpoint, payload):
    try:
        r = requests.post(f"{API_URL}/{endpoint}", json=payload, timeout=2)
        return r.status_code, r.json()
    except Exception as e:
        return 500, {"detail": str(e)}

# --- Autenticação ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "user_role" not in st.session_state:
    st.session_state["user_role"] = None
if "username" not in st.session_state:
    st.session_state["username"] = None

if not st.session_state["logged_in"]:
    logo_path = os.path.join(os.path.dirname(__file__), "logo.jpg")
    
    col_logo_1, col_logo_2, col_logo_3 = st.columns([2, 1, 2])
    with col_logo_2:
        if os.path.exists(logo_path):
            st.image(logo_path, use_container_width=True)
            
    st.markdown("<h1 style='text-align: center; color: #2a9d8f;'>🌳 RM Comportamental</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #666;'>Sistema Clínico Inteligente com Automação de Relatórios por IA e Compliance EVV.</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.container(border=True):
            st.info("Logins para testes:\n- **admin** (Acesso total)\n- **ana** (Terapeuta)\n- **familia** (Portal Restrito)")
            usuario = st.text_input("Usuário")
            senha = st.text_input("Senha", type="password")
            
            if st.button("Entrar no Sistema Seguro", use_container_width=True):
                if usuario.lower() == "familia":
                    st.session_state["user_role"] = "familia"
                    st.session_state["logged_in"] = True
                elif usuario.lower() == "admin":
                    st.session_state["user_role"] = "admin"
                    st.session_state["username"] = "admin"
                    st.session_state["logged_in"] = True
                else:
                    st.session_state["user_role"] = "terapeuta"
                    st.session_state["username"] = usuario
                    st.session_state["logged_in"] = True
                st.rerun()
else:
    # --- FETCH DATA FROM API ---
    patients = get_data("patients")
    appointments = get_data("appointments")
    goals = get_data("goals")
    evolutions = get_data("evolutions")
    documents = get_data("documents")
    metadata = get_data("metadata")
    professionals = get_data("professionals")

    # ==========================================
    # PORTAL DA FAMÍLIA
    # ==========================================
    if st.session_state["user_role"] == "familia":
        logo_path = os.path.join(os.path.dirname(__file__), "logo.jpg")
        if os.path.exists(logo_path):
            st.sidebar.image(logo_path, use_container_width=True)
        st.sidebar.title("👨‍👩‍👧 Portal da Família")
        st.sidebar.info("Criança Vinculada: João Silva")
        if st.sidebar.button("Sair Seguramente"):
            st.session_state.clear()
            st.rerun()
            
        st.title("🌟 Acompanhamento Clínico")
        st.markdown("Acompanhe o desenvolvimento do seu filho e seus documentos médicos.")
        
        evs_joao = [e for e in evolutions if e["paciente"] == "João Silva"]
        metas_joao = [m for m in goals if m["paciente"] == "João Silva"]
        docs_joao = [d for d in documents if d["paciente"] == "João Silva"]

        tab_evolucao, tab_metas, tab_cofre = st.tabs(["📈 Gráficos de Sessões", "🎯 Plano Terapêutico", "📄 Cofre de Documentos"])
        
        with tab_evolucao:
            st.markdown("### Histórico de Sessões Realizadas")
            for e in reversed(evs_joao):
                with st.expander(f"{e['data']} - {e['area']} (Ver Relatório)"):
                    st.write(f"**Relatório da Sessão:** {e.get('ai_draft', 'Sem relatório.')}")
                    st.caption(f"Assinatura do Responsável (EVV): {e.get('signature', 'Não assinado')}")
                    if e.get("id"):
                        st.markdown(f"[📥 Baixar PDF da Evolução (Oficial)]({API_URL}/evolutions/{e['id']}/pdf)")
            
        with tab_metas:
            for m in metas_joao:
                with st.container(border=True):
                    st.write(f"**Programa / Habilidade:** {m['meta']}")
                    st.progress(m['progresso'] / 100.0)

        with tab_cofre:
            st.markdown("### Documentos Seguros")
            if docs_joao:
                for d in docs_joao:
                    st.download_button(f"📥 Baixar {d['titulo']} (Data: {d['data']})", d['conteudo'], file_name=d['titulo'])
            else:
                st.info("Nenhum documento disponível no cofre.")

    # ==========================================
    # PORTAL CLÍNICO
    # ==========================================
    else:
        logo_path = os.path.join(os.path.dirname(__file__), "logo.jpg")
        if os.path.exists(logo_path):
            st.sidebar.image(logo_path, use_container_width=True)
        st.sidebar.title("🌳 RM Comportamental")
        role_label = "Admin (Coordenação)" if st.session_state["user_role"] == "admin" else "Terapeuta (AT)"
        st.sidebar.info(f"Usuário: **{st.session_state['username']}**\nNível: {role_label}")
        
        menu_options = ["📊 Dashboard", "👥 Pacientes", "📅 Agendamento Inteligente", "🎯 Programas ABA", "📱 Coletor de Dados (Mobile)"]
        
        if st.session_state["user_role"] == "admin":
            menu_options.append("📄 Gestão de Documentos (Cofre)")
            menu_options.append("💰 Faturamento Automático")
            menu_options.append("⚙️ Cadastro Geral")

        menu_selection = st.sidebar.radio("Módulos", menu_options)
        
        if st.sidebar.button("Fazer Logout"):
            st.session_state.clear()
            st.rerun()

        # --- DASHBOARD & PACIENTES & AGENDAMENTOS (Resumo das Fases Anteriores) ---
        if menu_selection == "📊 Dashboard":
            st.title("Visão Geral do Servidor")
            col1, col2, col3 = st.columns(3)
            with col1: st.metric("Pacientes no BD", len(patients))
            with col2: st.metric("Agendamentos Ativos", len(appointments))
            with col3: st.metric("Evoluções com EVV", len(evolutions))
                
            st.markdown("### Agenda Sincronizada via API")
            if appointments:
                st.dataframe(pd.DataFrame(appointments), use_container_width=True, hide_index=True)

        elif menu_selection == "👥 Pacientes":
            st.title("Prontuários Eletrônicos (PEP)")
            for p in patients:
                with st.expander(f"🧑‍⚕️ {p['nome']} - {p['diagnostico']}"):
                    st.write(f"Sessões Usadas: {p['sessoes_usadas']}/{max(p['sessoes_autorizadas'], 1)}")
                    st.progress(p['sessoes_usadas'] / max(p['sessoes_autorizadas'], 1))
                    
                    st.markdown("#### Ficha Cadastral")
                    col_c1, col_c2 = st.columns(2)
                    with col_c1:
                        st.write(f"**Plano de Saúde:** {p.get('plano_saude') or 'Não informado'}")
                        st.write(f"**Pai:** {p.get('nome_pai') or 'Não informado'}")
                        st.write(f"**Mãe:** {p.get('nome_mae') or 'Não informado'}")
                    with col_c2:
                        st.write(f"**Telefone:** {p.get('telefone') or 'Não informado'}")
                        st.write(f"**E-mail:** {p.get('email') or 'Não informado'}")
                        st.write(f"**Endereço:** {p.get('endereco') or 'Não informado'}")
                    
                    st.markdown("#### Histórico de Evoluções")
                    p_evs = [e for e in evolutions if e["paciente"] == p["nome"]]
                    if p_evs:
                        for e in reversed(p_evs):
                            st.write(f"📅 **{e['data']}** - {e['area']}")
                            st.write(f"Relatório: {e['ai_draft']}")
                            st.caption(f"Assinatura (EVV): {e['signature']}")
                            if e.get("id"):
                                st.markdown(f"[📥 Baixar PDF da Evolução (Oficial)]({API_URL}/evolutions/{e['id']}/pdf)")
                            st.markdown("---")
                    else:
                        st.info("Nenhuma evolução registrada para este paciente.")

        elif menu_selection == "📅 Agendamento Inteligente":
            st.title("Motor de Agendamento")
            with st.form("form_ag"):
                pac = st.selectbox("Paciente", [p["nome"] for p in patients])
                terap = st.selectbox("Terapeuta", metadata.get("therapists", []))
                sala = st.selectbox("Sala Física", metadata.get("rooms", []))
                data_ag = st.date_input("Data").strftime("%Y-%m-%d")
                hora_ag = st.time_input("Horário").strftime("%H:%M")
                
                if st.form_submit_button("Agendar"):
                    status, resp = post_data("appointments", {"paciente": pac, "terapeuta": terap, "sala": sala, "data": data_ag, "hora": hora_ag})
                    if status == 200: st.success("Agendado!")
                    else: st.error(resp.get('detail'))

        elif menu_selection == "🎯 Programas ABA":
            st.title("Metas Terapêuticas e Rastreio DTT")
            for m in goals:
                st.write(f"**{m['paciente']}**: {m['meta']} (Evolução: {m['progresso']}%)")

        # --- NOVA TELA: GESTÃO DE DOCUMENTOS ---
        elif menu_selection == "📄 Gestão de Documentos (Cofre)":
            st.title("📄 Cofre Digital do Paciente")
            st.markdown("Armazenamento seguro para Laudos, Termos de Consentimento e Contratos.")
            
            with st.form("form_doc"):
                doc_paciente = st.selectbox("Paciente", [p["nome"] for p in patients])
                doc_titulo = st.text_input("Título do Documento (Ex: Laudo Neurológico.pdf)")
                doc_file = st.file_uploader("Anexar Arquivo")
                
                if st.form_submit_button("Salvar no Cofre"):
                    if doc_file and doc_titulo:
                        status, resp = post_data("documents", {
                            "paciente": doc_paciente, "title": doc_titulo, "content": "BASE64_SIMULADO_DO_ARQUIVO_BINARIO"
                        })
                        st.success(resp["msg"])
                        st.rerun()
                    else:
                        st.warning("Preencha título e anexe o arquivo.")
            
            st.markdown("---")
            st.markdown("### Arquivos Atuais")
            for d in documents:
                st.write(f"📁 **{d['paciente']}** - {d['titulo']} (Upado em {d['data']})")

        elif menu_selection == "💰 Faturamento Automático":
            st.title("Exportação de Faturamento")
            if st.button("Processar Lote Mensal (TISS)"):
                st.success("Lote gerado com sucesso!")

        # --- NOVA FEATURE NO MOBILE COLETOR: IA DRAFTING & EVV ---
        elif menu_selection == "📱 Coletor de Dados (Mobile)":
            st.title("📱 Interface Tablet de Sessão")
            st.markdown("Coleta rápida seguida de Automação de Relatório (IA) e Assinatura Eletrônica (EVV).")
            
            pac_sessao = st.selectbox("Paciente em Sessão Ativa", [p["nome"] for p in patients])
            area_sessao = st.selectbox("Especialidade", ["Terapia Ocupacional", "Fonoaudiologia", "Análise do Comportamento (ABA)"])
            
            # Controle de fluxo do wizard da sessão
            if "sessao_step" not in st.session_state: st.session_state["sessao_step"] = 1
            if "freq_crise" not in st.session_state: st.session_state["freq_crise"] = 0
            if "engajamento" not in st.session_state: st.session_state["engajamento"] = 5
            if "draft_ia" not in st.session_state: st.session_state["draft_ia"] = ""

            # PASSO 1: COLETAR DADOS
            if st.session_state["sessao_step"] == 1:
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("<div class='btn-red'>", unsafe_allow_html=True)
                    if st.button("🔴 Clicar a cada Crise", use_container_width=True):
                        st.session_state["freq_crise"] += 1
                    st.markdown("</div>", unsafe_allow_html=True)
                    st.subheader(f"Crises: {st.session_state['freq_crise']}")
                with col2:
                    st.markdown("<div class='btn-green'>", unsafe_allow_html=True)
                    if st.button("🟢 Botão de Sucesso", use_container_width=True):
                        if st.session_state["engajamento"] < 10: st.session_state["engajamento"] += 1
                    st.markdown("</div>", unsafe_allow_html=True)
                    st.subheader(f"Engajamento: {st.session_state['engajamento']}/10")
                    
                st.markdown("---")
                if st.button("Terminar Sessão e Gerar Relatório c/ IA ✨"):
                    st.session_state["sessao_step"] = 2
                    # Simula a chamada da Inteligência Artificial
                    status, resp = post_data("generate-draft", {"engajamento": st.session_state["engajamento"], "crises": st.session_state["freq_crise"], "area": area_sessao})
                    st.session_state["draft_ia"] = resp["draft"]
                    st.rerun()

            # PASSO 2: REVISÃO DO RELATÓRIO E ASSINATURA (EVV)
            elif st.session_state["sessao_step"] == 2:
                st.info("🤖 **Assistente IA:** Escrevi o relatório clínico com base nos dados que você coletou. Por favor, revise e colete a assinatura do pai/mãe para dar o check-out!")
                
                texto_final = st.text_area("Relatório Clínico (SOAP)", value=st.session_state["draft_ia"], height=150)
                
                st.markdown("### 🔐 Electronic Visit Verification (EVV)")
                assinatura = st.text_input("Assinatura Eletrônica (Nome do Pai/Mãe ou PIN)", placeholder="Solicite ao familiar que digite o nome aqui")
                
                if st.button("Assinar e Salvar Sessão ✅"):
                    if not assinatura:
                        st.warning("A assinatura do responsável é obrigatória (EVV)!")
                    else:
                        status, resp = post_data("evolutions", {
                            "paciente": pac_sessao, "data": datetime.now().strftime("%Y-%m-%d"), "area": area_sessao,
                            "metrics": {"engajamento_score": st.session_state["engajamento"], "crises_registradas": st.session_state["freq_crise"]},
                            "ai_draft": texto_final, "signature": assinatura
                        })
                        if status == 200:
                            st.success("✅ Sessão salva! Relatório aprovado, assinatura validada e faturamento descontado.")
                            st.session_state["sessao_step"] = 1
                            st.session_state["freq_crise"] = 0
                            st.session_state["engajamento"] = 5
                            st.session_state["draft_ia"] = ""
                            st.rerun()
                        else:
                            st.error("Erro ao salvar sessão.")

        elif menu_selection == "⚙️ Cadastro Geral":
            st.title("⚙️ Cadastro Geral de Clínicos e Pacientes")
            st.markdown("Área restrita à coordenação para expansão da clínica.")
            
            tab_cad_paciente, tab_cad_profissional = st.tabs(["🧑‍⚕️ Novo Paciente", "👥 Novo Profissional"])
            
            with tab_cad_paciente:
                st.subheader("Ficha de Cadastro de Paciente")
                with st.form("form_cad_pac"):
                    pac_nome = st.text_input("Nome Completo do Paciente")
                    pac_idade = st.number_input("Idade", min_value=0, max_value=120, value=7)
                    pac_diag = st.text_input("Diagnóstico (Ex: TEA, TDAH, etc.)")
                    
                    st.markdown("---")
                    st.write("**Dados de Contato e Faturamento**")
                    pac_plano = st.text_input("Plano de Saúde / Convênio")
                    pac_pai = st.text_input("Nome Completo do Pai")
                    pac_mae = st.text_input("Nome Completo da Mãe")
                    pac_tel = st.text_input("Telefone para Contato")
                    pac_email = st.text_input("E-mail")
                    pac_end = st.text_input("Endereço Completo")
                    
                    st.markdown("---")
                    st.write("**Perfil Sensorial e Clínico**")
                    pac_auditiva = st.checkbox("Hipersensibilidade Auditiva")
                    pac_visual = st.checkbox("Hipersensibilidade Visual")
                    pac_verbal = st.checkbox("Paciente Não-Verbal")
                    pac_sessoes = st.number_input("Sessões Autorizadas (Pacote)", min_value=0, max_value=500, value=20)
                    
                    if st.form_submit_button("Cadastrar Paciente ✅"):
                        if not pac_nome or not pac_diag:
                            st.warning("Preencha ao menos o nome e o diagnóstico.")
                        else:
                            status, resp = post_data("patients", {
                                "nome": pac_nome, "idade": pac_idade, "diagnostico": pac_diag,
                                "hip_auditiva": pac_auditiva, "hip_visual": pac_visual, "nao_verbal": pac_verbal,
                                "sessoes_autorizadas": pac_sessoes, "plano_saude": pac_plano,
                                "nome_pai": pac_pai, "nome_mae": pac_mae, "telefone": pac_tel, "email": pac_email,
                                "endereco": pac_end
                            })
                            if status == 200:
                                st.success("Paciente cadastrado com sucesso!")
                                st.rerun()
                            else:
                                st.error("Erro ao cadastrar paciente.")
                                
            with tab_cad_profissional:
                st.subheader("Ficha de Cadastro de Profissional")
                with st.form("form_cad_prof"):
                    prof_user = st.text_input("Nome de Usuário (login)", placeholder="Ex: joao.terapeuta")
                    prof_nome = st.text_input("Nome Completo")
                    prof_esp = st.selectbox("Especialidade", ["Análise do Comportamento (ABA)", "Terapia Ocupacional", "Fonoaudiologia", "Psicopedagogia"])
                    prof_reg = st.text_input("Registro do Conselho (Ex: CRP 06/12345)")
                    
                    st.markdown("---")
                    st.write("**Dados de Contato**")
                    prof_tel = st.text_input("Telefone")
                    prof_email = st.text_input("E-mail")
                    prof_end = st.text_input("Endereço Residencial")
                    
                    if st.form_submit_button("Cadastrar Profissional ✅"):
                        if not prof_user or not prof_nome or not prof_reg:
                            st.warning("Preencha usuário, nome completo e registro do conselho.")
                        else:
                            status, resp = post_data("professionals", {
                                "username": prof_user, "nome_completo": prof_nome, "especialidade": prof_esp,
                                "registro_conselho": prof_reg, "telefone": prof_tel, "email": prof_email,
                                "endereco": prof_end
                            })
                            if status == 200:
                                st.success("Profissional cadastrado com sucesso!")
                                st.rerun()
                            else:
                                st.error(resp.get("detail", "Erro ao cadastrar profissional."))
