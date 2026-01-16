$(document).ready(function() {
    // Estado da aplicação
    let estado = {
        niveisSelecionados: [],
        disciplinasSelecionadas: [],
        turmasExpandidas: new Set()
    };
    
    // Inicializar tooltips do Bootstrap
    $('[data-bs-toggle="tooltip"]').tooltip();
    
    // ========================
    // MANIPULAÇÃO DE NÍVEIS
    // ========================
    
    $('.btn-selecionar-nivel').on('click', function() {
        const nivelId = $(this).data('nivel');
        const $card = $(this).closest('.nivel-card');
        
        if ($(this).hasClass('btn-outline-primary')) {
            // Selecionar
            $(this).removeClass('btn-outline-primary').addClass('btn-primary');
            $(this).html('<i class="fas fa-check me-1"></i>Selecionado');
            $card.addClass('active');
            
            estado.niveisSelecionados.push(nivelId);
        } else {
            // Desselecionar
            $(this).removeClass('btn-primary').addClass('btn-outline-primary');
            $(this).text('Selecionar');
            $card.removeClass('active');
            
            estado.niveisSelecionados = estado.niveisSelecionados.filter(id => id !== nivelId);
        }
        
        atualizarNiveisSelecionadosTexto();
    });
    
    function atualizarNiveisSelecionadosTexto() {
        const $texto = $('#niveis-selecionados-texto');
        
        if (estado.niveisSelecionados.length === 0) {
            $texto.text('Nenhum');
        } else {
            // Mapear IDs para nomes (simplificado - na prática viria do backend)
            const nomes = estado.niveisSelecionados.map(id => {
                switch(id) {
                    case 'fund1': return 'Fundamental I';
                    case 'fund2': return 'Fundamental II';
                    case 'medio': return 'Ensino Médio';
                    case 'prevest': return 'Pré-Vestibular';
                    default: return id;
                }
            });
            $texto.text(nomes.join(', '));
        }
    }
    
    // ========================
    // MANIPULAÇÃO DE DISCIPLINAS
    // ========================
    
    $('.checkbox-disciplina').on('change', function() {
        const disciplinaId = parseInt($(this).val());
        const disciplinaNome = $(this).data('nome');
        const disciplinaCusto = parseFloat($(this).data('custo'));
        
        if ($(this).is(':checked')) {
            estado.disciplinasSelecionadas.push({
                id: disciplinaId,
                nome: disciplinaNome,
                custo: disciplinaCusto
            });
            $(this).closest('.disciplina-item').addClass('border-primary');
        } else {
            estado.disciplinasSelecionadas = estado.disciplinasSelecionadas.filter(d => d.id !== disciplinaId);
            $(this).closest('.disciplina-item').removeClass('border-primary');
        }
    });
    
    // ========================
    // MANIPULAÇÃO DE TURMAS
    // ========================
    
    // Alternar expansão da turma
    window.toggleTurma = function(turmaId) {
        const $detalhes = $(`#detalhes-turma-${turmaId}`);
        const $toggleBtn = $(`#detalhes-turma-${turmaId}`).closest('.turma-card').find('.toggle-btn');
        
        if ($detalhes.hasClass('show')) {
            // Fechar
            $detalhes.removeClass('show');
            $toggleBtn.find('i').removeClass('fa-chevron-up').addClass('fa-chevron-down');
            $toggleBtn.removeClass('rotated');
            
            // Remover do estado
            estado.turmasExpandidas.delete(turmaId);
        } else {
            // Abrir
            $detalhes.addClass('show');
            $toggleBtn.find('i').removeClass('fa-chevron-down').addClass('fa-chevron-up');
            $toggleBtn.addClass('rotated');
            
            // Adicionar ao estado
            estado.turmasExpandidas.add(turmaId);
        }
    };
    
    // Atualizar turma quando campo muda
    $(document).on('input change', '.campo-turma', function() {
        const turmaId = $(this).data('turma-id');
        const campo = $(this).data('campo');
        const valor = $(this).val();
        
        // Validar capacidade máxima para alunos
        if (campo === 'alunos_matriculados') {
            const capacidade = $(`input[data-turma-id="${turmaId}"][data-campo="capacidade"]`).val();
            if (parseInt(valor) > parseInt(capacidade)) {
                $(this).val(capacidade);
                alert('O número de alunos não pode exceder a capacidade máxima!');
                return;
            }
        }
        
        // Enviar atualização para o servidor
        atualizarTurma(turmaId, campo, valor);
    });
    
    // Nova turma
    $('#btn-nova-turma').on('click', function() {
        // Abrir modal para criar nova turma
        $('#modalTurma .modal-title').html('<i class="fas fa-plus-circle me-2"></i>Nova Turma');
        
        // Carregar formulário via AJAX
        $.get('/turmas', function(data) {
            $('#modal-turma-body').html(data);
            $('#modalTurma').modal('show');
        });
    });
    
    // Remover turma
    $(document).on('click', '.btn-remover-turma', function() {
        const turmaId = $(this).data('turma-id');
        
        if (confirm('Tem certeza que deseja remover esta turma?')) {
            $.post(`/remover_turma/${turmaId}`, function(response) {
                if (response.success) {
                    $(`[data-turma-id="${turmaId}"]`).remove();
                    calcularViabilidade();
                    
                    // Atualizar contador se não houver mais turmas
                    if ($('.turma-card').length === 0) {
                        $('#turmas-container').html(`
                            <div class="text-center py-5 text-muted">
                                <i class="fas fa-users fa-3x mb-3"></i>
                                <p class="mb-1">Nenhuma turma adicionada</p>
                                <p class="small">Clique em "Nova Turma" para começar</p>
                            </div>
                        `);
                    }
                }
            });
        }
    });
    
    // ========================
    // CUSTOS FIXOS
    // ========================
    
    // Atualizar custos fixos automaticamente
    $('.custo-fixo').on('input', function() {
        calcularTotaisParciais();
    });
    
    function calcularTotaisParciais() {
        // Calcular total dos custos fixos
        let totalCustosFixos = 0;
        
        $('.custo-fixo').each(function() {
            const valor = parseFloat($(this).val()) || 0;
            totalCustosFixos += valor;
        });
        
        // Atualizar display
        $('#total-custos-fixos').text(formatarMoeda(totalCustosFixos));
    }
    
    // ========================
    // CÁLCULOS PRINCIPAIS
    // ========================
    
    $('#btn-calcular').on('click', function() {
        calcularViabilidade();
    });
    
    function calcularViabilidade() {
        // Coletar dados do formulário
        const dados = {
            custos_fixos: {},
            acr_inicial: parseFloat($('#acr-inicial').val()) || 0
        };
        
        // Coletar custos fixos
        $('.custo-fixo').each(function() {
            const id = $(this).attr('id');
            const valor = parseFloat($(this).val()) || 0;
            dados.custos_fixos[id] = valor;
        });
        
        // Enviar para o servidor
        $.post('/calcular_viabilidade', JSON.stringify(dados), function(response) {
            if (response.success) {
                atualizarResultados(response.resultados);
                atualizarResultadosTurmas(response.resultados.resultados_turmas);
            }
        }, 'json');
    }
    
    function atualizarResultados(resultados) {
        // Atualizar totais gerais
        $('#total-receita').text(formatarMoeda(resultados.total_receita));
        $('#total-custos-variaveis').text(formatarMoeda(resultados.total_custos_variaveis));
        $('#total-custos-fixos').text(formatarMoeda(resultados.total_custos_fixos));
        $('#resultado-mensal').text(formatarMoeda(resultados.resultado_mensal));
        $('#acr-atual').text(formatarMoeda(resultados.acr_atual));
        
        // Destacar resultado mensal
        const $resultado = $('#resultado-mensal');
        $resultado.removeClass('text-success text-danger');
        
        if (resultados.resultado_mensal > 0) {
            $resultado.addClass('text-success');
        } else if (resultados.resultado_mensal < 0) {
            $resultado.addClass('text-danger');
        }
    }
    
    function atualizarResultadosTurmas(resultadosTurmas) {
        resultadosTurmas.forEach(resultado => {
            const $badge = $(`#resultado-turma-${resultado.id}`);
            $badge.text(formatarMoeda(resultado.resultado));
            
            // Aplicar classe baseada no resultado
            $badge.removeClass('resultado-positivo resultado-negativo resultado-neutro');
            
            if (resultado.resultado > 0) {
                $badge.addClass('resultado-positivo');
            } else if (resultado.resultado < 0) {
                $badge.addClass('resultado-negativo');
            } else {
                $badge.addClass('resultado-neutro');
            }
        });
    }
    
    // ========================
    // FUNÇÕES UTILITÁRIAS
    // ========================
    
    function formatarMoeda(valor) {
        return new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: 'BRL',
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }).format(valor);
    }
    
    function atualizarTurma(turmaId, campo, valor) {
        const dados = {};
        dados[campo] = campo.includes('id') || campo.includes('capacidade') || 
                      campo.includes('alunos') || campo.includes('horas') || 
                      campo.includes('dias') ? parseInt(valor) || null : 
                      campo.includes('mensalidade') || campo.includes('custo') ? 
                      parseFloat(valor) || 0 : valor;
        
        $.post(`/atualizar_turma/${turmaId}`, JSON.stringify(dados), function(response) {
            if (response.success) {
                // Recalcular após atualização
                setTimeout(calcularViabilidade, 100);
            }
        }, 'json');
    }
    
    // ========================
    // CONTROLES GERAIS
    // ========================
    
    // Carregar exemplo
    $('#btn-exemplo').on('click', function() {
        if (confirm('Isso substituirá todos os dados atuais. Continuar?')) {
            $.post('/carregar_exemplo', function(response) {
                if (response.success) {
                    location.reload(); // Recarregar página para atualizar dados
                }
            });
        }
    });
    
    // Limpar tudo
    $('#btn-limpar').on('click', function() {
        if (confirm('Tem certeza que deseja limpar todos os dados?')) {
            $.post('/limpar_tudo', function(response) {
                if (response.success) {
                    location.reload(); // Recarregar página
                }
            });
        }
    });
    
    // ACR Inicial
    $('#acr-inicial').on('input', function() {
        calcularViabilidade();
    });
    
    // Inicializar cálculos
    calcularTotaisParciais();
});