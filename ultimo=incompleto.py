# app_corrigido_v4_COMPLETO.py - VERSÃO FINAL COM TODAS AS CORREÇÕES
import streamlit as st
import pandas as pd
import database
from session_state import init_session_state
from auto_save import salvar_tudo
from models import Turma, Professor, Disciplina, Sala, DIAS_SEMANA, Aula
import io
import traceback
from datetime import datetime, time
import random

# ============================================
# CONFIGURAÇÃO DE PÁGINA
# ============================================
st.set_page_config(page_title="Escola Timetable", layout="wide")
st.title("🕒 Gerador Inteligente de Grade Horária")

# ============================================
# VERIFICAÇÃO DE ALGORITMOS
# ============================================
ALGORITMOS_DISPONIVEIS = True
try:
    # Tentar importar algoritmo ULTRA primeiro
    from simple_scheduler_ultra import SimpleGradeHoraria as SimpleGradeHorariaUltra
    ALGORITMO_DISPONIVEL = "ULTRA-CORRIGIDO"
    st.sidebar.success("✅ Algoritmo ULTRA-CORRIGIDO disponível")
except ImportError:
    try:
        # Fallback para algoritmo corrigido
        from simple_scheduler_final import SimpleGradeHoraria
        ALGORITMO_DISPONIVEL = "CORRIGIDO"
        st.sidebar.warning("⚠️ Usando algoritmo CORRIGIDO")
    except ImportError:
        try:
            # Fallback para algoritmo original
            from simple_scheduler import SimpleGradeHoraria
            ALGORITMO_DISPONIVEL = "ORIGINAL"
            st.sidebar.error("⚠️ Usando algoritmo ORIGINAL (pode ter problemas)")
        except ImportError:
            ALGORITMOS_DISPONIVEIS = False
            ALGORITMO_DISPONIVEL = "NENHUM"
            st.sidebar.error("❌ Nenhum algoritmo disponível")
            
            class SimpleGradeHoraria:
                def __init__(self, *args, **kwargs):
                    self.turmas = []
                    self.professores = []
                    self.disciplinas = []
                    self.salas = []
                
                def gerar_grade(self):
                    st.error("❌ Nenhum algoritmo de geração disponível!")
                    return []

# ============================================
# INICIALIZAÇÃO
# ============================================
try:
    init_session_state()
    st.success("✅ Sistema inicializado com sucesso!")
except Exception as e:
    st.error(f"❌ Erro na inicialização: {str(e)}")
    st.code(traceback.format_exc())
    if st.button("🔄 Resetar Banco de Dados"):
        database.resetar_banco()
        st.rerun()
    st.stop()

# ============================================
# CONSTANTES E LIMITES
# ============================================
LIMITE_HORAS_EFII = 25  # horas semanais máximas para professores de EF II
LIMITE_HORAS_EM = 35    # horas semanais máximas para professores de EM

# ============================================
# FUNÇÕES AUXILIARES CORRIGIDAS
# ============================================

def obter_grupo_seguro(objeto, opcoes=["A", "B", "AMBOS"]):
    """Obtém o grupo de um objeto de forma segura"""
    try:
        if hasattr(objeto, 'grupo'):
            grupo = objeto.grupo
            if grupo in opcoes:
                return grupo
        return "A"
    except:
        return "A"

def obter_segmento_turma(turma_nome):
    """Determina o segmento da turma baseado no nome"""
    if not turma_nome:
        return "EF_II"
    
    turma_nome_lower = turma_nome.lower()
    
    # Verificar se é EM
    if 'em' in turma_nome_lower:
        return "EM"
    # Verificar se é EF II
    elif any(x in turma_nome_lower for x in ['6', '7', '8', '9', 'ano', 'ef']):
        return "EF_II"
    else:
        try:
            if turma_nome_lower[0].isdigit():
                return "EF_II"
            else:
                return "EM"
        except:
            return "EF_II"

