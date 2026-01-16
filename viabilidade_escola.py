import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
from datetime import datetime
from calculos import calcular_viabilidade, formatar_moeda
from turmas_manager import Turma, GerenciadorTurmas

class AplicacaoViabilidadeEscola:
    def __init__(self, root):
        self.root = root
        self.root.title("Calculadora de Viabilidade - Escola")
        self.root.geometry("1400x800")
        self.root.configure(bg='#f0f2f5')
        
        # Inicializar estado
        self.estado = {
            'niveis_selecionados': [],
            'disciplinas_selecionadas': [],
            'turmas': [],
            'acr_inicial': 0.0,
            'custos_fixos': {
                'aluguel': 0.0, 'condominio': 0.0, 'agua': 0.0, 'energia': 0.0,
                'internet': 0.0, 'limpeza': 0.0, 'projetor': 0.0, 'computadores': 0.0,
                'moveis': 0.0, 'arcondicionado': 0.0, 'divulgacao': 0.0,
                'material_grafico': 0.0, 'site': 0.0, 'redes_sociais': 0.0
            },
            'resultados': {
                'total_receita': 0.0, 'total_custos_variaveis': 0.0,
                'total_custos_fixos': 0.0, 'resultado_mensal': 0.0, 'acr_atual': 0.0
            }
        }
        
        self.gerenciador_turmas = GerenciadorTurmas()
        self.turma_id_counter = 1
        
        # Dados das disciplinas
        self.disciplinas = [
            {"