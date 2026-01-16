from flask import Flask, render_template, request, jsonify, session
import json
import os
from datetime import datetime
from models import calcular_viabilidade, Turma, Disciplina, NivelEnsino

app = Flask(__name__)
app.secret_key = 'viabilidade_escola_secret_key_2026'

# Dados das disciplinas
DISCIPLINAS = [
    Disciplina(1, "Matemática", 65),
    Disciplina(2, "História", 58),
    Disciplina(3, "Arte", 55),
    Disciplina(4, "Química", 70),
    Disciplina(5, "Sociologia", 60),
    Disciplina(6, "Português", 60),
    Disciplina(7, "Geografia", 50),
    Disciplina(8, "Educação Física", 52),
    Disciplina(9, "Biologia", 60),
    Disciplina(10, "Ciências", 62),
    Disciplina(11, "Inglês", 75),
    Disciplina(12, "Física", 70),
    Disciplina(13, "Filosofia", 60)
]

NIVEIS = [
    NivelEnsino("fund1", "Fundamental I", "1º ao 5º"),
    NivelEnsino("fund2", "Fundamental II", "6º ao 9º"),
    NivelEnsino("medio", "Ensino Médio", "1º ao 3º"),
    NivelEnsino("prevest", "Pré-Vestibular", "--")
]

@app.route('/')
def index():
    """Página principal da calculadora de viabilidade"""
    # Inicializar sessão se não existir
    if 'turmas' not in session:
        session['turmas'] = []
        session['niveis_selecionados'] = []
        session['disciplinas_selecionadas'] = []
        session['custos_fixos'] = {
            'aluguel': 0, 'condominio': 0, 'agua': 0, 'energia': 0,
            'internet': 0, 'limpeza': 0, 'projetor': 0, 'computadores': 0,
            'moveis': 0, 'arcondicionado': 0, 'divulgacao': 0,
            'material_grafico': 0, 'site': 0, 'redes_sociais': 0
        }
        session['acr_inicial'] = 0
    
    return render_template('index.html', 
                         disciplinas=DISCIPLINAS,
                         niveis=NIVEIS,
                         turmas=session['turmas'])

@app.route('/adicionar_turma', methods=['POST'])
def adicionar_turma():
    """Adiciona uma nova turma"""
    data = request.get_json()
    
    # Gerar ID único para a turma
    turma_id = len(session['turmas']) + 1
    
    # Criar objeto Turma
    nova_turma = {
        'id': turma_id,
        'disciplina_id': data.get('disciplina_id'),
        'nivel_id': data.get('nivel_id'),
        'capacidade': data.get('capacidade', 30),
        'alunos_matriculados': data.get('alunos_matriculados', 0),
        'horas_semana': data.get('horas_semana', 4),
        'dias_semana': data.get('dias_semana', 2),
        'mensalidade_aluno': data.get('mensalidade_aluno', 300),
        'custo_material_mes': data.get('custo_material_mes', 100),
        'expandida': False
    }
    
    # Adicionar custo/hora do professor baseado na disciplina
    if nova_turma['disciplina_id']:
        disciplina = next((d for d in DISCIPLINAS if d.id == nova_turma['disciplina_id']), None)
        if disciplina:
            nova_turma['custo_hora_professor'] = disciplina.custo_hora
    
    # Adicionar à sessão
    turmas = session['turmas']
    turmas.append(nova_turma)
    session['turmas'] = turmas
    
    return jsonify({'success': True, 'turma': nova_turma})

@app.route('/atualizar_turma/<int:turma_id>', methods=['POST'])
def atualizar_turma(turma_id):
    """Atualiza os dados de uma turma"""
    data = request.get_json()
    
    turmas = session['turmas']
    for i, turma in enumerate(turmas):
        if turma['id'] == turma_id:
            # Atualizar campos
            for key, value in data.items():
                if key in turma:
                    turma[key] = value
            
            # Atualizar custo/hora se disciplina mudou
            if 'disciplina_id' in data and data['disciplina_id']:
                disciplina = next((d for d in DISCIPLINAS if d.id == data['disciplina_id']), None)
                if disciplina:
                    turma['custo_hora_professor'] = disciplina.custo_hora
            
            turmas[i] = turma
            session['turmas'] = turmas
            break
    
    return jsonify({'success': True})