def obter_segmento_professor(professor):
    """Determina o segmento principal do professor baseado nas disciplinas que ministra"""
    if not hasattr(professor, 'disciplinas') or not professor.disciplinas:
        return "AMBOS"
    
    # Verificar disciplinas do professor
    tem_efii = False
    tem_em = False
    
    for disc_nome in professor.disciplinas:
        # Encontrar disciplina correspondente
        for disc in st.session_state.disciplinas:
            if disc.nome == disc_nome:
                # Verificar turmas desta disciplina
                for turma_nome in disc.turmas:
                    segmento = obter_segmento_turma(turma_nome)
                    if segmento == "EF_II":
                        tem_efii = True
                    elif segmento == "EM":
                        tem_em = True
    
    if tem_efii and tem_em:
        return "AMBOS"
    elif tem_efii:
        return "EF_II"
    elif tem_em:
        return "EM"
    else:
        return "AMBOS"

def obter_limite_horas_professor(professor):
    """Retorna o limite de horas semanais para o professor"""
    segmento = obter_segmento_professor(professor)
    
    if segmento == "EF_II":
        return LIMITE_HORAS_EFII
    elif segmento == "EM":
        return LIMITE_HORAS_EM
    else:
        # Para professores que dão aula em ambos, usar o limite maior
        return LIMITE_HORAS_EM

def calcular_horas_professor(professor, aulas):
    """Calcula horas semanais do professor baseado nas aulas"""
    total_horas = 0
    
    for aula in aulas:
        if obter_professor_aula(aula) == professor.nome:
            # Cada aula = 1 hora
            total_horas += 1
    
    return total_horas

def obter_horarios_turma(turma_nome):
    """Retorna os períodos disponíveis para a turma"""
    segmento = obter_segmento_turma(turma_nome)
    if segmento == "EM":
        return [1, 2, 3, 4, 5, 6, 7]  # 7 períodos para EM
    else:
        return [1, 2, 3, 4, 5]  # 5 períodos para EF II

def obter_horario_real(turma_nome, periodo):
    """Retorna o horário real formatado COM INTERVALO CORRETO"""
    segmento = obter_segmento_turma(turma_nome)
    
    if segmento == "EM":
        # Ensino Médio: 7 períodos com intervalo APÓS o 3º período
        horarios_em = {
            1: "07:00 - 07:50",
            2: "07:50 - 08:40", 
            3: "08:40 - 09:30",  # ÚLTIMO ANTES DO INTERVALO
            4: "09:50 - 10:40",  # PRIMEIRO APÓS INTERVALO
            5: "10:40 - 11:30",
            6: "11:30 - 12:20",
            7: "12:20 - 13:10"
        }
        return horarios_em.get(periodo, f"Período {periodo}")
    else:
        # EF II: 5 períodos com intervalo APÓS o 2º período
        horarios_efii = {
            1: "07:50 - 08:40",
            2: "08:40 - 09:30",  # ÚLTIMO ANTES DO INTERVALO
            3: "09:50 - 10:40",  # PRIMEIRO APÓS INTERVALO
            4: "10:40 - 11:30",
            5: "11:30 - 12:20"
        }
        return horarios_efii.get(periodo, f"Período {periodo}")

def obter_horario_real_time(turma_nome, periodo):
    """Retorna horário real como objetos time (inicio, fim)"""
    segmento = obter_segmento_turma(turma_nome)
    
    if segmento == "EM":
        horarios = {
            1: (time(7, 0), time(7, 50)),
            2: (time(7, 50), time(8, 40)), 
            3: (time(8, 40), time(9, 30)),
            4: (time(9, 50), time(10, 40)),
            5: (time(10, 40), time(11, 30)),
            6: (time(11, 30), time(12, 20)),
            7: (time(12, 20), time(13, 10))
        }
    else:  # EF_II
        horarios = {
            1: (time(7, 50), time(8, 40)),
            2: (time(8, 40), time(9, 30)),
            3: (time(9, 50), time(10, 40)),
            4: (time(10, 40), time(11, 30)),
            5: (time(11, 30), time(12, 20))
        }
    
    return horarios.get(periodo, (time(0, 0), time(0, 0)))

