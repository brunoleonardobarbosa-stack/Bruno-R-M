from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime
from fpdf import FPDF
import io
import os

from . import models, database

database.init_db()
app = FastAPI(title="RM Comportamental API - Sistema Clínico Avançado")

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Rotas para Setup de Mock Data Iniciais ---
@app.post("/setup")
def setup_initial_data(db: Session = Depends(get_db)):
    if db.query(models.User).first():
        return {"msg": "Banco já possui dados."}

    u1 = models.User(username="admin", hashed_password="hashed_pass", role=models.RoleEnum.ADMIN)
    u2 = models.User(username="ana", hashed_password="hashed_pass", role=models.RoleEnum.TERAPEUTA)
    db.add_all([u1, u2])

    s1 = models.ResourceRoom(name="Consultório 01")
    s2 = models.ResourceRoom(name="Sala de Integração Sensorial (IS)")
    db.add_all([s1, s2])

    sp1 = models.Specialty(name="Análise do Comportamento (ABA)")
    sp2 = models.Specialty(name="Terapia Ocupacional")
    sp3 = models.Specialty(name="Fonoaudiologia")
    sp4 = models.Specialty(name="Psicopedagogia")
    db.add_all([sp1, sp2, sp3, sp4])

    p1 = models.Patient(name="João Silva", age=7, diagnosis="TEA", hip_auditiva=True, nao_verbal=True, sessions_authorized=40, sessions_used=15)
    p2 = models.Patient(name="Maria Souza", age=9, diagnosis="TDAH", hip_visual=True, sessions_authorized=20, sessions_used=18)
    db.add_all([p1, p2])
    db.commit()
    
    g1 = models.Goal(patient_id=p1.id, description="Contato visual sustentado por 3s", progress=60)
    db.add(g1)
    
    d1 = models.Document(patient_id=p1.id, title="Laudo Neuropediatra 2026.pdf", upload_date=datetime.now().strftime("%Y-%m-%d"), file_content="[ARQUIVO PDF ASSINADO]")
    db.add(d1)
    db.commit()

    return {"msg": "Setup inicial concluído com sucesso."}


# --- PATIENTS ---
@app.get("/patients")
def get_patients(db: Session = Depends(get_db)):
    patients = db.query(models.Patient).all()
    return [
        {
            "id": p.id, "nome": p.name, "idade": p.age, "diagnostico": p.diagnosis,
            "hip_auditiva": p.hip_auditiva, "hip_visual": p.hip_visual, "nao_verbal": p.nao_verbal,
            "sessoes_autorizadas": p.sessions_authorized, "sessoes_usadas": p.sessions_used,
            "plano_saude": p.health_insurance,
            "nome_pai": p.father_name,
            "nome_mae": p.mother_name,
            "telefone": p.phone,
            "email": p.email,
            "endereco": p.address
        } for p in patients
    ]

@app.post("/patients")
def create_patient(data: dict, db: Session = Depends(get_db)):
    new_patient = models.Patient(
        name=data["nome"], age=data["idade"], diagnosis=data["diagnostico"],
        hip_auditiva=data.get("hip_auditiva", False), 
        hip_visual=data.get("hip_visual", False),
        nao_verbal=data.get("nao_verbal", False),
        sessions_authorized=data.get("sessoes_autorizadas", 0),
        health_insurance=data.get("plano_saude"),
        father_name=data.get("nome_pai"),
        mother_name=data.get("nome_mae"),
        phone=data.get("telefone"),
        email=data.get("email"),
        address=data.get("endereco")
    )
    db.add(new_patient)
    db.commit()
    return {"msg": "Paciente salvo!"}

# --- APPOINTMENTS (Smart Scheduling) ---
@app.get("/appointments")
def get_appointments(db: Session = Depends(get_db)):
    apps = db.query(models.Appointment).all()
    return [
        {"paciente": a.patient.name, "terapeuta": a.therapist.username, "sala": a.room.name, "data": a.date_str, "hora": a.time_str} for a in apps
    ]

