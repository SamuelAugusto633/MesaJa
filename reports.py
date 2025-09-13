# back/reports.py

from fpdf import FPDF
from datetime import date, timedelta
from sqlalchemy.orm import Session
import crud

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 14)
        # O título será definido em cada função para ser específico
    
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

def gerar_relatorio_diario_pdf(db: Session):
    hoje = date.today()
    
    # --- BUSCAR DADOS (CORRIGIDO) ---
    clientes_do_dia = crud.listar_clientes_do_dia(db, dia=hoje)
    clientes_atendidos_hoje = [c for c in clientes_do_dia if c.status == 'atendido' and c.horario_atendimento]
    clientes_cancelados_hoje = len([c for c in clientes_do_dia if c.status == 'cancelado']) # <-- CORREÇÃO AQUI

    # --- CÁLCULO DO TEMPO MÉDIO DE ESPERA ---
    tempo_medio_espera = 0
    if clientes_atendidos_hoje:
        total_espera_segundos = sum((c.horario_atendimento - c.horario_chegada).total_seconds() for c in clientes_atendidos_hoje)
        tempo_medio_espera = round((total_espera_segundos / len(clientes_atendidos_hoje)) / 60)

    # --- MONTAR PDF ---
    pdf = PDF()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'Relatório Diário de Atividade - MesaJa', 0, 1, 'C')
    pdf.ln(5)

    # RESUMO (CORRIGIDO)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Resumo do Dia', 0, 1, 'L')
    pdf.set_font('Arial', '', 11)
    pdf.cell(0, 8, f"Data do Relatório: {hoje.strftime('%d/%m/%Y')}", 0, 1)
    pdf.cell(0, 8, f"- Total de Clientes na Fila Hoje: {len(clientes_do_dia)}", 0, 1) # <-- NOME PADRONIZADO
    pdf.cell(0, 8, f"- Total de Clientes Atendidos: {len(clientes_atendidos_hoje)}", 0, 1)
    pdf.cell(0, 8, f"- Total de Desistências: {clientes_cancelados_hoje}", 0, 1) # <-- LINHA ADICIONADA

    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 8, f"- Tempo Médio de Espera: {tempo_medio_espera} minutos", 0, 1)
    pdf.ln(10)

    # TABELA DE CLIENTES
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Registo de Clientes na Fila', 0, 1, 'L')
    
    if not clientes_do_dia:
        pdf.set_font('Arial', 'I', 11)
        pdf.cell(0, 10, "Nenhuma atividade de clientes registada hoje.", 0, 1)
    else:
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(80, 10, 'Nome do Cliente', 1, 0, 'C')
        pdf.cell(30, 10, 'Grupo', 1, 0, 'C')
        pdf.cell(40, 10, 'Horário Chegada', 1, 0, 'C')
        pdf.cell(30, 10, 'Status', 1, 1, 'C')
        
        pdf.set_font('Arial', '', 10)
        for cliente in clientes_do_dia:
            horario_chegada_str = cliente.horario_chegada.strftime('%H:%M:%S')
            status_str = cliente.status.capitalize()
            pdf.cell(80, 10, cliente.nome_cliente, 1, 0)
            pdf.cell(30, 10, str(cliente.tamanho_grupo), 1, 0, 'C')
            pdf.cell(40, 10, horario_chegada_str, 1, 0, 'C')
            pdf.cell(30, 10, status_str, 1, 1, 'C')

    # SALVAR PDF
    nome_ficheiro = f"relatorio_diario_{hoje.strftime('%Y_%m_%d')}.pdf"
    caminho_completo = f"relatorios/{nome_ficheiro}"
    import os
    os.makedirs("relatorios", exist_ok=True)
    pdf.output(caminho_completo)
    
    return caminho_completo

