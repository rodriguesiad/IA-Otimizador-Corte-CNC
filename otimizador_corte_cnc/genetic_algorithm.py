from common.layout_display import LayoutDisplayMixin
import random
import copy
import math
import numpy as np
from flexible_packing import FlexiblePacking

class GeneticAlgorithm(LayoutDisplayMixin):
    def __init__(self, TAM_POP, recortes_disponiveis, sheet_width, sheet_height, numero_geracoes=100):
        print("Algoritmo Genético para Otimização do Corte de Chapa. Executado por Iad.")
        self.TAM_POP = TAM_POP
        self.initial_layout = recortes_disponiveis  # Available cut parts
        self.sheet_width = sheet_width
        self.sheet_height = sheet_height
        self.POP = []
        self.POP_AUX = []
        self.aptidao = []
        self.numero_geracoes = numero_geracoes
        self.initialize_population()
        self.melhor_aptidoes = []
        self.optimized_layout = None 

    def initialize_population(self):
        """
        Inicializa a população criando indivíduos com:
        - Ordem aleatória dos recortes.
        - Rotação aleatória (0 a 90, de 10 em 10) para peças rotacionáveis.
        - Configurações aleatórias de varredura.
        """

        for _ in range(self.TAM_POP):
            # Copia e embaralha os recortes
            individuo = copy.deepcopy(self.initial_layout)
            random.shuffle(individuo)

            # Aplica rotação aleatória nos recortes que podem girar (Comentada por aumentar demais a variabilidade dos indivíduos)
            #for peca in individuo:
            #    if peca["tipo"] in ["retangular", "diamante"]:  # Apenas essas podem girar
            #        peca["rotacao"] = random.choice(range(0, 100, 10))

            # Gera configurações aleatórias de varredura
            varrer_esquerda_direita = random.choice([True, False])
            varrer_cima_baixo = random.choice([True, False])
            priorizar_horizontal = random.choice([True, False])

            # Gera o indivíduo com essas configurações
            gerar_individuo = FlexiblePacking(
                sheet_width=self.sheet_width, sheet_height=self.sheet_height,
                recortes_disponiveis=individuo,
                varrer_esquerda_direita=varrer_esquerda_direita,
                varrer_cima_baixo=varrer_cima_baixo,
                priorizar_horizontal=priorizar_horizontal,
                margem=5
            )

            # Empacota e adiciona à população
            individuo_empacotado = gerar_individuo.empacotar()
            self.POP.append(individuo_empacotado)
    

    def evaluate(self):
        # Evaluate the fitness of individuals based on available parts.
        pass

    def genetic_operators(self):
        # Execute genetic operators (crossover, mutation, etc.) to evolve the population.
        pass

    def run(self):
        # Main loop of the evolutionary algorithm.

        # Temporary return statement to avoid errors
        self.initialize_population()
        self.optimized_layout = self.initial_layout
        return self.optimized_layout

    def optimize_and_display(self):
        """
        Displays the initial layout, runs the optimization algorithm,
        and displays the optimized layout using the mixin's display_layout method.
        """
        # Display initial layout
        #self.display_layout(self.initial_layout, title="Initial Layout - Genetic Algorithm")
        
        # Run the optimization algorithm (updates self.melhor_individuo)
        self.optimized_layout = self.run()

        for individuos in self.POP:
                self.display_layout(individuos, title="Optimized Layout - Genetic Algorithm - Individuos")
        
        # Display optimized layout
        #self.display_layout(self.optimized_layout, title="Optimized Layout - Genetic Algorithm")
        return self.optimized_layout