import sys
import os

# Adiciona o diretório raiz do projeto (que contém 'lotofacil_analyzer.py')
# ao caminho de busca do Python. Isso permite que os testes importem o módulo.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