@app.post("/appointments")
def create_appointment(data: dict, db: Session = Depends(get_db)):
    patient = db.query(models.Patient).filter(models.Patient.name == data["paciente"]).first()
    therapist = db.query(models.User).filter(models.User.username == data["terapeuta"]).first()
    room = db.query(models.ResourceRoom).filter(models.ResourceRoom.name == data["sala"]).first()

    if not all([patient, therapist, room]):
        raise HTTPException(status_code=400, detail="Entidades inválidas.")

    conflict_room = db.query(models.Appointment).filter(
        models.Appointment.room_id == room.id, models.Appointment.date_str == data["data"], models.Appointment.time_str == data["hora"]
    ).first()
    if conflict_room: raise HTTPException(status_code=400, detail="Sala ocupada neste horário!")

    conflict_therapist = db.query(models.Appointment).filter(
        models.Appointment.therapist_id == therapist.id, models.Appointment.date_str == data["data"], models.Appointment.time_str == data["hora"]
    ).first()
    if conflict_therapist: raise HTTPException(status_code=400, detail="Terapeuta indisponível!")

    new_app = models.Appointment(
        patient_id=patient.id, therapist_id=therapist.id, room_id=room.id,
        date_str=data["data"], time_str=data["hora"]
    )
    db.add(new_app)
    db.commit()
    return {"msg": "Agendamento confirmado!"}

# --- GOALS (METAS ABA) ---
@app.get("/goals")
def get_goals(db: Session = Depends(get_db)):
    goals = db.query(models.Goal).all()
    return [{"id": g.id, "paciente": g.patient.name, "meta": g.description, "status": g.status, "progresso": g.progress} for g in goals]

@app.post("/goals")
def create_goal(data: dict, db: Session = Depends(get_db)):
    patient = db.query(models.Patient).filter(models.Patient.name == data["paciente"]).first()
    new_goal = models.Goal(patient_id=patient.id, description=data["meta"])
    db.add(new_goal)
    db.commit()
    return {"msg": "Meta salva!"}

# --- IA CLINIC ASSISTANT (SOAP NOTES) ---
@app.post("/generate-draft")
def generate_draft(data: dict):
    # Simulação determinística de um Modelo de IA (LLM) que escreve o texto com base nas métricas
    engajamento = data.get("engajamento", 5)
    crises = data.get("crises", 0)
    area = data.get("area", "Terapia")
    
    texto = f"Sessão de {area} realizada. O paciente demonstrou um nível de engajamento "
    if engajamento >= 8:
        texto += "excelente, participando ativamente das propostas e mantendo atenção compartilhada sustentada. "
    elif engajamento >= 5:
        texto += "adequado, necessitando de mediação ocasional para concluir as tarefas. "
    else:
        texto += "baixo, apresentando dificuldade de regulação e dispersão frequente. "
        
    if crises == 0:
        texto += "Nenhum comportamento inadequado ou crise de regulação foi observado durante o atendimento, denotando boa estabilidade emocional hoje."
    else:
        texto += f"Foram registradas {crises} ocorrências de comportamento inadequado/crise de desregulação, que foram manejadas pela equipe conforme o protocolo ABA."
        
    return {"draft": texto}

class ClinicalPDF(FPDF):
    def header(self):
        # Logo RM Comportamental
        logo_path = os.path.join(os.path.dirname(__file__), "logo.jpg")
        if os.path.exists(logo_path):
            self.image(logo_path, 10, 8, 25) # x=10, y=8, w=25
            self.set_x(40) # Mover para a direita para não sobrepor o logo
            
        self.set_font('helvetica', 'B', 16)
        self.set_text_color(42, 157, 143) # #2a9d8f
        
        # Alinhar à esquerda se houver logo, senão no centro
        align_mode = 'L' if os.path.exists(logo_path) else 'C'
        self.cell(0, 10, 'RM Comportamental - Relatorio de Evolucao Clinica', border=False, new_x="LMARGIN", new_y="NEXT", align=align_mode)
        
        if os.path.exists(logo_path):
            self.set_x(40)
            
        self.set_font('helvetica', '', 9)
        self.set_text_color(100, 100, 100)
        self.cell(0, 5, 'Sistema de Registro Clinico e Compliance EVV', border=False, new_x="LMARGIN", new_y="NEXT", align=align_mode)
        self.ln(12)

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f'Pagina {self.page_no()}/{{nb}} | RM Comportamental Cloud', align='C')

# --- CLINICAL EVOLUTIONS ---
@app.get("/evolutions")
def get_evolutions(db: Session = Depends(get_db)):
    evs = db.query(models.ClinicalEvolution).all()
    return [
        {"id": e.id, "paciente": e.patient.name, "data": e.date_str, "area": e.area, "metrics": e.metrics, 
         "ai_draft": e.ai_draft_text, "signature": e.guardian_signature} for e in evs
    ]

