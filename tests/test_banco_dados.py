# Testes automatizados do Banco de Dados (DB) do Sistema Aurora Siger
# O teste verifica a estrutura SQLite e suas regras de integridade

import sqlite3
import unittest

from banco_dados import abrir_conexao, inicializar_banco

# Testes da conexão e estrutura do banco SQLite
class TestBancoDados(unittest.TestCase):
    # Prepara um banco temporário para cada teste
    def setUp(self):
        self.conexao = abrir_conexao(":memory:")
        self.addCleanup(self.conexao.close)

        inicializar_banco(self.conexao)

    # Verifica a existência das cinco tabelas
    def test_criacao_das_tabelas(self):
        registros = self.conexao.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            """
        ).fetchall()

        tabelas = {registro["name"] for registro in registros}

        esperadas = {
            "modulos",
            "sensores",
            "leituras",
            "alertas",
            "solicitacoes"
        }

        self.assertEqual(tabelas, esperadas)

    # Verifica se as foreign keys estão habilitadas
    def test_chaves_estrangeiras_ativas(self):
        resultado = self.conexao.execute(
            "PRAGMA foreign_keys"
        ).fetchone()[0]

        self.assertEqual(resultado, 1)

    # O campo critico aceita somente 0 ou 1
    def test_rejeitar_criticidade_invalida(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.conexao.execute(
                """
                INSERT INTO modulos
                    (codigo, nome, tipo, critico)
                VALUES (?, ?, ?, ?)
                """,
                ("MOD_TESTE", "Módulo Teste", "energia", 2)
            )
    
    # Dois módulos não podem possuir o mesmo código
    def test_rejeitar_codigo_duplicado(self):
        dados = ("MOD-001", "Habitação", "habitacao")

        self.conexao.execute(
            """
            INSERT INTO modulos (codigo, nome, tipo)
            VALUES (?, ?, ?)
            """,
            dados
        )

        with self.assertRaises(sqlite3.IntegrityError):
            self.conexao.execute(
                """
                INSERT INTO modulos (codigo, nome, tipo)
                VALUES (?, ?, ?)
                """,
                dados
            )

    # Um sensor não pode apontar para um módulo inexistente
    def test_rejeitar_sensor_sem_modulo(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.conexao.execute(
                """
                INSERT INTO sensores
                    (codigo, modulo_id, tipo, unidade)
                VALUES (?, ?, ?, ?)
                """,
                ("SEN-TESTE", 999, "consumo_kw", "kW")
            )
    
    # Inicializar novamente não deve apagar dados
    def test_inicializacao_repetida(self):
        self.conexao.execute(
            """
            INSERT INTO modulos (codigo, nome, tipo)
            VALUES (?, ?, ?)
            """,
            ("MOD-TESTE", "Módulo Teste", "energia")
        )

        inicializar_banco(self.conexao)

        resultado = self.conexao.execute(
            "SELECT COUNT(*) FROM modulos"
        ).fetchone()[0]

        self.assertEqual(resultado, 1)

if __name__ == "__name__":
    unittest.main()