def obter_periodo_por_horario_real(turma_nome, horario_real):
    """Converte horário real para número do período baseado no segmento"""
    segmento = obter_segmento_turma(turma_nome)
    
    if segmento == "EM":
        # EM: 7 períodos
        horarios_em = {
            "07:00 - 07:50": 1,
            "07:50 - 08:40": 2,
            "08:40 - 09:30": 3,
            "09:50 - 10:40": 4,
            "10:40 - 11:30": 5,
            "11:30 - 12:20": 6,
            "12:20 - 13:10": 7
        }
        return horarios_em.get(horario_real, 0)
    else:
        # EF II: 5 períodos
        horarios_efii = {
            "07:50 - 08:40": 1,
            "08:40 - 09:30": 2,
            "09:50 - 10:40": 3,
            "10:40 - 11:30": 4,
            "11:30 - 12:20": 5
        }
        return horarios_efii.get(horario_real, 0)

def calcular_carga_maxima(serie):
    """Calcula a quantidade máxima de aulas semanais"""
    if not serie:
        return 25
    
    serie_lower = serie.lower()
    if 'em' in serie_lower or serie_lower in ['1em', '2em', '3em']:
        return 35  # EM: 7 aulas × 5 dias
    else:
        return 25  # EF II: 5 aulas × 5 dias

def converter_dia_para_semana(dia):
    """Converte dia do formato completo para abreviado"""
    if dia == "segunda": return "seg"
    elif dia == "terca": return "ter"
    elif dia == "quarta": return "qua"
    elif dia == "quinta": return "qui"
    elif dia == "sexta": return "sex"
    else: return dia

def converter_dia_para_completo(dia):
    """Converte dia do formato abreviado para completo"""
    if dia == "seg": return "segunda"
    elif dia == "ter": return "terca"
    elif dia == "qua": return "quarta"
    elif dia == "qui": return "quinta"
    elif dia == "sex": return "sexta"
    else: return dia

def converter_disponibilidade_para_semana(disponibilidade):
    """Converte conjunto de disponibilidade para formato DIAS_SEMANA"""
    convertido = []
    for dia in disponibilidade:
        dia_convertido = converter_dia_para_semana(dia)
        if dia_convertido in DIAS_SEMANA:
            convertido.append(dia_convertido)
    return convertido

def converter_disponibilidade_para_completo(disponibilidade):
    """Converte conjunto de disponibilidade para formato completo"""
    convertido = []
    for dia in disponibilidade:
        convertido.append(converter_dia_para_completo(dia))
    return convertido

# ============================================
# FUNÇÕES DE ACESSO SEGURO A AULAS
# ============================================

def obter_turma_aula(aula):
    """Obtém a turma de uma aula de forma segura"""
    if isinstance(aula, Aula):
        return aula.turma
    elif isinstance(aula, dict) and 'turma' in aula:
        return aula['turma']
    elif hasattr(aula, 'turma'):
        return aula.turma
    return None

def obter_disciplina_aula(aula):
    """Obtém a disciplina de uma aula de forma segura"""
    if isinstance(aula, Aula):
        return aula.disciplina
    elif isinstance(aula, dict) and 'disciplina' in aula:
        return aula['disciplina']
    elif hasattr(aula, 'disciplina'):
        return aula.disciplina
    return None

def obter_professor_aula(aula):
    """Obtém o professor de uma aula de forma segura"""
    if isinstance(aula, Aula):
        return aula.professor
    elif isinstance(aula, dict) and 'professor' in aula:
        return aula['professor']
    elif hasattr(aula, 'professor'):
        return aula.professor
    return None

def obter_dia_aula(aula):
    """Obtém o dia de uma aula de forma segura"""
    if isinstance(aula, Aula):
        return aula.dia
    elif isinstance(aula, dict) and 'dia' in aula:
        return aula['dia']
    elif hasattr(aula, 'dia'):
        return aula.dia
    return None

def obter_horario_aula(aula):
    """Obtém o número do horário de uma aula de forma segura"""
    if isinstance(aula, Aula):
        return aula.horario
    elif isinstance(aula, dict) and 'horario' in aula:
        return aula['horario']
    elif hasattr(aula, 'horario'):
        return aula.horario
    return None