@app.get("/evolutions/{evolution_id}/pdf")
def get_evolution_pdf(evolution_id: int, db: Session = Depends(get_db)):
    evolution = db.query(models.ClinicalEvolution).filter(models.ClinicalEvolution.id == evolution_id).first()
    if not evolution:
        raise HTTPException(status_code=404, detail="Evolucao nao encontrada.")
    
    pdf = ClinicalPDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    
    # Titulo da evolucao
    pdf.set_font("helvetica", "B", 12)
    pdf.set_text_color(43, 45, 66) # #2b2d42
    pdf.cell(0, 8, f"Detalhamento do Atendimento - ID #{evolution.id}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    
    # Informacoes do Paciente
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(40, 6, "Paciente:")
    pdf.set_font("helvetica", "", 10)
    pdf.cell(0, 6, evolution.patient.name, new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(40, 6, "Idade / Diagnostico:")
    pdf.set_font("helvetica", "", 10)
    pdf.cell(0, 6, f"{evolution.patient.age} anos | {evolution.patient.diagnosis}", new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(40, 6, "Data da Sessao:")
    pdf.set_font("helvetica", "", 10)
    pdf.cell(0, 6, evolution.date_str, new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(40, 6, "Area de Atendimento:")
    pdf.set_font("helvetica", "", 10)
    pdf.cell(0, 6, evolution.area, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    
    # Metricas da Sessao
    pdf.set_font("helvetica", "B", 11)
    pdf.set_text_color(42, 157, 143)
    pdf.cell(0, 8, "Metricas Registradas (Mobile)", new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(43, 45, 66)
    
    metrics = evolution.metrics or {}
    pdf.set_font("helvetica", "", 10)
    pdf.cell(60, 6, f"- Nivel de Engajamento: {metrics.get('engajamento_score', 'N/A')}/10")
    pdf.cell(0, 6, f"- Ocorrencias de Crises: {metrics.get('crises_registradas', 0)}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    
    # Relatorio Clinico (SOAP)
    pdf.set_font("helvetica", "B", 11)
    pdf.set_text_color(42, 157, 143)
    pdf.cell(0, 8, "Relatorio Clinico e Conduta (SOAP)", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", "", 10)
    pdf.set_text_color(43, 45, 66)
    
    # Remover caracteres nao-latin1 se existirem
    relatorio = evolution.ai_draft_text or "Nenhum relatorio adicionado."
    # Garantir codificacao segura para PDF default do fpdf (latin-1)
    relatorio = relatorio.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 6, relatorio)
    pdf.ln(10)
    
    # Assinatura Digital / EVV
    pdf.set_font("helvetica", "B", 11)
    pdf.set_text_color(42, 157, 143)
    pdf.cell(0, 8, "Validacao de Visita Eletronica (EVV)", new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_font("helvetica", "", 10)
    pdf.set_text_color(43, 45, 66)
    
    sig = evolution.guardian_signature or "NAO ASSINADO"
    if sig.startswith("data:image/"):
        try:
            import base64
            from PIL import Image
            import io
            header, encoded = sig.split(",", 1)
            img_data = base64.b64decode(encoded)
            img_sig = Image.open(io.BytesIO(img_data))
            
            pdf.cell(50, 6, "Assinatura Digital (EVV):")
            # Insere a imagem da assinatura no PDF
            pdf.image(img_sig, x=pdf.get_x(), y=pdf.get_y() - 3, w=45, h=12)
            pdf.ln(14)
        except Exception:
            pdf.cell(0, 6, "[Erro ao renderizar assinatura canvas]", new_x="LMARGIN", new_y="NEXT")
    else:
        pdf.cell(50, 6, "Assinatura do Familiar:")
        pdf.set_font("helvetica", "B", 10)
        sig_clean = sig.encode('latin-1', 'replace').decode('latin-1')
        pdf.cell(0, 6, sig_clean, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(5)
        
    pdf.set_font("helvetica", "", 8)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 6, f"Assinatura colhida eletronicamente via aplicativo RM Comportamental em {evolution.date_str}.", new_x="LMARGIN", new_y="NEXT")
    
    # Gerar como string de bytes binarios (fpdf2 usa output(dest='S') ou output() retornando bytes dependendo da versao, dest='S' eh compativel)
    pdf_bytes = pdf.output()
    
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=evolucao_{evolution.id}.pdf"}
    )

@app.post("/evolutions")
def create_evolution(data: dict, db: Session = Depends(get_db)):
    patient = db.query(models.Patient).filter(models.Patient.name == data["paciente"]).first()
    new_ev = models.ClinicalEvolution(
        patient_id=patient.id, date_str=data["data"], area=data["area"], metrics=data["metrics"],
        ai_draft_text=data.get("ai_draft"), guardian_signature=data.get("signature")
    )
    db.add(new_ev)
    patient.sessions_used += 1
    db.commit()
    return {"msg": "Evolução salva!"}

# --- DOCUMENT VAULT ---
@app.get("/documents")
def get_documents(db: Session = Depends(get_db)):
    docs = db.query(models.Document).all()
    return [{"paciente": d.patient.name, "titulo": d.title, "data": d.upload_date, "conteudo": d.file_content} for d in docs]

@app.post("/documents")
def create_document(data: dict, db: Session = Depends(get_db)):
    patient = db.query(models.Patient).filter(models.Patient.name == data["paciente"]).first()
    new_doc = models.Document(
        patient_id=patient.id, title=data["title"], upload_date=datetime.now().strftime("%Y-%m-%d"),
        file_content=data.get("content", "PDF/DOC_SIMULADO")
    )
    db.add(new_doc)
    db.commit()
    return {"msg": "Documento armazenado com segurança no cofre!"}

# --- PROFESSIONALS ---
@app.get("/professionals")
def get_professionals(db: Session = Depends(get_db)):
    profs = db.query(models.User).filter(models.User.role != models.RoleEnum.FAMILIA).all()
    return [
        {
            "id": u.id,
            "username": u.username,
            "role": u.role,
            "nome_completo": u.full_name,
            "endereco": u.address,
            "telefone": u.phone,
            "email": u.email,
            "registro_conselho": u.council_registry,
            "especialidade": u.specialty
        } for u in profs
    ]

@app.post("/professionals")
def create_professional(data: dict, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.username == data["username"]).first()
    if existing:
        raise HTTPException(status_code=400, detail="Nome de usuário já cadastrado!")
        
    new_user = models.User(
        username=data["username"],
        hashed_password="hashed_pass",
        role=models.RoleEnum.TERAPEUTA,
        full_name=data["nome_completo"],
        address=data["endereco"],
        phone=data["telefone"],
        email=data["email"],
        council_registry=data["registro_conselho"],
        specialty=data["especialidade"]
    )
    db.add(new_user)
    db.commit()
    return {"msg": "Profissional cadastrado com sucesso!"}

# --- SPECIALTIES ---
@app.get("/specialties")
def get_specialties(db: Session = Depends(get_db)):
    specs = db.query(models.Specialty).all()
    return [{"id": s.id, "nome": s.name} for s in specs]

@app.post("/specialties")
def create_specialty(data: dict, db: Session = Depends(get_db)):
    existing = db.query(models.Specialty).filter(models.Specialty.name == data["nome"]).first()
    if existing:
        return {"msg": "Especialidade já cadastrada."}
    new_spec = models.Specialty(name=data["nome"])
    db.add(new_spec)
    db.commit()
    return {"msg": "Especialidade cadastrada com sucesso!"}

# --- ROOMS ---
@app.get("/rooms")
def get_rooms(db: Session = Depends(get_db)):
    rooms = db.query(models.ResourceRoom).all()
    return [{"id": r.id, "nome": r.name} for r in rooms]

@app.post("/rooms")
def create_room(data: dict, db: Session = Depends(get_db)):
    existing = db.query(models.ResourceRoom).filter(models.ResourceRoom.name == data["nome"]).first()
    if existing:
        return {"msg": "Sala já cadastrada."}
    new_room = models.ResourceRoom(name=data["nome"])
    db.add(new_room)
    db.commit()
    return {"msg": "Sala cadastrada com sucesso!"}

@app.get("/metadata")
def get_metadata(db: Session = Depends(get_db)):
    therapists = [u.username for u in db.query(models.User).filter(models.User.role != models.RoleEnum.FAMILIA).all()]
    rooms = [r.name for r in db.query(models.ResourceRoom).all()]
    specialties = [s.name for s in db.query(models.Specialty).all()]
    return {"therapists": therapists, "rooms": rooms, "specialties": specialties}
