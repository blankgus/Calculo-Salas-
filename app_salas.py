# app_salas.py - Viabilidade Financeira de Salas de Aula
from flask import Flask, render_template_string, request, jsonify, session, redirect
from datetime import datetime
import json
import os
import sqlite3
from typing import Dict, List, Any

app = Flask(__name__)
app.config['SECRET_KEY'] = 'viabilidade_salas_2024'

# Configuração do banco de dados
DATABASE = 'database_salas.db'

# Configurações padrão
HORAS_MENSAL_PADRAO = 80  # 20h semanais × 4 semanas
DIAS_AULA_MES = 20
CARGA_HORARIA_DIARIA = 4

# Tipos de disciplinas com custos por hora
DISCIPLINAS = {
    'matematica': {'nome': 'Matemática', 'custo_hora': 65, 'cor': '#FF6B6B'},
    'portugues': {'nome': 'Português', 'custo_hora': 60, 'cor': '#4ECDC4'},
    'ciencias': {'nome': 'Ciências', 'custo_hora': 62, 'cor': '#45B7D1'},
    'historia': {'nome': 'História', 'custo_hora': 58, 'cor': '#96CEB4'},
    'geografia': {'nome': 'Geografia', 'custo_hora': 58, 'cor': '#FFEAA7'},
    'ingles': {'nome': 'Inglês', 'custo_hora': 75, 'cor': '#DDA0DD'},
    'arte': {'nome': 'Arte', 'custo_hora': 55, 'cor': '#98D8C8'},
    'educacao_fisica': {'nome': 'Educação Física', 'custo_hora': 52, 'cor': '#F7DC6F'},
    'fisica': {'nome': 'Física', 'custo_hora': 70, 'cor': '#BB8FCE'},
    'quimica': {'nome': 'Química', 'custo_hora': 70, 'cor': '#85C1E9'},
    'biologia': {'nome': 'Biologia', 'custo_hora': 68, 'cor': '#82E0AA'},
    'filosofia': {'nome': 'Filosofia', 'custo_hora': 60, 'cor': '#F8C471'},
    'sociologia': {'nome': 'Sociologia', 'custo_hora': 60, 'cor': '#EB984E'}
}

# Níveis de ensino
NIVEIS_ENSINO = {
    'fundamental_i': {'nome': 'Fundamental I', 'series': '1º ao 5º', 'idade': '6-10 anos'},
    'fundamental_ii': {'nome': 'Fundamental II', 'series': '6º ao 9º', 'idade': '11-14 anos'},
    'medio': {'nome': 'Ensino Médio', 'series': '1º ao 3º', 'idade': '15-17 anos'},
    'pre_vestibular': {'nome': 'Pré-Vestibular', 'series': '--', 'idade': '17+ anos'}
}

# Categorias de custos fixos
CATEGORIAS_CUSTOS = {
    'infraestrutura': ['Aluguel', 'Condomínio', 'Água', 'Energia', 'Internet', 'Limpeza'],
    'manutencao': ['Material de limpeza', 'Reparos', 'Material administrativo', 'Taxas'],
    'equipamentos': ['Projetor', 'Computadores', 'Móveis', 'Ar condicionado'],
    'marketing': ['Divulgação', 'Material gráfico', 'Site', 'Redes sociais'],
    'administrativo': ['Secretária', 'Coordenação', 'Contador', 'Seguro']
}

