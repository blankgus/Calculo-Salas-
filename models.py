class Disciplina:
    def __init__(self, id, nome, custo_hora):
        self.id = id
        self.nome = nome
        self.custo_hora = custo_hora

class NivelEnsino:
    def __init__(self, id, nome, descricao):
        self.id = id
        self.nome = nome
        self.descricao = descricao

class Turma:
    def __init__(self, id, disciplina_id, nivel_id, capacidade, alunos_matriculados,
                 horas_semana, dias_semana, custo_hora_professor, mensalidade_aluno,
                 custo_material_mes):
        self.id = id
        self.disciplina_id = disciplina_id
        self.nivel_id = nivel_id
        self.capacidade = capacidade
        self.alunos_matriculados = alunos_matriculados
        self.horas_semana = horas_semana
        self.dias_semana = dias_semana
        self.custo_hora_professor = custo_hora_professor
        self.mensalidade_aluno = mensalidade_aluno
        self.custo_material_mes = custo_material_mes
    
    def calcular_custo_professor_mes(self):
        """Calcula custo mensal do professor"""
        semanas_mes = 4.33
        return self.horas_semana * semanas_mes * self.custo_hora_professor
    
    def calcular_custo_total(self):
        """Calcula custo total da turma (professor + material)"""
        return self.calcular_custo_professor_mes() + self.custo_material_mes
    
    def calcular_receita(self):
        """Calcula receita mensal da turma"""
        return self.alunos_matriculados * self.mensalidade_aluno
    
    def calcular_resultado(self):
        """Calcula resultado financeiro da turma"""
        return self.calcular_receita() - self.calcular_custo_total()

def calcular_viabilidade(turmas, custos_fixos, acr_inicial):
    """
    Calcula a viabilidade financeira completa
    
    Args:
        turmas: Lista de dicionários com dados das turmas
        custos_fixos: Dicionário com custos fixos mensais
        acr_inicial: Valor inicial do ACR
    
    Returns:
        Dicionário com todos os resultados calculados
    """
    total_custos_fixos = sum(custos_fixos.values())
    
    total_receita = 0
    total_custos_variaveis = 0
    
    # Calcular resultados de cada turma
    resultados_turmas = []
    for turma_data in turmas:
        # Criar objeto Turma temporário para cálculos
        turma_obj = Turma(
            id=turma_data['id'],
            disciplina_id=turma_data.get('disciplina_id'),
            nivel_id=turma_data.get('nivel_id'),
            capacidade=turma_data.get('capacidade', 0),
            alunos_matriculados=turma_data.get('alunos_matriculados', 0),
            horas_semana=turma_data.get('horas_semana', 0),
            dias_semana=turma_data.get('dias_semana', 0),
            custo_hora_professor=turma_data.get('custo_hora_professor', 0),
            mensalidade_aluno=turma_data.get('mensalidade_aluno', 0),
            custo_material_mes=turma_data.get('custo_material_mes', 0)
        )
        
        receita_turma = turma_obj.calcular_receita()
        custo_turma = turma_obj.calcular_custo_total()
        resultado_turma = turma_obj.calcular_resultado()
        
        total_receita += receita_turma
        total_custos_variaveis += custo_turma
        
        resultados_turmas.append({
            'id': turma_data['id'],
            'receita': receita_turma,
            'custo': custo_turma,
            'resultado': resultado_turma,
            'disciplina_id': turma_data.get('disciplina_id'),
            'nivel_id': turma_data.get('nivel_id')
        })
    
    # Calcular totais
    resultado_mensal = total_receita - total_custos_variaveis - total_custos_fixos
    acr_atual = acr_inicial + resultado_mensal
    
    return {
        'total_receita': total_receita,
        'total_custos_variaveis': total_custos_variaveis,
        'total_custos_fixos': total_custos_fixos,
        'resultado_mensal': resultado_mensal,
        'acr_atual': acr_atual,
        'resultados_turmas': resultados_turmas
    }

def formatar_moeda(valor):
    """Formata valor em moeda brasileira"""
    return f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')