def obter_horario_real_aula(aula):
    """Obtém o horário REAL de uma aula"""
    turma = obter_turma_aula(aula)
    horario_num = obter_horario_aula(aula)
    
    if turma and horario_num:
        return obter_horario_real(turma, horario_num)
    return None

def obter_segmento_aula(aula):
    """Obtém o segmento de uma aula de forma segura"""
    if isinstance(aula, Aula):
        return aula.segmento if hasattr(aula, 'segmento') else None
    elif isinstance(aula, dict) and 'segmento' in aula:
        return aula['segmento']
    elif hasattr(aula, 'segmento'):
        return aula.segmento
    return None

# ============================================
# FUNÇÕES PARA PROFESSORES POR DISCIPLINA
# ============================================

def obter_professores_para_disciplina(disciplina_nome, grupo=None):
    """Retorna lista de professores que podem ministrar uma disciplina"""
    professores_disponiveis = []
    
    for professor in st.session_state.professores:
        if disciplina_nome in professor.disciplinas:
            # Verificar se o grupo do professor é compatível
            if grupo:
                prof_grupo = obter_grupo_seguro(professor)
                if prof_grupo in [grupo, "AMBOS"]:
                    professores_disponiveis.append(professor)
            else:
                professores_disponiveis.append(professor)
    
    return professores_disponiveis

def calcular_disponibilidade_professor(professor):
    """Calcula disponibilidade semanal do professor em horas"""
    dias_disponiveis = len(professor.disponibilidade) if hasattr(professor, 'disponibilidade') else 0
    horarios_indisponiveis = len(professor.horarios_indisponiveis) if hasattr(professor, 'horarios_indisponiveis') else 0
    
    # Cada dia tem 7 períodos possíveis
    total_periodos = dias_disponiveis * 7
    periodos_disponiveis = total_periodos - horarios_indisponiveis
    
    return periodos_disponiveis

def verificar_professor_comprometido(professor, disciplina_nome, grupo):
    """Verifica se um professor está comprometido com outras disciplinas"""
    # Obter todas as disciplinas que o professor ministra
    disciplinas_prof = professor.disciplinas
    
    if disciplina_nome not in disciplinas_prof:
        return False  # Não ministra esta disciplina
    
    # Verificar se há outras disciplinas no mesmo grupo
    outras_disciplinas = [d for d in disciplinas_prof if d != disciplina_nome]
    
    if not outras_disciplinas:
        return False  # Só ministra esta disciplina
    
    # Verificar se outras disciplinas são do mesmo grupo
    for outra_disc_nome in outras_disciplinas:
        # Encontrar a disciplina
        for disc in st.session_state.disciplinas:
            if disc.nome == outra_disc_nome:
                disc_grupo = obter_grupo_seguro(disc)
                if disc_grupo == grupo:
                    return True  # Está comprometido com outra disciplina do mesmo grupo
    
    return False

# ============================================
# VERIFICAÇÃO DE CONFLITOS (CORRIGIDAS)
# ============================================