def gerar_relatorio_semanal_pdf(db: Session):
    hoje = date.today()
    data_inicio = hoje - timedelta(days=6)
    
    clientes_semana = crud.listar_clientes_da_semana(db, hoje=hoje)
    clientes_atendidos_semana = [c for c in clientes_semana if c.status == 'atendido' and c.horario_atendimento]
    clientes_cancelados_semana = len([c for c in clientes_semana if c.status == 'cancelado'])

    tempo_medio_espera = 0
    if clientes_atendidos_semana:
        total_espera_segundos = sum((c.horario_atendimento - c.horario_chegada).total_seconds() for c in clientes_atendidos_semana)
        tempo_medio_espera = round((total_espera_segundos / len(clientes_atendidos_semana)) / 60)

    pdf = PDF()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'Relatório Semanal de Atividade - MesaJa', 0, 1, 'C')
    pdf.ln(5)

    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Resumo da Semana', 0, 1, 'L')
    pdf.set_font('Arial', '', 11)
    pdf.cell(0, 8, f"Período: {data_inicio.strftime('%d/%m/%Y')} a {hoje.strftime('%d/%m/%Y')}", 0, 1)
    pdf.cell(0, 8, f"- Total de Clientes na Fila Durante a Semana: {len(clientes_semana)}", 0, 1) # <-- NOME PADRONIZADO
    pdf.cell(0, 8, f"- Total de Clientes Atendidos: {len(clientes_atendidos_semana)}", 0, 1)
    pdf.cell(0, 8, f"- Total de Desistências: {clientes_cancelados_semana}", 0, 1) # <-- JÁ ESTAVA CORRETO
    
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 8, f"- Tempo Médio de Espera: {tempo_medio_espera} minutos", 0, 1)
    pdf.ln(10)

    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Registo de Clientes na Semana', 0, 1, 'L')

    if not clientes_semana:
        pdf.set_font('Arial', 'I', 11)
        pdf.cell(0, 10, "Nenhuma atividade de clientes registada na semana.", 0, 1)
    else:
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(60, 10, 'Cliente', 1, 0, 'C')
        pdf.cell(20, 10, 'Grupo', 1, 0, 'C')
        pdf.cell(30, 10, 'Data', 1, 0, 'C')
        pdf.cell(30, 10, 'Chegada', 1, 0, 'C')
        pdf.cell(40, 10, 'Status', 1, 1, 'C')
        
        pdf.set_font('Arial', '', 9)
        for cliente in clientes_semana:
            data_chegada_str = cliente.horario_chegada.strftime('%d/%m')
            horario_chegada_str = cliente.horario_chegada.strftime('%H:%M')
            status_str = cliente.status.capitalize()
            pdf.cell(60, 10, cliente.nome_cliente, 1, 0)
            pdf.cell(20, 10, str(cliente.tamanho_grupo), 1, 0, 'C')
            pdf.cell(30, 10, data_chegada_str, 1, 0, 'C')
            pdf.cell(30, 10, horario_chegada_str, 1, 0, 'C')
            pdf.cell(40, 10, status_str, 1, 1, 'C')

    nome_ficheiro = f"relatorio_semanal_{hoje.strftime('%Y_%m_%d')}.pdf"
    caminho_completo = f"relatorios/{nome_ficheiro}"
    import os
    os.makedirs("relatorios", exist_ok=True)
    pdf.output(caminho_completo)
    
    return caminho_completo

def gerar_relatorio_personalizado_pdf(db: Session, data_inicio: date, data_fim: date):
    
    clientes_periodo = crud.listar_clientes_por_periodo(db, data_inicio=data_inicio, data_fim=data_fim)
    clientes_atendidos = [c for c in clientes_periodo if c.status == 'atendido' and c.horario_atendimento]
    clientes_cancelados = len([c for c in clientes_periodo if c.status == 'cancelado'])

    tempo_medio_espera = 0
    if clientes_atendidos:
        total_espera_segundos = sum((c.horario_atendimento - c.horario_chegada).total_seconds() for c in clientes_atendidos)
        tempo_medio_espera = round((total_espera_segundos / len(clientes_atendidos)) / 60)

    pdf = PDF()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'Relatório Personalizado de Atividade - MesaJa', 0, 1, 'C')
    pdf.ln(5)

    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Resumo do Período', 0, 1, 'L')
    pdf.set_font('Arial', '', 11)
    pdf.cell(0, 8, f"Período: {data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}", 0, 1)
    pdf.cell(0, 8, f"- Total de Clientes na Fila No Periodo Escolhido: {len(clientes_periodo)}", 0, 1)
    pdf.cell(0, 8, f"- Total de Clientes Atendidos: {len(clientes_atendidos)}", 0, 1)
    pdf.cell(0, 8, f"- Total de Desistências: {clientes_cancelados}", 0, 1)
    
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 8, f"- Tempo Médio de Espera: {tempo_medio_espera} minutos", 0, 1)
    pdf.ln(10)

    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Registo de Clientes no Período', 0, 1, 'L')

    if not clientes_periodo:
        pdf.set_font('Arial', 'I', 11)
        pdf.cell(0, 10, "Nenhuma atividade de clientes registada no período selecionado.", 0, 1)
    else:
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(60, 10, 'Cliente', 1, 0, 'C')
        pdf.cell(20, 10, 'Grupo', 1, 0, 'C')
        pdf.cell(30, 10, 'Data', 1, 0, 'C')
        pdf.cell(30, 10, 'Chegada', 1, 0, 'C')
        pdf.cell(40, 10, 'Status', 1, 1, 'C')
        
        pdf.set_font('Arial', '', 9)
        for cliente in clientes_periodo:
            data_chegada_str = cliente.horario_chegada.strftime('%d/%m/%y')
            horario_chegada_str = cliente.horario_chegada.strftime('%H:%M')
            status_str = cliente.status.capitalize()
            pdf.cell(60, 10, cliente.nome_cliente, 1, 0)
            pdf.cell(20, 10, str(cliente.tamanho_grupo), 1, 0, 'C')
            pdf.cell(30, 10, data_chegada_str, 1, 0, 'C')
            pdf.cell(30, 10, horario_chegada_str, 1, 0, 'C')
            pdf.cell(40, 10, status_str, 1, 1, 'C')

    nome_ficheiro = f"relatorio_personalizado_{data_inicio.strftime('%Y%m%d')}_a_{data_fim.strftime('%Y%m%d')}.pdf"
    caminho_completo = f"relatorios/{nome_ficheiro}"
    import os
    os.makedirs("relatorios", exist_ok=True)
    pdf.output(caminho_completo)
    
    return caminho_completo