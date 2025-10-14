import pytest
import pandas as pd
from pathlib import Path

# Importa a classe que queremos testar
from lotofacil_analyzer import AnalisadorLotofacil

# Conteúdo do CSV falso que será usado nos testes.
# Usamos um histórico pequeno e controlado para ter resultados previsíveis.
MOCK_CSV_DATA = """Concurso;Data Sorteio;Bola1;Bola2;Bola3;Bola4;Bola5;Bola6;Bola7;Bola8;Bola9;Bola10;Bola11;Bola12;Bola13;Bola14;Bola15
1;01/01/2023;1;2;3;4;5;6;7;8;9;10;11;12;13;14;15
2;02/01/2023;1;2;3;4;5;16;17;18;19;20;21;22;23;24;25
3;03/01/2023;1;2;3;6;7;8;9;10;11;16;17;18;19;20;25
"""

@pytest.fixture
def analisador_mock(tmp_path: Path) -> AnalisadorLotofacil:
    """
    Fixture do Pytest que cria um ambiente de teste isolado.
    
    1. `tmp_path`: Uma fixture nativa do pytest que cria um diretório temporário.
    2. Cria um arquivo CSV falso dentro desse diretório.
    3. Inicializa a classe AnalisadorLotofacil com o caminho para este arquivo falso.
    4. Retorna a instância do analisador para ser usada nos testes.
    """
    csv_path = tmp_path / "mock_lotofacil.csv"
    csv_path.write_text(MOCK_CSV_DATA, encoding='latin-1')
    
    # Retorna uma instância da classe pronta para o teste
    return AnalisadorLotofacil(str(csv_path))


def test_extracao_historico(analisador_mock: AnalisadorLotofacil):
    """Testa se o histórico foi extraído corretamente do CSV."""
    # Esperamos 3 jogos no nosso histórico mock
    assert len(analisador_mock.historico_numeros) == 3
    
    # Verifica se o primeiro jogo foi lido e ordenado corretamente
    primeiro_jogo_esperado = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
    assert analisador_mock.historico_numeros[0] == primeiro_jogo_esperado

    # Verifica o último jogo
    ultimo_jogo_esperado = sorted([1, 2, 3, 6, 7, 8, 9, 10, 11, 16, 17, 18, 19, 20, 25])
    assert analisador_mock.historico_numeros[2] == ultimo_jogo_esperado

def test_jogo_mais_sorteados(analisador_mock: AnalisadorLotofacil):
    """Testa a lógica para encontrar os números mais sorteados."""
    # Com nosso histórico mock, os números 1, 2, 3 aparecem 3 vezes.
    # Outros aparecem 2 vezes. O resto, 1 vez.
    # A função deve retornar os 15 mais frequentes.
    resultado = analisador_mock.jogo_mais_sorteados()
    
    # Os números 1, 2, 3 DEVEM estar na lista
    assert 1 in resultado
    assert 2 in resultado
    assert 3 in resultado
    
    # Os números 13, 14, 21, 22, 23, 24 (que só aparecem 1 vez) NÃO DEVEM estar na lista dos 15 mais.
    # No nosso caso, há mais de 15 números que aparecem 2 ou 3 vezes, então a seleção exata
    # pode depender da ordem interna do Counter. O importante é testar as inclusões/exclusões certas.
    # Vamos verificar os que aparecem 2x: 4, 5, 6, 7, 8, 9, 10, 11, 16, 17, 18, 19, 20, 25
    # Total: 3 (3x) + 14 (2x) = 17 números. Os 15 mais comuns serão os 3 de 3x e 12 dos de 2x.
    # Os números 13, 14, 15, 21, 22, 23, 24 (1x) não devem estar.
    assert 13 not in resultado
    assert 14 not in resultado
    assert 21 not in resultado
    
    assert len(resultado) == 15

def test_jogo_menos_sorteados(analisador_mock: AnalisadorLotofacil):
    """Testa a lógica para encontrar os números menos sorteados."""
    resultado = analisador_mock.jogo_menos_sorteados()
    
    # Números que aparecem apenas 1 vez: 12, 13, 14, 15, 21, 22, 23, 24
    # Todos eles devem estar na lista dos menos sorteados.
    assert 13 in resultado
    assert 14 in resultado
    assert 15 in resultado
    assert 21 in resultado
    assert 22 in resultado
    assert 23 in resultado
    assert 24 in resultado
    
    # Números que aparecem 3 vezes (1, 2, 3) não devem estar na lista dos menos sorteados.
    assert 1 not in resultado
    assert 2 not in resultado
    assert 3 not in resultado
    
    assert len(resultado) == 15

def test_jogo_pares_impares_equilibrado(analisador_mock: AnalisadorLotofacil):
    """Testa a lógica de equilíbrio par/ímpar."""
    # Histórico de pares: Jogo1 (6), Jogo2 (7), Jogo3 (8)
    # A distribuição mais comum de pares é... nenhuma, todas ocorreram 1 vez.
    # O `most_common(1)` pode retornar 6, 7 ou 8. O teste precisa ser flexível
    # ou o método precisa ter um desempate definido.
    # Assumindo que o `Counter` pega o último que viu em caso de empate, seria 8.
    # Qtd Pares Ideal = 8, Qtd Ímpares Ideal = 7
    
    resultado = analisador_mock.jogo_pares_impares_equilibrado()
    
    qtd_pares = sum(1 for n in resultado if n % 2 == 0)
    qtd_impares = sum(1 for n in resultado if n % 2 != 0)
    
    # O resultado deve ter 15 números
    assert len(resultado) == 15
    # A proporção deve ser a mais comum encontrada (ou uma delas, em caso de empate)
    assert (qtd_pares == 8 and qtd_impares == 7) or \
           (qtd_pares == 7 and qtd_impares == 8) or \
           (qtd_pares == 6 and qtd_impares == 9)