def verificar_conflitos_horarios(aulas):
    """Verifica se há horários sobrepostos na mesma turma considerando horários REAIS"""
    conflitos = []
    horarios_por_turma = {}
    aulas_por_disciplina_turma = {}
    
    for aula in aulas:
        turma = obter_turma_aula(aula)
        dia = obter_dia_aula(aula)
        horario_num = obter_horario_aula(aula)
        disciplina = obter_disciplina_aula(aula)
        
        if not turma or not dia or not horario_num or not disciplina:
            continue
        
        # Obter horário REAL
        hora_real = obter_horario_real(turma, horario_num)
        segmento = obter_segmento_turma(turma)
        
        # Chave baseada em horário REAL
        chave_horario = f"{turma}|{dia}|{hora_real}"
        
        if chave_horario not in horarios_por_turma:
            horarios_por_turma[chave_horario] = []
        
        # VERIFICAÇÃO 1: Conflito no mesmo horário REAL
        disciplinas_no_horario = [obter_disciplina_aula(a) for a in horarios_por_turma[chave_horario]]
        if disciplina in disciplinas_no_horario:
            # AULA REPETIDA - mesma disciplina já alocada neste horário REAL
            conflitos.append({
                'tipo': 'repeticao_mesmo_horario',
                'turma': turma,
                'dia': dia,
                'horario_real': hora_real,
                'horario_num': horario_num,
                'disciplina': disciplina,
                'chave': chave_horario,
                'segmento': segmento
            })
        else:
            horarios_por_turma[chave_horario].append(aula)
            
            if len(horarios_por_turma[chave_horario]) > 1:
                # CONFLITO DETECTADO! Horário sobreposto com disciplinas diferentes
                conflitos.append({
                    'tipo': 'sobreposicao',
                    'turma': turma,
                    'dia': dia,
                    'horario_real': hora_real,
                    'horario_num': horario_num,
                    'aulas': horarios_por_turma[chave_horario].copy(),
                    'disciplinas': [obter_disciplina_aula(a) for a in horarios_por_turma[chave_horario]],
                    'chave': chave_horario,
                    'segmento': segmento
                })
        
        # VERIFICAÇÃO 2: Aulas repetidas em excesso
        chave_disc_turma = f"{turma}|{disciplina}"
        
        if chave_disc_turma not in aulas_por_disciplina_turma:
            aulas_por_disciplina_turma[chave_disc_turma] = []
        
        aulas_por_disciplina_turma[chave_disc_turma].append(aula)
        
        # Obter carga semanal necessária
        carga_necessaria = 0
        for disc in st.session_state.disciplinas:
            if disc.nome == disciplina and turma in disc.turmas:
                carga_necessaria = disc.carga_semanal
                break
        
        if len(aulas_por_disciplina_turma[chave_disc_turma]) > carga_necessaria:
            conflitos.append({
                'tipo': 'excesso_aulas',
                'turma': turma,
                'disciplina': disciplina,
                'quantidade': len(aulas_por_disciplina_turma[chave_disc_turma]),
                'necessario': carga_necessaria,
                'chave': chave_disc_turma,
                'segmento': segmento
            })
    
    return conflitos

def verificar_professor_superposto(aulas):
    """Verifica se o mesmo professor tem aulas em horários REAIS sobrepostos"""
    superposicoes = []
    
    # Usar dicionário para agrupar por professor-dia-horario_real
    grupos = {}
    
    for aula in aulas:
        professor = obter_professor_aula(aula)
        dia = obter_dia_aula(aula)
        horario_num = obter_horario_aula(aula)
        turma = obter_turma_aula(aula)
        
        if not professor or not dia or not horario_num or not turma:
            continue
        
        # Obter horário REAL
        hora_real = obter_horario_real(turma, horario_num)
        
        # Chave única: professor + dia + horário REAL
        chave = f"{professor}|{dia}|{hora_real}"
        
        if chave not in grupos:
            grupos[chave] = []
        
        grupos[chave].append(aula)
    
    # Verificar grupos com mais de uma aula
    for chave, aulas_grupo in grupos.items():
        if len(aulas_grupo) > 1:
            professor, dia, hora_real = chave.split('|')
            
            # Obter informações das aulas
            turmas = [obter_turma_aula(a) for a in aulas_grupo]
            disciplinas = [obter_disciplina_aula(a) for a in aulas_grupo]
            segmentos = [obter_segmento_turma(t) for t in turmas]
            horarios_nums = [obter_horario_aula(a) for a in aulas_grupo]
            
            superposicoes.append({
                'professor': professor,
                'dia': dia,
                'horario_real': hora_real,
                'aulas': aulas_grupo.copy(),
                'turmas': turmas,
                'disciplinas': disciplinas,
                'segmentos': segmentos,
                'horarios_numericos': horarios_nums,
                'chave': chave,
                'quantidade': len(aulas_grupo)
            })
    
    return superposicoes