def init_db():
    """Inicializa o banco de dados"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS simulacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            data_criacao TEXT,
            total_turmas INTEGER,
            total_alunos INTEGER,
            total_professores INTEGER,
            investimento_inicial REAL,
            custo_mensal_total REAL,
            receita_mensal_total REAL,
            lucro_mensal REAL,
            margem_lucro REAL,
            ticket_medio REAL,
            dados_completos TEXT
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS turmas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            simulacao_id INTEGER,
            nome_turma TEXT,
            nivel TEXT,
            disciplina TEXT,
            capacidade INTEGER,
            alunos_matriculados INTEGER,
            horas_semanais REAL,
            dias_semana INTEGER,
            custo_hora_professor REAL,
            mensalidade_aluno REAL,
            custo_material_mensal REAL,
            FOREIGN KEY (simulacao_id) REFERENCES simulacoes (id) ON DELETE CASCADE
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS alunos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            turma_id INTEGER,
            nome TEXT,
            mensalidade REAL,
            status TEXT DEFAULT 'ativo',
            data_matricula TEXT,
            FOREIGN KEY (turma_id) REFERENCES turmas (id) ON DELETE CASCADE
        )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ Banco de dados de salas inicializado!")
        return True
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

# Inicializar banco
init_db()

def get_base_html(title="Viabilidade de Salas", content=""):
    """Retorna o HTML base"""
    return f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {{
            --primary: #4361ee;
            --secondary: #3a0ca3;
            --success: #4cc9f0;
            --warning: #f72585;
            --info: #7209b7;
        }}
        
        body {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }}
        
        .container-main {{
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            margin-top: 30px;
            margin-bottom: 30px;
            padding: 30px;
        }}
        
        .card {{
            border-radius: 15px;
            border: none;
            box-shadow: 0 5px 15px rgba(0,0,0,0.08);
            transition: transform 0.3s;
            margin-bottom: 20px;
        }}
        
        .card:hover {{
            transform: translateY(-5px);
        }}
        
        .card-header {{
            border-radius: 15px 15px 0 0 !important;
            font-weight: 600;
        }}
        
        .btn-primary {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border: none;
            border-radius: 10px;
            padding: 10px 25px;
            font-weight: 600;
        }}
        
        .btn-primary:hover {{
            background: linear-gradient(135deg, #5a6fd8 0%, #6a4092 100%);
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }}
        
        .turma-card {{
            border-left: 5px solid var(--primary);
            background: #f8f9ff;
        }}
        
        .disciplina-badge {{
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            color: white;
            font-weight: 600;
            margin: 2px;
        }}
        
        .nivel-badge {{
            background: var(--info);
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.8em;
        }}
        
        .resultado-card {{
            background: linear-gradient(135deg, #4cc9f0 0%, #4361ee 100%);
            color: white;
            border-radius: 15px;
            padding: 20px;
            margin: 10px 0;
        }}
        
        .indicador {{
            text-align: center;
            padding: 15px;
            background: white;
            border-radius: 10px;
            box-shadow: 0 3px 10px rgba(0,0,0,0.1);
        }}
        
        .indicador .valor {{
            font-size: 2em;
            font-weight: 700;
            margin: 10px 0;
        }}
        
        .indicador .label {{
            font-size: 0.9em;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .table-custom {{
            background: white;
            border-radius: 10px;
            overflow: hidden;
        }}
        
        .table-custom thead {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }}
        
        .add-btn {{
            background: #4cc9f0;
            border: none;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            color: white;
            font-size: 1.5em;
            cursor: pointer;
            transition: all 0.3s;
        }}
        
        .add-btn:hover {{
            background: #3ab8df;
            transform: rotate(90deg);
        }}
        
        .form-control, .form-select {{
            border-radius: 10px;
            border: 2px solid #e0e0e0;
            padding: 10px 15px;
        }}
        
        .form-control:focus, .form-select:focus {{
            border-color: #667eea;
            box-shadow: 0 0 0 0.2rem rgba(102, 126, 234, 0.25);
        }}
        
        .aluno-item {{
            background: #f0f4ff;
            border-radius: 10px;
            padding: 15px;
            margin: 10px 0;
            border-left: 4px solid #4cc9f0;
        }}
        
        .alert-custom {{
            border-radius: 10px;
            border: none;
            padding: 15px;
        }}
        
        @media (max-width: 768px) {{
            .container-main {{
                padding: 15px;
                margin: 10px;
            }}
            
            .indicador .valor {{
                font-size: 1.5em;
            }}
        }}
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark" style="background: rgba(0,0,0,0.2); backdrop-filter: blur(10px);">
        <div class="container">
            <a class="navbar-brand" href="/">
                <i class="fas fa-chalkboard-teacher"></i> Viabilidade de Salas
            </a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="/"><i class="fas fa-home"></i> Início</a>
                <a class="nav-link" href="/simulacao"><i class="fas fa-plus"></i> Nova Análise</a>
                <a class="nav-link" href="/historico"><i class="fas fa-history"></i> Histórico</a>
                <a class="nav-link" href="/relatorio"><i class="fas fa-chart-pie"></i> Relatórios</a>
            </div>
        </div>
    </nav>

    <div class="container container-main">
        {content}
    </div>

    <footer class="text-center text-white py-4" style="background: rgba(0,0,0,0.2);">
        <p><i class="fas fa-calculator"></i> Sistema de Viabilidade Financeira de Salas de Aula</p>
        <p class="mb-0">© 2024 - Análise precisa de custos e receitas</p>
    </footer>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>'''

@app.route('/')
def index():
    """Página inicial"""
    content = '''
    <div class="text-center">
        <h1 class="display-4 mb-4" style="color: #4361ee;">
            <i class="fas fa-chalkboard-teacher"></i> Viabilidade de Salas de Aula
        </h1>
        <p class="lead mb-4">
            Calcule a viabilidade financeira das suas turmas, professores e custos
        </p>
        
        <div class="row mt-5">
            <div class="col-md-4">
                <div class="card">
                    <div class="card-body text-center">
                        <i class="fas fa-users fa-3x mb-3" style="color: #667eea;"></i>
                        <h4>Turmas</h4>
                        <p>Crie e analise turmas por disciplina e nível</p>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card">
                    <div class="card-body text-center">
                        <i class="fas fa-user-graduate fa-3x mb-3" style="color: #4cc9f0;"></i>
                        <h4>Alunos</h4>
                        <p>Controle de matrículas e mensalidades</p>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card">
                    <div class="card-body text-center">
                        <i class="fas fa-calculator fa-3x mb-3" style="color: #f72585;"></i>
                        <h4>Custos</h4>
                        <p>Análise detalhada de custos fixos e variáveis</p>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="row mt-4">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header bg-primary text-white">
                        <h5 class="mb-0"><i class="fas fa-cogs"></i> Funcionalidades</h5>
                    </div>
                    <div class="card-body">
                        <ul class="list-group list-group-flush">
                            <li class="list-group-item">
                                <i class="fas fa-check text-success"></i> Cálculo de custo por hora/professor
                            </li>
                            <li class="list-group-item">
                                <i class="fas fa-check text-success"></i> Análise de ocupação de salas
                            </li>
                            <li class="list-group-item">
                                <i class="fas fa-check text-success"></i> Controle de mensalidades por aluno
                            </li>
                            <li class="list-group-item">
                                <i class="fas fa-check text-success"></i> Custos fixos e variáveis
                            </li>
                            <li class="list-group-item">
                                <i class="fas fa-check text-success"></i> Relatórios financeiros detalhados
                            </li>
                        </ul>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header bg-success text-white">
                        <h5 class="mb-0"><i class="fas fa-chart-line"></i> Indicadores</h5>
                    </div>
                    <div class="card-body">
                        <ul class="list-group list-group-flush">
                            <li class="list-group-item">
                                <strong>Ticket médio:</strong> Cálculo automático
                            </li>
                            <li class="list-group-item">
                                <strong>Margem de lucro:</strong> Por turma e geral
                            </li>
                            <li class="list-group-item">
                                <strong>Custo por aluno:</strong> Análise de eficiência
                            </li>
                            <li class="list-group-item">
                                <strong>Ocupação ideal:</strong> Sugestões de otimização
                            </li>
                            <li class="list-group-item">
                                <strong>Payback:</strong> Retorno do investimento
                            </li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="mt-5">
            <a href="/simulacao" class="btn btn-primary btn-lg">
                <i class="fas fa-rocket"></i> Começar Nova Análise
            </a>
            <a href="/exemplo" class="btn btn-outline-primary btn-lg ms-3">
                <i class="fas fa-eye"></i> Ver Exemplo
            </a>
        </div>
    </div>
    '''
    return get_base_html("Viabilidade de Salas", content)

@app.route('/simulacao')
@app.route('/simulacao/<int:simulacao_id>')
def simulacao(simulacao_id=None):
    """Página de simulação de viabilidade"""
    modo_edicao = simulacao_id is not None
    dados_edicao = {}
    
    if modo_edicao:
        try:
            conn = sqlite3.connect(DATABASE)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM simulacoes WHERE id = ?', (simulacao_id,))
            simulacao = cursor.fetchone()
            if simulacao:
                dados_completos = json.loads(simulacao['dados_completos'])
                dados_edicao = {
                    'id': simulacao_id,
                    'nome': simulacao['nome'],
                    'turmas': dados_completos.get('turmas', []),
                    'custos': dados_completos.get('custos', {}),
                    'alunos': dados_completos.get('alunos', [])
                }
            conn.close()
        except Exception as e:
            print(f"Erro ao carregar: {e}")
            return redirect('/historico')
    
    # HTML para seleção de disciplinas
    disciplinas_html = ""
    for codigo, info in DISCIPLINAS.items():
        disciplinas_html += f'''
        <div class="col-md-4 mb-3">
            <div class="form-check">
                <input class="form-check-input disciplina-check" type="checkbox" 
                       id="disc_{codigo}" value="{codigo}" data-custo="{info['custo_hora']}">
                <label class="form-check-label" for="disc_{codigo}">
                    <span class="disciplina-badge" style="background-color: {info['cor']};">
                        {info['nome']} (R$ {info['custo_hora']}/h)
                    </span>
                </label>
            </div>
        </div>
        '''
    
    # HTML para níveis de ensino
    niveis_html = ""
    for codigo, info in NIVEIS_ENSINO.items():
        niveis_html += f'''
        <div class="col-md-3 mb-3">
            <div class="card">
                <div class="card-body text-center">
                    <h6>{info['nome']}</h6>
                    <small class="text-muted">{info['series']}</small>
                    <div class="mt-2">
                        <input type="radio" class="btn-check" name="nivel" 
                               id="nivel_{codigo}" value="{codigo}" autocomplete="off">
                        <label class="btn btn-outline-primary btn-sm" for="nivel_{codigo}">
                            Selecionar
                        </label>
                    </div>
                </div>
            </div>
        </div>
        '''
    
    # HTML para custos fixos
    custos_html = ""
    for categoria, itens in CATEGORIAS_CUSTOS.items():
        titulo_categoria = categoria.replace('_', ' ').title()
        custos_html += f'''
        <div class="col-md-6">
            <div class="card mb-4">
                <div class="card-header bg-secondary text-white">
                    <h6 class="mb-0"><i class="fas fa-{["building", "tools", "laptop", "bullhorn", "user-tie"][list(CATEGORIAS_CUSTOS.keys()).index(categoria)]}"></i> {titulo_categoria}</h6>
                </div>
                <div class="card-body">
        '''
        
        for item in itens:
            campo_id = f"custo_{categoria}_{item.lower().replace(' ', '_')}"
            valor_edicao = 0
            if dados_edicao.get('custos', {}).get(categoria, {}).get(item):
                valor_edicao = dados_edicao['custos'][categoria][item]
            
            custos_html += f'''
            <div class="mb-3">
                <label class="form-label">{item}:</label>
                <div class="input-group">
                    <span class="input-group-text">R$</span>
                    <input type="number" class="form-control campo-custo" 
                           id="{campo_id}" data-categoria="{categoria}"
                           value="{valor_edicao}" min="0" step="10">
                </div>
            </div>
            '''
        
        custos_html += '''
                </div>
            </div>
        </div>
        '''
    
    content = f'''
    <div class="row">
        <div class="col-lg-12">
            <div class="card">
                <div class="card-header bg-primary text-white">
                    <h3 class="mb-0">
                        <i class="fas fa-calculator"></i> {'Editar Análise' if modo_edicao else 'Nova Análise de Viabilidade'}
                    </h3>
                </div>
                <div class="card-body">
                    <form id="formSimulacao">
                        <!-- Informações básicas -->
                        <div class="row mb-4">
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">Nome da Instituição/Análise:</label>
                                    <input type="text" class="form-control" id="nome_analise" 
                                           value="{dados_edicao.get('nome', 'Minha Escola')}" required>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">Quantidade de Salas Disponíveis:</label>
                                    <input type="number" class="form-control" id="salas_disponiveis" 
                                           value="{dados_edicao.get('salas', 5)}" min="1" required>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Níveis de Ensino -->
                        <div class="row mb-4">
                            <div class="col-12">
                                <h5 class="border-bottom pb-2 mb-3">
                                    <i class="fas fa-graduation-cap"></i> Níveis de Ensino
                                </h5>
                                <div class="row">
                                    {niveis_html}
                                </div>
                            </div>
                        </div>
                        
                        <!-- Disciplinas -->
                        <div class="row mb-4">
                            <div class="col-12">
                                <h5 class="border-bottom pb-2 mb-3">
                                    <i class="fas fa-book-open"></i> Disciplinas Oferecidas
                                </h5>
                                <p class="text-muted">Selecione as disciplinas que serão oferecidas:</p>
                                <div class="row">
                                    {disciplinas_html}
                                </div>
                            </div>
                        </div>
                        
                        <!-- Turmas -->
                        <div class="row mb-4">
                            <div class="col-12">
                                <div class="d-flex justify-content-between align-items-center mb-3">
                                    <h5 class="mb-0">
                                        <i class="fas fa-chalkboard"></i> Turmas
                                    </h5>
                                    <button type="button" class="btn btn-success" onclick="adicionarTurma()">
                                        <i class="fas fa-plus"></i> Adicionar Turma
                                    </button>
                                </div>
                                
                                <div id="turmas_container" class="row">
                                    <!-- Turmas serão adicionadas aqui -->
                                </div>
                            </div>
                        </div>
                        
                        <!-- Custos Fixos Mensais -->
                        <div class="row mb-4">
                            <div class="col-12">
                                <h5 class="border-bottom pb-2 mb-3">
                                    <i class="fas fa-money-bill-wave"></i> Custos Fixos Mensais
                                </h5>
                                <div class="row">
                                    {custos_html}
                                </div>
                            </div>
                        </div>
                        
                        <!-- Alunos (opcional) -->
                        <div class="row mb-4">
                            <div class="col-12">
                                <div class="card">
                                    <div class="card-header bg-info text-white">
                                        <h5 class="mb-0"><i class="fas fa-user-graduate"></i> Dados dos Alunos (Opcional)</h5>
                                    </div>
                                    <div class="card-body">
                                        <div class="mb-3">
                                            <label class="form-label">Nome do Aluno:</label>
                                            <input type="text" class="form-control" id="nome_aluno">
                                        </div>
                                        <div class="mb-3">
                                            <label class="form-label">Mensalidade do Aluno (R$):</label>
                                            <input type="number" class="form-control" id="mensalidade_aluno" min="0" step="10">
                                        </div>
                                        <button type="button" class="btn btn-outline-info" onclick="adicionarAluno()">
                                            <i class="fas fa-plus"></i> Adicionar Aluno
                                        </button>
                                        
                                        <div id="alunos_lista" class="mt-3">
                                            <!-- Lista de alunos será exibida aqui -->
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Resultados e Ações -->
                        <div class="row">
                            <div class="col-md-6">
                                <div class="card">
                                    <div class="card-header bg-warning text-white">
                                        <h5 class="mb-0"><i class="fas fa-chart-bar"></i> Resumo Financeiro</h5>
                                    </div>
                                    <div class="card-body">
                                        <div id="resumo_financeiro">
                                            <p class="text-center text-muted">Adicione turmas para ver o resumo</p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="col-md-6">
                                <div class="card">
                                    <div class="card-header bg-success text-white">
                                        <h5 class="mb-0"><i class="fas fa-rocket"></i> Ações</h5>
                                    </div>
                                    <div class="card-body">
                                        <div class="d-grid gap-2">
                                            <button type="button" class="btn btn-primary btn-lg" onclick="calcularViabilidade({simulacao_id if modo_edicao else 'null'})">
                                                <i class="fas fa-calculator"></i> {'Atualizar Análise' if modo_edicao else 'Calcular Viabilidade'}
                                            </button>
                                            <button type="button" class="btn btn-outline-secondary" onclick="carregarExemplo()">
                                                <i class="fas fa-magic"></i> Carregar Exemplo
                                            </button>
                                            <button type="button" class="btn btn-outline-danger" onclick="limparFormulario()">
                                                <i class="fas fa-trash"></i> Limpar Tudo
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </div>

    <!-- Template de Turma -->
    <template id="template-turma">
        <div class="col-md-6">
            <div class="card turma-card mb-4">
                <div class="card-header d-flex justify-content-between align-items-center">
                    <h6 class="mb-0"><i class="fas fa-chalkboard"></i> <span class="nome-turma">Nova Turma</span></h6>
                    <i class="fas fa-times text-danger" style="cursor: pointer;" onclick="removerTurma(this)"></i>
                </div>
                <div class="card-body">
                    <div class="row g-2">
                        <div class="col-12">
                            <input type="text" class="form-control mb-2 nome-turma-input" 
                                   placeholder="Nome da turma (ex: Matemática 1º EM)" value="Nova Turma">
                        </div>
                        <div class="col-md-6">
                            <select class="form-select mb-2 select-disciplina" onchange="atualizarCustoProfessor(this)">
                                <option value="">Selecione a disciplina</option>
                                {''.join([f'<option value="{cod}" data-custo="{info["custo_hora"]}">{info["nome"]}</option>' for cod, info in DISCIPLINAS.items()])}
                            </select>
                        </div>
                        <div class="col-md-6">
                            <select class="form-select mb-2 select-nivel">
                                <option value="">Nível de ensino</option>
                                {''.join([f'<option value="{cod}">{info["nome"]}</option>' for cod, info in NIVEIS_ENSINO.items()])}
                            </select>
                        </div>
                        <div class="col-md-6">
                            <input type="number" class="form-control mb-2 capacidade-turma" 
                                   placeholder="Capacidade máxima" value="30" min="1">
                        </div>
                        <div class="col-md-6">
                            <input type="number" class="form-control mb-2 alunos-matriculados" 
                                   placeholder="Alunos matriculados" value="20" min="0">
                        </div>
                        <div class="col-md-6">
                            <input type="number" class="form-control mb-2 horas-semanais" 
                                   placeholder="Horas/semana" value="4" min="1" step="0.5">
                        </div>
                        <div class="col-md-6">
                            <input type="number" class="form-control mb-2 dias-semana" 
                                   placeholder="Dias/semana" value="2" min="1" max="7">
                        </div>
                        <div class="col-md-6">
                            <div class="input-group mb-2">
                                <span class="input-group-text">R$</span>
                                <input type="number" class="form-control custo-hora-professor" 
                                       placeholder="Custo/hora professor" value="60" min="0" step="1">
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="input-group mb-2">
                                <span class="input-group-text">R$</span>
                                <input type="number" class="form-control mensalidade-aluno" 
                                       placeholder="Mensalidade/aluno" value="250" min="0" step="10">
                            </div>
                        </div>
                        <div class="col-12">
                            <div class="input-group">
                                <span class="input-group-text">R$</span>
                                <input type="number" class="form-control custo-material" 
                                       placeholder="Custo material/mês" value="100" min="0" step="10">
                                <span class="input-group-text">/mês</span>
                            </div>
                        </div>
                    </div>
                    
                    <div class="mt-3 p-2 bg-light rounded">
                        <div class="row small text-center">
                            <div class="col-6">
                                <strong>Custo mensal:</strong><br>
                                <span class="text-danger custo-mensal-turma">R$ 0,00</span>
                            </div>
                            <div class="col-6">
                                <strong>Receita mensal:</strong><br>
                                <span class="text-success receita-mensal-turma">R$ 0,00</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </template>

    <!-- Template de Aluno -->
    <template id="template-aluno">
        <div class="aluno-item">
            <div class="d-flex justify-content-between align-items-center">
                <div>
                    <strong><span class="nome-aluno">Novo Aluno</span></strong><br>
                    <small>Mensalidade: R$ <span class="valor-mensalidade">0,00</span></small>
                </div>
                <i class="fas fa-times text-danger" style="cursor: pointer;" onclick="removerAluno(this)"></i>
            </div>
        </div>
    </template>

    <script>
    document.addEventListener('DOMContentLoaded', function() {{
        // Adiciona uma turma inicial
        adicionarTurma();
        
        // Atualiza resumo quando campos são alterados
        document.querySelectorAll('.form-control, .form-select').forEach(campo => {{
            campo.addEventListener('input', atualizarResumo);
        }});
        
        // Configura eventos para checkboxes de disciplinas
        document.querySelectorAll('.disciplina-check').forEach(cb => {{
            cb.addEventListener('change', atualizarResumo);
        }});
        
        atualizarResumo();
    }});
    
    function adicionarTurma() {{
        const container = document.getElementById('turmas_container');
        const template = document.getElementById('template-turma').content.cloneNode(true);
        
        // Configurar eventos para a nova turma
        const inputs = template.querySelectorAll('input, select');
        inputs.forEach(input => {{
            input.addEventListener('input', function() {{
                if (this.classList.contains('nome-turma-input')) {{
                    this.closest('.turma-card').querySelector('.nome-turma').textContent = this.value;
                }}
                calcularTurma(this.closest('.turma-card'));
                atualizarResumo();
            }});
        }});
        
        container.appendChild(template);
        calcularTurma(container.lastElementChild.querySelector('.turma-card'));
        atualizarResumo();
    }}
    
    function removerTurma(elemento) {{
        elemento.closest('.col-md-6').remove();
        atualizarResumo();
    }}
    
    function adicionarAluno() {{
        const nome = document.getElementById('nome_aluno').value.trim();
        const mensalidade = parseFloat(document.getElementById('mensalidade_aluno').value) || 0;
        
        if (!nome) {{
            alert('Digite o nome do aluno');
            return;
        }}
        
        const container = document.getElementById('alunos_lista');
        const template = document.getElementById('template-aluno').content.cloneNode(true);
        
        template.querySelector('.nome-aluno').textContent = nome;
        template.querySelector('.valor-mensalidade').textContent = mensalidade.toFixed(2);
        
        container.appendChild(template);
        
        // Limpa os campos
        document.getElementById('nome_aluno').value = '';
        document.getElementById('mensalidade_aluno').value = '';
        
        atualizarResumo();
    }}
    
    function removerAluno(elemento) {{
        elemento.closest('.aluno-item').remove();
        atualizarResumo();
    }}
    
    function calcularTurma(turmaCard) {{
        const alunos = parseInt(turmaCard.querySelector('.alunos-matriculados').value) || 0;
        const capacidade = parseInt(turmaCard.querySelector('.capacidade-turma').value) || 0;
        const horasSemanais = parseFloat(turmaCard.querySelector('.horas-semanais').value) || 0;
        const diasSemana = parseInt(turmaCard.querySelector('.dias-semana').value) || 0;
        const custoHora = parseFloat(turmaCard.querySelector('.custo-hora-professor').value) || 0;
        const mensalidade = parseFloat(turmaCard.querySelector('.mensalidade-aluno').value) || 0;
        const custoMaterial = parseFloat(turmaCard.querySelector('.custo-material').value) || 0;
        
        // Cálculos
        const horasMensais = horasSemanais * diasSemana * 4; // 4 semanas no mês
        const custoProfessorMensal = custoHora * horasMensais;
        const custoTotal = custoProfessorMensal + custoMaterial;
        const receitaMensal = alunos * mensalidade;
        const ocupacao = capacidade > 0 ? (alunos / capacidade) * 100 : 0;
        
        // Atualiza display
        turmaCard.querySelector('.custo-mensal-turma').textContent = 
            `R$ ${{custoTotal.toLocaleString('pt-BR', {{minimumFractionDigits: 2}})}}`;
        turmaCard.querySelector('.receita-mensal-turma').textContent = 
            `R$ ${{receitaMensal.toLocaleString('pt-BR', {{minimumFractionDigits: 2}})}}`;
        
        // Atualiza cor da borda baseada na ocupação
        if (ocupacao >= 80) {{
            turmaCard.style.borderLeftColor = '#28a745'; // Verde - boa ocupação
        }} else if (ocupacao >= 50) {{
            turmaCard.style.borderLeftColor = '#ffc107'; // Amarelo - média ocupação
        }} else {{
            turmaCard.style.borderLeftColor = '#dc3545'; // Vermelho - baixa ocupação
        }}
        
        return {{
            alunos: alunos,
            capacidade: capacidade,
            custoTotal: custoTotal,
            receitaMensal: receitaMensal,
            ocupacao: ocupacao
        }};
    }}
    
    function atualizarCustoProfessor(select) {{
        const custoHora = select.options[select.selectedIndex].getAttribute('data-custo');
        if (custoHora) {{
            const turmaCard = select.closest('.turma-card');
            turmaCard.querySelector('.custo-hora-professor').value = custoHora;
            calcularTurma(turmaCard);
            atualizarResumo();
        }}
    }}
    
    function atualizarResumo() {{
        // Coletar dados das turmas
        let totalAlunos = 0, totalCapacidade = 0, receitaTurmas = 0, custoTurmas = 0;
        const turmas = [];
        
        document.querySelectorAll('.turma-card').forEach(card => {{
            const dados = calcularTurma(card);
            turmas.push(dados);
            
            totalAlunos += dados.alunos;
            totalCapacidade += dados.capacidade;
            receitaTurmas += dados.receitaMensal;
            custoTurmas += dados.custoTotal;
        }});
        
        // Calcular ocupação total
        const ocupacaoTotal = totalCapacidade > 0 ? (totalAlunos / totalCapacidade) * 100 : 0;
        
        // Custos fixos
        let custosFixos = 0;
        document.querySelectorAll('.campo-custo').forEach(campo => {{
            custosFixos += parseFloat(campo.value) || 0;
        }});
        
        // Alunos individuais (se houver)
        let receitaAlunosIndividuais = 0;
        let totalAlunosIndividuais = 0;
        document.querySelectorAll('.aluno-item').forEach(item => {{
            const mensalidade = parseFloat(item.querySelector('.valor-mensalidade').textContent) || 0;
            receitaAlunosIndividuais += mensalidade;
            totalAlunosIndividuais++;
        }});
        
        // Totais gerais
        const totalAlunosGeral = totalAlunos + totalAlunosIndividuais;
        const receitaTotal = receitaTurmas + receitaAlunosIndividuais;
        const custoTotal = custoTurmas + custosFixos;
        const lucroMensal = receitaTotal - custoTotal;
        const margemLucro = receitaTotal > 0 ? (lucroMensal / receitaTotal) * 100 : 0;
        
        // Ticket médio
        const ticketMedio = totalAlunosGeral > 0 ? receitaTotal / totalAlunosGeral : 0;
        
        // Atualizar display do resumo
        document.getElementById('resumo_financeiro').innerHTML = `
            <div class="row text-center">
                <div class="col-md-3 mb-3">
                    <div class="indicador">
                        <div class="label">Alunos</div>
                        <div class="valor" style="color: #4361ee;">${{totalAlunosGeral}}</div>
                        <small>Ocupação: ${{ocupacaoTotal.toFixed(1)}}%</small>
                    </div>
                </div>
                <div class="col-md-3 mb-3">
                    <div class="indicador">
                        <div class="label">Receita/Mês</div>
                        <div class="valor" style="color: #28a745;">R$ ${{receitaTotal.toLocaleString('pt-BR', {{minimumFractionDigits: 2}})}}</div>
                        <small>Ticket: R$ ${{ticketMedio.toFixed(2)}}</small>
                    </div>
                </div>
                <div class="col-md-3 mb-3">
                    <div class="indicador">
                        <div class="label">Custo/Mês</div>
                        <div class="valor" style="color: #dc3545;">R$ ${{custoTotal.toLocaleString('pt-BR', {{minimumFractionDigits: 2}})}}</div>
                        <small>Fixos: R$ ${{custosFixos.toLocaleString('pt-BR')}}</small>
                    </div>
                </div>
                <div class="col-md-3 mb-3">
                    <div class="indicador">
                        <div class="label">Lucro/Mês</div>
                        <div class="valor" style="color: ${{lucroMensal >= 0 ? '#17a2b8' : '#dc3545'}};">
                            R$ ${{lucroMensal.toLocaleString('pt-BR', {{minimumFractionDigits: 2}})}}
                        </div>
                        <small>Margem: ${{margemLucro.toFixed(1)}}%</small>
                    </div>
                </div>
            </div>
            
            <div class="alert ${{lucroMensal >= 0 ? 'alert-success' : 'alert-danger'}} alert-custom mt-3">
                <i class="fas ${{lucroMensal >= 0 ? 'fa-check-circle' : 'fa-exclamation-triangle'}}"></i>
                <strong>${{lucroMensal >= 0 ? 'VIÁVEL' : 'INVIÁVEL'}}</strong> - 
                ${{lucroMensal >= 0 ? 'O projeto é financeiramente viável.' : 'O projeto precisa de ajustes para ser viável.'}}
            </div>
        `;
    }}
    
    async function calcularViabilidade(simulacaoId = null) {{
        const btn = document.querySelector('button[onclick*="calcularViabilidade"]');
        const originalText = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processando...';
        btn.disabled = true;
        
        try {{
            // Coletar dados do formulário
            const dados = {{
                nome: document.getElementById('nome_analise').value,
                salas_disponiveis: parseInt(document.getElementById('salas_disponiveis').value) || 0
            }};
            
            // Coletar turmas
            dados.turmas = [];
            document.querySelectorAll('.turma-card').forEach(card => {{
                dados.turmas.push({{
                    nome: card.querySelector('.nome-turma-input').value,
                    disciplina: card.querySelector('.select-disciplina').value,
                    nivel: card.querySelector('.select-nivel').value,
                    capacidade: parseInt(card.querySelector('.capacidade-turma').value) || 0,
                    alunos_matriculados: parseInt(card.querySelector('.alunos-matriculados').value) || 0,
                    horas_semanais: parseFloat(card.querySelector('.horas-semanais').value) || 0,
                    dias_semana: parseInt(card.querySelector('.dias-semana').value) || 0,
                    custo_hora_professor: parseFloat(card.querySelector('.custo-hora-professor').value) || 0,
                    mensalidade_aluno: parseFloat(card.querySelector('.mensalidade-aluno').value) || 0,
                    custo_material_mensal: parseFloat(card.querySelector('.custo-material').value) || 0
                }});
            }});
            
            // Coletar custos fixos
            dados.custos = {{}};
            document.querySelectorAll('.campo-custo').forEach(campo => {{
                const categoria = campo.getAttribute('data-categoria');
                const valor = parseFloat(campo.value) || 0;
                
                if (!dados.custos[categoria]) {{
                    dados.custos[categoria] = {{}};
                }}
                // Extrai o nome do item do ID
                const item = campo.id.split('_').slice(2).join(' ').replace(/_/g, ' ');
                dados.custos[categoria][item] = valor;
            }});
            
            // Coletar alunos individuais
            dados.alunos = [];
            document.querySelectorAll('.aluno-item').forEach(item => {{
                dados.alunos.push({{
                    nome: item.querySelector('.nome-aluno').textContent,
                    mensalidade: parseFloat(item.querySelector('.valor-mensalidade').textContent) || 0
                }});
            }});
            
            // Enviar para API
            const url = simulacaoId ? `/api/atualizar_simulacao/${{simulacaoId}}` : '/api/nova_simulacao';
            const method = simulacaoId ? 'PUT' : 'POST';
            
            const response = await fetch(url, {{
                method: method,
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify(dados)
            }});
            
            if (!response.ok) {{
                const error = await response.text();
                throw new Error(error);
            }}
            
            const resultados = await response.json();
            
            // Mostrar sucesso e redirecionar
            alert('✅ Análise salva com sucesso! Redirecionando para relatório...');
            window.location.href = `/relatorio/${{resultados.id || simulacaoId}}`;
            
        }} catch (error) {{
            alert('❌ Erro: ' + error.message);
        }} finally {{
            btn.innerHTML = originalText;
            btn.disabled = false;
        }}
    }}
    
    function carregarExemplo() {{
        if (confirm('Carregar dados de exemplo?')) {{
            // Limpar turmas existentes
            document.getElementById('turmas_container').innerHTML = '';
            
            // Dados de exemplo
            const exemplos = [
                {{
                    nome: 'Matemática 1º EM',
                    disciplina: 'matematica',
                    nivel: 'medio',
                    capacidade: 30,
                    alunos: 25,
                    horas: 5,
                    dias: 2,
                    custo_hora: 65,
                    mensalidade: 280,
                    material: 150
                }},
                {{
                    nome: 'Português 9º Ano',
                    disciplina: 'portugues',
                    nivel: 'fundamental_ii',
                    capacidade: 30,
                    alunos: 22,
                    horas: 4,
                    dias: 2,
                    custo_hora: 60,
                    mensalidade: 250,
                    material: 120
                }},
                {{
                    nome: 'Inglês Intermediário',
                    disciplina: 'ingles',
                    nivel: 'medio',
                    capacidade: 25,
                    alunos: 20,
                    horas: 3,
                    dias: 2,
                    custo_hora: 75,
                    mensalidade: 320,
                    material: 200
                }}
            ];
            
            // Adicionar turmas de exemplo
            exemplos.forEach((ex, index) => {{
                setTimeout(() => {{
                    adicionarTurma();
                    const turmas = document.querySelectorAll('.turma-card');
                    const ultimaTurma = turmas[turmas.length - 1];
                    
                    ultimaTurma.querySelector('.nome-turma-input').value = ex.nome;
                    ultimaTurma.querySelector('.nome-turma').textContent = ex.nome;
                    ultimaTurma.querySelector('.select-disciplina').value = ex.disciplina;
                    ultimaTurma.querySelector('.select-nivel').value = ex.nivel;
                    ultimaTurma.querySelector('.capacidade-turma').value = ex.capacidade;
                    ultimaTurma.querySelector('.alunos-matriculados').value = ex.alunos;
                    ultimaTurma.querySelector('.horas-semanais').value = ex.horas;
                    ultimaTurma.querySelector('.dias-semana').value = ex.dias;
                    ultimaTurma.querySelector('.custo-hora-professor').value = ex.custo_hora;
                    ultimaTurma.querySelector('.mensalidade-aluno').value = ex.mensalidade;
                    ultimaTurma.querySelector('.custo-material').value = ex.material;
                    
                    calcularTurma(ultimaTurma);
                }}, index * 100);
            }});
            
            // Preencher alguns custos fixos
            setTimeout(() => {{
                document.getElementById('nome_analise').value = 'Escola Exemplo';
                document.getElementById('salas_disponiveis').value = 8;
                
                // Selecionar alguns checkboxes
                ['matematica', 'portugues', 'ingles', 'ciencias'].forEach(id => {{
                    const cb = document.getElementById('disc_' + id);
                    if (cb) cb.checked = true;
                }});
                
                // Selecionar nível
                document.getElementById('nivel_medio').checked = true;
                
                // Preencher custos fixos de exemplo
                const custosExemplo = {{
                    'custo_infraestrutura_aluguel': 3500,
                    'custo_infraestrutura_energia': 800,
                    'custo_manutencao_material_de_limpeza': 300,
                    'custo_administrativo_secretária': 2200
                }};
                
                Object.entries(custosExemplo).forEach(([id, valor]) => {{
                    const campo = document.getElementById(id);
                    if (campo) campo.value = valor;
                }});
                
                atualizarResumo();
            }}, 400);
        }}
    }}
    
    function limparFormulario() {{
        if (confirm('Tem certeza que deseja limpar todos os dados?')) {{
            // Limpa todas as turmas
            document.getElementById('turmas_container').innerHTML = '';
            
            // Limpa alunos
            document.getElementById('alunos_lista').innerHTML = '';
            
            // Limpa campos básicos
            document.getElementById('nome_analise').value = 'Minha Escola';
            document.getElementById('salas_disponiveis').value = 5;
            
            // Desmarca checkboxes e radios
            document.querySelectorAll('.disciplina-check').forEach(cb => cb.checked = false);
            document.querySelectorAll('[name="nivel"]').forEach(radio => radio.checked = false);
            
            // Limpa custos fixos
            document.querySelectorAll('.campo-custo').forEach(campo => campo.value = 0);
            
            // Limpa campos de aluno
            document.getElementById('nome_aluno').value = '';
            document.getElementById('mensalidade_aluno').value = '';
            
            // Adiciona uma turma vazia
            setTimeout(() => {{
                adicionarTurma();
                atualizarResumo();
            }}, 100);
        }}
    }}
    </script>
    '''
    
    return get_base_html("Simulação de Viabilidade", content)

@app.route('/api/nova_simulacao', methods=['POST'])
def api_nova_simulacao():
    """API para criar nova simulação"""
    try:
        dados = request.get_json()
        if not dados:
            return jsonify({'error': 'Sem dados'}), 400
        
        print("Processando nova simulação de viabilidade...")
        
        # Calcular resultados
        resultados = calcular_resultados_salas(dados)
        
        # Salvar no banco
        simulacao_id = salvar_simulacao_banco(dados, resultados)
        
        return jsonify({
            **resultados,
            'id': simulacao_id,
            'success': True,
            'message': 'Simulação salva com sucesso!'
        })
        
    except Exception as e:
        print(f"Erro na API: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/atualizar_simulacao/<int:simulacao_id>', methods=['PUT'])
def api_atualizar_simulacao(simulacao_id):
    """API para atualizar simulação existente"""
    try:
        dados = request.get_json()
        if not dados:
            return jsonify({'error': 'Sem dados'}), 400
        
        # Calcular resultados
        resultados = calcular_resultados_salas(dados)
        
        # Atualizar no banco
        atualizar_simulacao_banco(simulacao_id, dados, resultados)
        
        return jsonify({
            **resultados,
            'id': simulacao_id,
            'success': True,
            'message': 'Simulação atualizada com sucesso!'
        })
        
    except Exception as e:
        print(f"Erro na API atualizar: {e}")
        return jsonify({'error': str(e)}), 500

def calcular_resultados_salas(dados: Dict) -> Dict:
    """Calcula resultados para salas de aula"""
    # Calcular totais das turmas
    total_alunos = 0
    total_capacidade = 0
    receita_turmas = 0
    custo_turmas = 0
    total_turmas = len(dados.get('turmas', []))
    
    for turma in dados.get('turmas', []):
        alunos = turma.get('alunos_matriculados', 0)
        capacidade = turma.get('capacidade', 0)
        horas_semanais = turma.get('horas_semanais', 0)
        dias_semana = turma.get('dias_semana', 0)
        custo_hora = turma.get('custo_hora_professor', 0)
        mensalidade = turma.get('mensalidade_aluno', 0)
        material = turma.get('custo_material_mensal', 0)
        
        # Cálculos
        horas_mensais = horas_semanais * dias_semana * 4
        custo_professor = custo_hora * horas_mensais
        custo_total = custo_professor + material
        receita = alunos * mensalidade
        
        total_alunos += alunos
        total_capacidade += capacidade
        receita_turmas += receita
        custo_turmas += custo_total
    
    # Calcular custos fixos
    custos_fixos = 0
    for categoria, itens in dados.get('custos', {}).items():
        for item, valor in itens.items():
            custos_fixos += valor
    
    # Calcular alunos individuais
    receita_alunos_individuais = 0
    total_alunos_individuais = len(dados.get('alunos', []))
    for aluno in dados.get('alunos', []):
        receita_alunos_individuais += aluno.get('mensalidade', 0)
    
    # Totais gerais
    total_alunos_geral = total_alunos + total_alunos_individuais
    receita_total = receita_turmas + receita_alunos_individuais
    custo_total = custo_turmas + custos_fixos
    lucro_mensal = receita_total - custo_total
    margem_lucro = (lucro_mensal / receita_total * 100) if receita_total > 0 else 0
    ticket_medio = (receita_total / total_alunos_geral) if total_alunos_geral > 0 else 0
    ocupacao = (total_alunos / total_capacidade * 100) if total_capacidade > 0 else 0
    
    return {
        'total_turmas': total_turmas,
        'total_alunos': total_alunos_geral,
        'total_professores': total_turmas,  # Assumindo 1 professor por turma
        'investimento_inicial': 0,  # Pode ser adicionado depois
        'custo_mensal_total': custo_total,
        'receita_mensal_total': receita_total,
        'lucro_mensal': lucro_mensal,
        'margem_lucro': margem_lucro,
        'ticket_medio': ticket_medio,
        'ocupacao_salas': ocupacao,
        'custo_por_aluno': (custo_total / total_alunos_geral) if total_alunos_geral > 0 else 0
    }

def salvar_simulacao_banco(dados: Dict, resultados: Dict):
    """Salva simulação no banco de dados"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO simulacoes (
            nome, data_criacao, total_turmas, total_alunos, total_professores,
            investimento_inicial, custo_mensal_total, receita_mensal_total,
            lucro_mensal, margem_lucro, ticket_medio, dados_completos
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            dados.get('nome', 'Nova Simulação'),
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            resultados['total_turmas'],
            resultados['total_alunos'],
            resultados['total_professores'],
            resultados['investimento_inicial'],
            resultados['custo_mensal_total'],
            resultados['receita_mensal_total'],
            resultados['lucro_mensal'],
            resultados['margem_lucro'],
            resultados['ticket_medio'],
            json.dumps({
                'entrada': dados,
                'resultados': resultados,
                'turmas': dados.get('turmas', []),
                'custos': dados.get('custos', {}),
                'alunos': dados.get('alunos', [])
            })
        ))
        
        simulacao_id = cursor.lastrowid
        
        # Salvar turmas
        for turma in dados.get('turmas', []):
            cursor.execute('''
            INSERT INTO turmas (
                simulacao_id, nome_turma, nivel, disciplina, capacidade,
                alunos_matriculados, horas_semanais, dias_semana,
                custo_hora_professor, mensalidade_aluno, custo_material_mensal
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                simulacao_id,
                turma.get('nome', ''),
                turma.get('nivel', ''),
                turma.get('disciplina', ''),
                turma.get('capacidade', 0),
                turma.get('alunos_matriculados', 0),
                turma.get('horas_semanais', 0),
                turma.get('dias_semana', 0),
                turma.get('custo_hora_professor', 0),
                turma.get('mensalidade_aluno', 0),
                turma.get('custo_material_mensal', 0)
            ))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Simulação #{simulacao_id} salva no banco!")
        return simulacao_id
        
    except Exception as e:
        print(f"❌ Erro ao salvar no banco: {e}")
        return None

def atualizar_simulacao_banco(simulacao_id: int, dados: Dict, resultados: Dict):
    """Atualiza simulação existente no banco"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('''
        UPDATE simulacoes SET
            nome = ?,
            total_turmas = ?,
            total_alunos = ?,
            total_professores = ?,
            investimento_inicial = ?,
            custo_mensal_total = ?,
            receita_mensal_total = ?,
            lucro_mensal = ?,
            margem_lucro = ?,
            ticket_medio = ?,
            dados_completos = ?
        WHERE id = ?
        ''', (
            dados.get('nome', 'Simulação Atualizada'),
            resultados['total_turmas'],
            resultados['total_alunos'],
            resultados['total_professores'],
            resultados['investimento_inicial'],
            resultados['custo_mensal_total'],
            resultados['receita_mensal_total'],
            resultados['lucro_mensal'],
            resultados['margem_lucro'],
            resultados['ticket_medio'],
            json.dumps({
                'entrada': dados,
                'resultados': resultados,
                'turmas': dados.get('turmas', []),
                'custos': dados.get('custos', {}),
                'alunos': dados.get('alunos', [])
            }),
            simulacao_id
        ))
        
        # Remover turmas antigas
        cursor.execute('DELETE FROM turmas WHERE simulacao_id = ?', (simulacao_id,))
        
        # Salvar novas turmas
        for turma in dados.get('turmas', []):
            cursor.execute('''
            INSERT INTO turmas (
                simulacao_id, nome_turma, nivel, disciplina, capacidade,
                alunos_matriculados, horas_semanais, dias_semana,
                custo_hora_professor, mensalidade_aluno, custo_material_mensal
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                simulacao_id,
                turma.get('nome', ''),
                turma.get('nivel', ''),
                turma.get('disciplina', ''),
                turma.get('capacidade', 0),
                turma.get('alunos_matriculados', 0),
                turma.get('horas_semanais', 0),
                turma.get('dias_semana', 0),
                turma.get('custo_hora_professor', 0),
                turma.get('mensalidade_aluno', 0),
                turma.get('custo_material_mensal', 0)
            ))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Simulação #{simulacao_id} atualizada!")
        
    except Exception as e:
        print(f"❌ Erro ao atualizar no banco: {e}")