@app.route('/remover_turma/<int:turma_id>', methods=['POST'])
def remover_turma(turma_id):
    """Remove uma turma"""
    turmas = session['turmas']
    turmas = [t for t in turmas if t['id'] != turma_id]
    session['turmas'] = turmas
    
    return jsonify({'success': True})

@app.route('/calcular_viabilidade', methods=['POST'])
def calcular():
    """Calcula a viabilidade financeira"""
    data = request.get_json()
    
    # Atualizar dados da sessão
    if 'custos_fixos' in data:
        session['custos_fixos'] = data['custos_fixos']
    if 'acr_inicial' in data:
        session['acr_inicial'] = data['acr_inicial']
    
    # Calcular viabilidade
    resultados = calcular_viabilidade(
        session['turmas'],
        session['custos_fixos'],
        session['acr_inicial']
    )
    
    return jsonify({'success': True, 'resultados': resultados})

@app.route('/carregar_exemplo', methods=['POST'])
def carregar_exemplo():
    """Carrega dados de exemplo"""
    # Limpar dados atuais
    session.clear()
    
    # Configurar exemplo
    session['niveis_selecionados'] = ['fund2', 'medio']
    session['disciplinas_selecionadas'] = [1, 4, 6, 9, 11, 12]  # IDs das disciplinas
    
    # Custos fixos exemplo
    session['custos_fixos'] = {
        'aluguel': 2500, 'condominio': 800, 'agua': 150, 'energia': 400,
        'internet': 120, 'limpeza': 600, 'projetor': 200, 'computadores': 500,
        'moveis': 300, 'arcondicionado': 250, 'divulgacao': 800,
        'material_grafico': 300, 'site': 200, 'redes_sociais': 150
    }
    
    # ACR inicial
    session['acr_inicial'] = 5000
    
    # Turmas exemplo
    session['turmas'] = [
        {
            'id': 1,
            'disciplina_id': 1,  # Matemática
            'nivel_id': 'medio',
            'capacidade': 35,
            'alunos_matriculados': 32,
            'horas_semana': 6,
            'dias_semana': 3,
            'custo_hora_professor': 65,
            'mensalidade_aluno': 350,
            'custo_material_mes': 150,
            'expandida': False
        },
        {
            'id': 2,
            'disciplina_id': 11,  # Inglês
            'nivel_id': 'fund2',
            'capacidade': 25,
            'alunos_matriculados': 22,
            'horas_semana': 4,
            'dias_semana': 2,
            'custo_hora_professor': 75,
            'mensalidade_aluno': 400,
            'custo_material_mes': 200,
            'expandida': False
        },
        {
            'id': 3,
            'disciplina_id': 12,  # Física
            'nivel_id': 'medio',
            'capacidade': 30,
            'alunos_matriculados': 28,
            'horas_semana': 5,
            'dias_semana': 2,
            'custo_hora_professor': 70,
            'mensalidade_aluno': 380,
            'custo_material_mes': 180,
            'expandida': False
        }
    ]
    
    # Calcular resultados do exemplo
    resultados = calcular_viabilidade(
        session['turmas'],
        session['custos_fixos'],
        session['acr_inicial']
    )
    
    return jsonify({'success': True, 'resultados': resultados})

@app.route('/limpar_tudo', methods=['POST'])
def limpar_tudo():
    """Limpa todos os dados"""
    session.clear()
    
    # Reinicializar sessão
    session['turmas'] = []
    session['niveis_selecionados'] = []
    session['disciplinas_selecionadas'] = []
    session['custos_fixos'] = {
        'aluguel': 0, 'condominio': 0, 'agua': 0, 'energia': 0,
        'internet': 0, 'limpeza': 0, 'projetor': 0, 'computadores': 0,
        'moveis': 0, 'arcondicionado': 0, 'divulgacao': 0,
        'material_grafico': 0, 'site': 0, 'redes_sociais': 0
    }
    session['acr_inicial'] = 0
    
    return jsonify({'success': True})

@app.route('/turmas')
def gerenciar_turmas():
    """Página para gerenciar turmas (modal/popup)"""
    return render_template('turmas.html', 
                         disciplinas=DISCIPLINAS,
                         niveis=NIVEIS,
                         turmas=session.get('turmas', []))

if __name__ == '__main__':
    app.run(debug=True, port=5000)