def analisar_superposicoes_por_horario_real(aulas):
    """Analisa superposições agrupando por horário REAL"""
    analise = {}
    
    for aula in aulas:
        professor = obter_professor_aula(aula)
        dia = obter_dia_aula(aula)
        horario_num = obter_horario_aula(aula)
        turma = obter_turma_aula(aula)
        
        if not all([professor, dia, horario_num, turma]):
            continue
        
        # Obter horário REAL
        hora_real = obter_horario_real(turma, horario_num)
        segmento = obter_segmento_turma(turma)
        
        chave = f"{professor}|{dia}|{hora_real}"
        
        if chave not in analise:
            analise[chave] = {
                'professor': professor,
                'dia': dia,
                'horario_real': hora_real,
                'aulas': [],
                'turmas': [],
                'segmentos': [],
                'horarios_numericos': []
            }
        
        analise[chave]['aulas'].append(aula)
        analise[chave]['turmas'].append(turma)
        analise[chave]['segmentos'].append(segmento)
        analise[chave]['horarios_numericos'].append(horario_num)
    
    # Filtrar apenas os que têm superposição
    superposicoes = {k: v for k, v in analise.items() if len(v['aulas']) > 1}
    
    return superposicoes

def verificar_limites_professores(aulas):
    """Verifica se algum professor excedeu o limite de horas"""
    problemas = []
    
    for professor in st.session_state.professores:
        horas_atual = calcular_horas_professor(professor, aulas)
        limite = obter_limite_horas_professor(professor)
        
        if horas_atual > limite:
            problemas.append({
                'professor': professor.nome,
                'horas_atual': horas_atual,
                'limite': limite,
                'segmento': obter_segmento_professor(professor)
            })
    
    return problemas

# ============================================
# FUNÇÃO: REMOVER AULAS REPETIDAS
# ============================================

def remover_aulas_repetidas(aulas):
    """Remove aulas repetidas da mesma disciplina para a mesma turma"""
    if not aulas:
        return aulas
    
    aulas_filtradas = []
    contador = {}
    
    for aula in aulas:
        turma = obter_turma_aula(aula)
        disciplina = obter_disciplina_aula(aula)
        
        if not turma or not disciplina:
            aulas_filtradas.append(aula)  # Mantém se não puder identificar
            continue
            
        chave = f"{turma}|{disciplina}"
        
        # Obter carga semanal necessária
        carga_necessaria = 0
        for disc in st.session_state.disciplinas:
            if disc.nome == disciplina and turma in disc.turmas:
                carga_necessaria = disc.carga_semanal
                break
        
        # Inicializar contador se não existir
        if chave not in contador:
            contador[chave] = 0
        
        # Adicionar apenas se não exceder a carga necessária
        if contador[chave] < carga_necessaria:
            aulas_filtradas.append(aula)
            contador[chave] += 1
        else:
            # Aula repetida - não adicionar
            continue
    
    return aulas_filtradas

# ============================================
# FUNÇÃO: CORREÇÃO ULTRA-EFICAZ (REMOVER CONFLITOS)
# ============================================

def corrigir_superposicoes_ultra(aulas, superposicoes):
    """
    Correção ULTRA-EFICAZ: Remove aulas conflitantes em vez de tentar mover
    Mantém apenas a primeira aula de cada conflito
    """
    if not superposicoes:
        return aulas
    
    # Identificar todas as aulas em conflito
    aulas_para_remover = set()
    relatorio = []
    
    for superposicao in superposicoes:
        professor = superposicao['professor']
        dia = superposicao['dia']
        horario_real = superposicao['horario_real']
        
        # Todas as aulas deste professor neste horário
        aulas_conflito = superposicao['aulas']
        
        # Manter apenas a PRIMEIRA aula, marcar as outras para remoção
        if len(aulas_conflito) > 1:
            manter_aula = aulas_conflito[0]
            mantida_info = f"{obter_disciplina_aula(manter_aula)} - {obter_turma_aula(manter_aula)}"
            
            # Encontrar índices das aulas para remover
            for i in range(1, len(aulas_conflito)):
                aula_para_remover = aulas_conflito[i]
                
                # Encontrar índice da aula para remover na lista original
                for idx, aula in enumerate(aulas):
                    if (obter_professor_aula(aula) == professor and
                        obter_dia_aula(aula) == dia and
                        obter_horario_real_aula(aula) == horario_real and
                        obter_disciplina_aula(aula) == obter_disciplina_aula(aula_para_remover) and
                        obter_turma_aula(aula) == obter_turma_aula(aula_para_remover)):
                        
                        # Marcar para remoção
                        aulas_para_remover.add(idx)
                        
                        # Registrar no relatório
                        removida_info = f"{obter_disciplina_aula(aula_para_remover)} - {obter_turma_aula(aula_para_remover)}"
                        relatorio.append(f"• REMOVIDA: {removida_info} (mantida: {mantida_info})")
                        break
    
    # Remover aulas marcadas
    aulas_corrigidas = [aula for idx, aula in enumerate(aulas) if idx not in aulas_para_remover]
    
    # Mostrar relatório
    if relatorio:
        st.warning(f"**CORREÇÃO ULTRA APLICADA**: Removidas {len(aulas_para_remover)} aulas conflitantes")
        with st.expander("📋 Ver detalhes das remoções", expanded=False):
            for item in relatorio[:10]:  # Mostrar apenas 10 itens
                st.write(item)
            if len(relatorio) > 10:
                st.write(f"... e mais {len(relatorio) - 10} remoções")
    
    return aulas_corrigidas