@app.route('/historico')
def historico():
    """Página com histórico de simulações"""
    try:
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT id, nome, data_criacao, total_turmas, total_alunos,
               receita_mensal_total, custo_mensal_total, lucro_mensal,
               margem_lucro, ticket_medio
        FROM simulacoes 
        ORDER BY data_criacao DESC 
        LIMIT 20
        ''')
        
        simulacoes = cursor.fetchall()
        conn.close()
        
        # HTML para tabela
        tabela_html = ""
        if simulacoes:
            tabela_html = '''
            <div class="card">
                <div class="card-header bg-primary text-white">
                    <h5 class="mb-0"><i class="fas fa-history"></i> Histórico de Análises</h5>
                </div>
                <div class="card-body p-0">
                    <div class="table-responsive">
                        <table class="table table-hover mb-0">
                            <thead class="table-dark">
                                <tr>
                                    <th>Nome</th>
                                    <th>Data</th>
                                    <th class="text-center">Turmas</th>
                                    <th class="text-center">Alunos</th>
                                    <th class="text-end">Receita</th>
                                    <th class="text-end">Custo</th>
                                    <th class="text-end">Lucro</th>
                                    <th class="text-center">Margem</th>
                                    <th class="text-center">Ações</th>
                                </tr>
                            </thead>
                            <tbody>
            '''
            
            for sim in simulacoes:
                tabela_html += f'''
                                <tr>
                                    <td>{sim['nome']}</td>
                                    <td>{sim['data_criacao'][:10]}</td>
                                    <td class="text-center">{sim['total_turmas']}</td>
                                    <td class="text-center">{sim['total_alunos']}</td>
                                    <td class="text-end text-success">R$ {sim['receita_mensal_total']:,.2f}</td>
                                    <td class="text-end text-danger">R$ {sim['custo_mensal_total']:,.2f}</td>
                                    <td class="text-end { 'text-success' if sim['lucro_mensal'] > 0 else 'text-danger' }">
                                        R$ {sim['lucro_mensal']:,.2f}
                                    </td>
                                    <td class="text-center">
                                        <span class="badge { 'bg-success' if sim['margem_lucro'] >= 20 else 'bg-warning' if sim['margem_lucro'] >= 10 else 'bg-danger' }">
                                            {sim['margem_lucro']:.1f}%
                                        </span>
                                    </td>
                                    <td class="text-center">
                                        <div class="btn-group btn-group-sm">
                                            <a href="/simulacao/{sim['id']}" class="btn btn-warning" title="Editar">
                                                <i class="fas fa-edit"></i>
                                            </a>
                                            <a href="/relatorio/{sim['id']}" class="btn btn-info" title="Ver Relatório">
                                                <i class="fas fa-eye"></i>
                                            </a>
                                            <button class="btn btn-danger" title="Excluir" onclick="excluirSimulacao({sim['id']})">
                                                <i class="fas fa-trash"></i>
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                '''
            
            tabela_html += '''
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
            '''
        else:
            tabela_html = '''
            <div class="alert alert-info">
                <i class="fas fa-info-circle"></i> Nenhuma análise encontrada. 
                <a href="/simulacao" class="alert-link">Crie sua primeira análise</a>.
            </div>
            '''
        
        content = f'''
        <div class="row">
            <div class="col-lg-12">
                <h3 class="mb-4">
                    <i class="fas fa-history"></i> Histórico de Análises
                </h3>
                
                {tabela_html}
                
                <div class="mt-4">
                    <a href="/simulacao" class="btn btn-primary">
                        <i class="fas fa-plus"></i> Nova Análise
                    </a>
                    <a href="/" class="btn btn-outline-secondary ms-2">
                        <i class="fas fa-home"></i> Voltar ao Início
                    </a>
                </div>
            </div>
        </div>
        
        <script>
        function excluirSimulacao(id) {{
            if (confirm('Tem certeza que deseja excluir esta análise?')) {{
                fetch('/api/excluir_simulacao/' + id, {{
                    method: 'DELETE'
                }})
                .then(response => response.json())
                .then(data => {{
                    if (data.success) {{
                        location.reload();
                    }} else {{
                        alert('Erro ao excluir: ' + (data.error || 'Erro desconhecido'));
                    }}
                }})
                .catch(error => {{
                    alert('Erro: ' + error.message);
                }});
            }}
        }}
        </script>
        '''
        
        return get_base_html("Histórico", content)
        
    except Exception as e:
        print(f"Erro no histórico: {e}")
        return redirect('/')

@app.route('/relatorio/<int:simulacao_id>')
def relatorio(simulacao_id):
    """Página de relatório detalhado"""
    try:
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM simulacoes WHERE id = ?', (simulacao_id,))
        simulacao = cursor.fetchone()
        
        if not simulacao:
            return redirect('/historico')
        
        dados_completos = json.loads(simulacao['dados_completos'])
        resultados = dados_completos.get('resultados', {})
        turmas = dados_completos.get('turmas', [])
        custos = dados_completos.get('custos', {})
        
        conn.close()
        
        # HTML para turmas
        turmas_html = ""
        for turma in turmas:
            disciplinas_info = DISCIPLINAS.get(turma.get('disciplina', ''), {'nome': 'Não especificada', 'cor': '#ccc'})
            niveis_info = NIVEIS_ENSINO.get(turma.get('nivel', ''), {'nome': 'Não especificado'})
            
            # Calcular valores para esta turma
            alunos = turma.get('alunos_matriculados', 0)
            capacidade = turma.get('capacidade', 0)
            horas_semanais = turma.get('horas_semanais', 0)
            dias_semana = turma.get('dias_semana', 0)
            custo_hora = turma.get('custo_hora_professor', 0)
            mensalidade = turma.get('mensalidade_aluno', 0)
            material = turma.get('custo_material_mensal', 0)
            
            horas_mensais = horas_semanais * dias_semana * 4
            custo_professor = custo_hora * horas_mensais
            custo_total = custo_professor + material
            receita = alunos * mensalidade
            lucro = receita - custo_total
            margem = (lucro / receita * 100) if receita > 0 else 0
            ocupacao = (alunos / capacidade * 100) if capacidade > 0 else 0
            
            turmas_html += f'''
            <div class="col-md-6">
                <div class="card mb-4" style="border-left: 5px solid {disciplinas_info['cor']};">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <h6 class="mb-0">
                            <i class="fas fa-chalkboard"></i> {turma.get('nome', 'Turma sem nome')}
                        </h6>
                        <span class="nivel-badge">{niveis_info['nome']}</span>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-6">
                                <small class="text-muted">Disciplina</small>
                                <p class="mb-1">
                                    <span class="disciplina-badge" style="background-color: {disciplinas_info['cor']};">
                                        {disciplinas_info['nome']}
                                    </span>
                                </p>
                            </div>
                            <div class="col-6">
                                <small class="text-muted">Ocupação</small>
                                <p class="mb-1">
                                    <span class="badge { 'bg-success' if ocupacao >= 80 else 'bg-warning' if ocupacao >= 50 else 'bg-danger' }">
                                        {ocupacao:.1f}% ({alunos}/{capacidade})
                                    </span>
                                </p>
                            </div>
                        </div>
                        
                        <div class="row mt-2">
                            <div class="col-6">
                                <small class="text-muted">Carga horária</small>
                                <p class="mb-1">{horas_semanais}h/semana × {dias_semana} dias</p>
                            </div>
                            <div class="col-6">
                                <small class="text-muted">Custo/hora professor</small>
                                <p class="mb-1">R$ {custo_hora:.2f}</p>
                            </div>
                        </div>
                        
                        <div class="row mt-3 text-center">
                            <div class="col-4">
                                <div class="small text-muted">Custo/Mês</div>
                                <div class="text-danger">R$ {custo_total:,.2f}</div>
                            </div>
                            <div class="col-4">
                                <div class="small text-muted">Receita/Mês</div>
                                <div class="text-success">R$ {receita:,.2f}</div>
                            </div>
                            <div class="col-4">
                                <div class="small text-muted">Lucro/Mês</div>
                                <div class="{ 'text-success' if lucro >= 0 else 'text-danger' }">R$ {lucro:,.2f}</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            '''
        
        # HTML para custos fixos
        custos_html = ""
        total_custos_fixos = 0
        
        for categoria, itens in custos.items():
            titulo_categoria = categoria.replace('_', ' ').title()
            custos_categoria = 0
            
            itens_html = ""
            for item, valor in itens.items():
                if valor > 0:
                    custos_categoria += valor
                    total_custos_fixos += valor
                    itens_html += f'''
                    <tr>
                        <td>{item}</td>
                        <td class="text-end">R$ {valor:,.2f}</td>
                    </tr>
                    '''
            
            if itens_html:
                custos_html += f'''
                <div class="col-md-6">
                    <div class="card mb-4">
                        <div class="card-header bg-secondary text-white">
                            <h6 class="mb-0">{titulo_categoria}</h6>
                        </div>
                        <div class="card-body p-0">
                            <table class="table table-sm mb-0">
                                <tbody>
                                    {itens_html}
                                    <tr class="table-light">
                                        <td><strong>Total {titulo_categoria}</strong></td>
                                        <td class="text-end"><strong>R$ {custos_categoria:,.2f}</strong></td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
                '''
        
        content = f'''
        <div class="row">
            <div class="col-lg-12">
                <div class="card mb-4">
                    <div class="card-header bg-primary text-white">
                        <h3 class="mb-0">
                            <i class="fas fa-file-alt"></i> Relatório: {simulacao['nome']}
                        </h3>
                        <small class="opacity-75">Criado em: {simulacao['data_criacao']}</small>
                    </div>
                    <div class="card-body">
                        <!-- Indicadores principais -->
                        <div class="row mb-4">
                            <div class="col-md-3">
                                <div class="indicador">
                                    <div class="label">Turmas Ativas</div>
                                    <div class="valor" style="color: #4361ee;">{resultados.get('total_turmas', 0)}</div>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="indicador">
                                    <div class="label">Alunos</div>
                                    <div class="valor" style="color: #4cc9f0;">{resultados.get('total_alunos', 0)}</div>
                                    <small>Ocupação: {resultados.get('ocupacao_salas', 0):.1f}%</small>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="indicador">
                                    <div class="label">Ticket Médio</div>
                                    <div class="valor" style="color: #28a745;">R$ {resultados.get('ticket_medio', 0):.2f}</div>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="indicador">
                                    <div class="label">Margem</div>
                                    <div class="valor" style="color: { 'green' if resultados.get('margem_lucro', 0) >= 0 else 'red' };">
                                        {resultados.get('margem_lucro', 0):.1f}%
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Resumo financeiro -->
                        <div class="row mb-4">
                            <div class="col-md-4">
                                <div class="resultado-card">
                                    <h6><i class="fas fa-money-bill-wave"></i> Receita Mensal</h6>
                                    <h2>R$ {resultados.get('receita_mensal_total', 0):,.2f}</h2>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="resultado-card" style="background: linear-gradient(135deg, #f72585 0%, #7209b7 100%);">
                                    <h6><i class="fas fa-calculator"></i> Custo Mensal</h6>
                                    <h2>R$ {resultados.get('custo_mensal_total', 0):,.2f}</h2>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="resultado-card" style="background: linear-gradient(135deg, { '#4cc9f0' if resultados.get('lucro_mensal', 0) >= 0 else '#dc3545' } 0%, { '#4361ee' if resultados.get('lucro_mensal', 0) >= 0 else '#f72585' } 100%);">
                                    <h6><i class="fas fa-chart-line"></i> Lucro Mensal</h6>
                                    <h2>R$ {resultados.get('lucro_mensal', 0):,.2f}</h2>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Turmas -->
                        <h5 class="mt-5 mb-3">
                            <i class="fas fa-chalkboard"></i> Turmas ({len(turmas)})
                        </h5>
                        <div class="row">
                            {turmas_html if turmas_html else '<div class="col-12"><p class="text-center text-muted">Nenhuma turma cadastrada.</p></div>'}
                        </div>
                        
                        <!-- Custos Fixos -->
                        <h5 class="mt-5 mb-3">
                            <i class="fas fa-calculator"></i> Custos Fixos Mensais
                        </h5>
                        <div class="row">
                            {custos_html if custos_html else '<div class="col-12"><p class="text-center text-muted">Nenhum custo fixo cadastrado.</p></div>'}
                        </div>
                        
                        <!-- Gráfico -->
                        <div class="row mt-5">
                            <div class="col-12">
                                <div class="card">
                                    <div class="card-header bg-info text-white">
                                        <h5 class="mb-0"><i class="fas fa-chart-pie"></i> Distribuição Financeira</h5>
                                    </div>
                                    <div class="card-body">
                                        <div class="chart-container">
                                            <canvas id="graficoFinancas"></canvas>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Ações -->
                        <div class="row mt-4">
                            <div class="col-12 text-center">
                                <a href="/simulacao/{simulacao_id}" class="btn btn-primary btn-lg me-3">
                                    <i class="fas fa-edit"></i> Editar Análise
                                </a>
                                <a href="/historico" class="btn btn-secondary btn-lg me-3">
                                    <i class="fas fa-history"></i> Voltar ao Histórico
                                </a>
                                <button onclick="window.print()" class="btn btn-success btn-lg">
                                    <i class="fas fa-print"></i> Imprimir Relatório
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
        document.addEventListener('DOMContentLoaded', function() {{
            // Gráfico de pizza
            const ctx = document.getElementById('graficoFinancas').getContext('2d');
            const receita = {resultados.get('receita_mensal_total', 0)};
            const custo = {resultados.get('custo_mensal_total', 0)};
            const lucro = {resultados.get('lucro_mensal', 0)};
            
            new Chart(ctx, {{
                type: 'pie',
                data: {{
                    labels: ['Receita Total', 'Custos Totais', 'Lucro Líquido'],
                    datasets: [{{
                        data: [receita, custo, Math.max(lucro, 0)],
                        backgroundColor: [
                            '#28a745',  // Verde para receita
                            '#dc3545',  // Vermelho para custos
                            '#17a2b8'   // Azul para lucro
                        ],
                        borderWidth: 1
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        legend: {{
                            position: 'bottom'
                        }},
                        tooltip: {{
                            callbacks: {{
                                label: function(context) {{
                                    const label = context.label || '';
                                    const value = context.raw || 0;
                                    const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                    const percentage = Math.round((value / total) * 100);
                                    return `${{label}}: R$ ${{value.toLocaleString('pt-BR', {{minimumFractionDigits: 2}})}} (${{percentage}}%)`;
                                }}
                            }}
                        }}
                    }}
                }}
            }});
        }});
        </script>
        '''
        
        return get_base_html(f"Relatório: {simulacao['nome']}", content)
        
    except Exception as e:
        print(f"Erro no relatório: {e}")
        return redirect('/historico')

@app.route('/exemplo')
def exemplo():
    """Página com exemplo de uso"""
    content = '''
    <div class="row">
        <div class="col-lg-10 mx-auto">
            <div class="card">
                <div class="card-header bg-primary text-white">
                    <h3 class="mb-0"><i class="fas fa-graduation-cap"></i> Exemplo Prático de Uso</h3>
                </div>
                <div class="card-body">
                    <h4 class="mb-3">Cenário: Escola de Ensino Médio</h4>
                    
                    <div class="row">
                        <div class="col-md-6">
                            <div class="card mb-4">
                                <div class="card-header bg-info text-white">
                                    <h5 class="mb-0"><i class="fas fa-chalkboard-teacher"></i> Turmas Exemplo</h5>
                                </div>
                                <div class="card-body">
                                    <table class="table table-sm">
                                        <thead>
                                            <tr>
                                                <th>Turma</th>
                                                <th class="text-center">Alunos</th>
                                                <th class="text-end">Mensalidade</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            <tr>
                                                <td>Matemática 1º EM</td>
                                                <td class="text-center">25/30</td>
                                                <td class="text-end">R$ 280,00</td>
                                            </tr>
                                            <tr>
                                                <td>Português 9º Ano</td>
                                                <td class="text-center">22/30</td>
                                                <td class="text-end">R$ 250,00</td>
                                            </tr>
                                            <tr>
                                                <td>Inglês Intermediário</td>
                                                <td class="text-center">20/25</td>
                                                <td class="text-end">R$ 320,00</td>
                                            </tr>
                                            <tr class="table-light">
                                                <td><strong>Total</strong></td>
                                                <td class="text-center"><strong>67/85</strong></td>
                                                <td class="text-end"><strong>R$ 850,00 (média)</strong></td>
                                            </tr>
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                        
                        <div class="col-md-6">
                            <div class="card mb-4">
                                <div class="card-header bg-success text-white">
                                    <h5 class="mb-0"><i class="fas fa-calculator"></i> Resultados Financeiros</h5>
                                </div>
                                <div class="card-body">
                                    <table class="table table-sm">
                                        <tbody>
                                            <tr>
                                                <td>Receita Mensal Total:</td>
                                                <td class="text-end text-success">R$ 17.960,00</td>
                                            </tr>
                                            <tr>
                                                <td>Custo Professores:</td>
                                                <td class="text-end text-danger">R$ 10.240,00</td>
                                            </tr>
                                            <tr>
                                                <td>Custos Fixos:</td>
                                                <td class="text-end text-danger">R$ 4.800,00</td>
                                            </tr>
                                            <tr class="table-light">
                                                <td><strong>Lucro Mensal:</strong></td>
                                                <td class="text-end"><strong class="text-success">R$ 2.920,00</strong></td>
                                            </tr>
                                            <tr>
                                                <td>Margem de Lucro:</td>
                                                <td class="text-end"><span class="badge bg-success">16,3%</span></td>
                                            </tr>
                                            <tr>
                                                <td>Ticket Médio:</td>
                                                <td class="text-end">R$ 268,06</td>
                                            </tr>
                                            <tr>
                                                <td>Ocupação das Salas:</td>
                                                <td class="text-end"><span class="badge bg-success">78,8%</span></td>
                                            </tr>
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="alert alert-info">
                        <h5><i class="fas fa-lightbulb"></i> Conclusão do Exemplo</h5>
                        <p>Esta escola é <strong>financeiramente viável</strong> com margem de lucro de 16,3%. 
                        Para melhorar os resultados, poderia:</p>
                        <ul>
                            <li>Aumentar a ocupação das turmas de 78,8% para pelo menos 85%</li>
                            <li>Revisar os custos fixos para possíveis reduções</li>
                            <li>Oferecer pacotes semestrais com desconto para aumentar a receita</li>
                            <li>Diversificar com novas disciplinas em horários ociosos</li>
                        </ul>
                    </div>
                    
                    <div class="text-center mt-4">
                        <a href="/simulacao" class="btn btn-primary btn-lg">
                            <i class="fas fa-play-circle"></i> Criar Minha Própria Análise
                        </a>
                        <button onclick="carregarExemploNoForm()" class="btn btn-outline-primary btn-lg ms-3">
                            <i class="fas fa-magic"></i> Usar Este Exemplo
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
    function carregarExemploNoForm() {{
        if (confirm('Carregar dados do exemplo no formulário de simulação?')) {{
            window.location.href = '/simulacao';
            // O exemplo será carregado automaticamente pelo JavaScript na página de simulação
        }}
    }}
    </script>
    '''
    
    return get_base_html("Exemplo Prático", content)

@app.route('/api/excluir_simulacao/<int:simulacao_id>', methods=['DELETE'])
def api_excluir_simulacao(simulacao_id):
    """API para excluir simulação"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Primeiro excluir turmas relacionadas
        cursor.execute('DELETE FROM turmas WHERE simulacao_id = ?', (simulacao_id,))
        
        # Depois excluir a simulação
        cursor.execute('DELETE FROM simulacoes WHERE id = ?', (simulacao_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Análise excluída com sucesso!'})
        
    except Exception as e:
        print(f"Erro ao excluir simulação: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Configuração segura para execução
    import os
    
    # Remove variáveis problemáticas
    for key in list(os.environ.keys()):
        if 'WERKZEUG' in key.upper():
            os.environ.pop(key, None)
    
    print("=" * 70)
    print("🚀 SISTEMA DE VIABILIDADE DE SALAS DE AULA")
    print("📊 Iniciando servidor...")
    print("=" * 70)
    
    # Configurações seguras
    app.run(
        host='localhost',
        port=5000,
        debug=False,        # IMPORTANTE: False para evitar problemas
        use_reloader=False,  # IMPORTANTE: False
        threaded=True
    )