# ============================================
# FUNÇÃO: VISUALIZAR GRADE EM FORMATO CALENDÁRIO
# ============================================

def visualizar_grade_calendario(aulas, turma_nome=None):
    """Visualiza grade em formato de calendário/tabela"""
    if not aulas:
        st.warning("Nenhuma aula para visualizar")
        return
    
    # Filtrar por turma se especificado
    if turma_nome:
        aulas = [a for a in aulas if obter_turma_aula(a) == turma_nome]
        if not aulas:
            st.warning(f"Nenhuma aula para a turma {turma_nome}")
            return
    
    # Determinar turmas únicas
    turmas_unicas = set()
    for aula in aulas:
        turma = obter_turma_aula(aula)
        if turma:
            turmas_unicas.add(turma)
    
    # Para cada turma, criar tabela
    for turma in sorted(turmas_unicas):
        st.subheader(f"📅 Grade da Turma: {turma}")
        
        # Filtrar aulas desta turma
        aulas_turma = [a for a in aulas if obter_turma_aula(a) == turma]
        
        # Determinar segmento
        segmento = obter_segmento_turma(turma)
        
        # Horários disponíveis
        if segmento == "EM":
            periodos = list(range(1, 8))
            horarios = {
                1: "07:00 - 07:50",
                2: "07:50 - 08:40",
                3: "08:40 - 09:30",
                4: "09:50 - 10:40",
                5: "10:40 - 11:30",
                6: "11:30 - 12:20",
                7: "12:20 - 13:10"
            }
        else:
            periodos = list(range(1, 6))
            horarios = {
                1: "07:50 - 08:40",
                2: "08:40 - 09:30",
                3: "09:50 - 10:40",
                4: "10:40 - 11:30",
                5: "11:30 - 12:20"
            }
        
        # Dias da semana
        dias = ["segunda", "terca", "quarta", "quinta", "sexta"]
        dias_display = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta"]
        
        # Criar tabela HTML
        html = f"""
        <style>
        .tabela-calendario {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            font-family: Arial, sans-serif;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .tabela-calendario th {{
            background-color: #4a6baf;
            color: white;
            padding: 12px;
            text-align: center;
            font-weight: bold;
            border: 1px solid #ddd;
        }}
        .tabela-calendario td {{
            padding: 10px;
            border: 1px solid #ddd;
            text-align: center;
            vertical-align: middle;
            min-height: 60px;
        }}
        .celula-horario {{
            background-color: #f0f7ff;
            font-weight: bold;
            color: #2c5282;
        }}
        .celula-aula {{
            background-color: #e8f5e9;
            border-radius: 4px;
            margin: 2px;
        }}
        .celula-vazia {{
            background-color: #f9f9f9;
            color: #999;
            font-style: italic;
        }}
        .disciplina-nome {{
            font-weight: bold;
            font-size: 13px;
            color: #2e7d32;
        }}
        .professor-nome {{
            font