from common.layout_display import LayoutDisplayMixin
import random
import math

class AntColony(LayoutDisplayMixin):
    
    def __init__(self, num_ants, num_iterations, sheet_width, sheet_height, recortes_disponiveis):
        """
        Initializes the Ant Colony optimizer.
        :param num_ants: Number of ants.
        :param num_iterations: Number of iterations to run.
        :param sheet_width: Width of the cutting sheet.
        :param sheet_height: Height of the cutting sheet.
        :param recortes_disponiveis: List of available parts (JSON structure).
        """
        self.num_ants = num_ants
        self.num_iterations = num_iterations
        self.sheet_width = sheet_width
        self.sheet_height = sheet_height
        self.initial_layout = recortes_disponiveis
        self.optimized_layout = None
        self.solutions = None
        self.min_width = 29
        self.min_height = 4

        # Chamar inicialização da matriz de feromônios diretamente
        self.initialize_pheromones()
        
        print("Ant Colony Optimization Initialized.")

    def initialize_pheromones(self):
        # Initialize the pheromone matrix.
        # Definição dos passos com base na largura e altura mínima dos recortes disponíveis 
        self.min_width = 29
        self.min_height = 4

        # Definição do número de linhas e colunas da matriz de feromônios de acordo os passos
        num_cols = self.sheet_width // self.min_width
        num_rows = self.sheet_height // self.min_height

        # Criação matriz de feromônios inicializada com 1.0
        self.pheromone_matrix = [[1.0 for _ in range(num_cols)] for _ in range(num_rows)]

    def construct_solution(self, ant):
        # Construct a solution for the given ant using pheromone and heuristic information.
        ant["path"] = []

        # Copia matriz de feromônio
        pheromone_matrix = self.pheromone_matrix

        # Cria uma matriz de ocupação para evitar sobreposição
        occupancy_matrix = [[0 for _ in range(len(pheromone_matrix[0]))] for _ in range(len(pheromone_matrix))]

        # Lista para armazenar a posição de cada recorte (soluçaõ)
        solution = []

        # Percorre os recortes e os posiciona na chapa
        for recorte in self.initial_layout:
            if recorte["tipo"] == "circular":
                raio = recorte["r"] 
                largura = altura = raio * 2
            else:
                largura = recorte["largura"]
                altura = recorte["altura"]

            # Lista de posições válidas
            valid_positions = []

            # Verifica todas as posições possíveis dentro da chapa. 
            for row in range(len(pheromone_matrix) - (altura // self.min_height)):
                for col in range(len(pheromone_matrix[0]) - (largura // self.min_width)):
                    if self.is_valid_position(col, row, largura, altura, occupancy_matrix):
                        valid_positions.append((col, row))

            # Se não houver posições válidas, pula esse recorte
            if not valid_positions:
                continue

            # Escolha baseada nos feromônios (quanto maior o feromônio, maior a chance)
            probabilities = [pheromone_matrix[y][x] for x, y in valid_positions]
            total_pheromone = sum(probabilities)
            probabilities = [p / total_pheromone for p in probabilities]

            # Escolher a posição baseada na distribuição de probabilidade
            chosen_index = random.choices(range(len(valid_positions)), weights=probabilities, k=1)[0]
            chosen_x, chosen_y = valid_positions[chosen_index]

            # Converter coordenadas da matriz para coordenadas reais na chapa
            real_x = chosen_x * self.min_width
            real_y = chosen_y * self.min_height

            # Adicionar à solução
            if recorte["tipo"] == "circular":
                solution.append({
                    "tipo": "circular",
                    "r": raio, 
                    "x": real_x,
                    "y": real_y
                })
            else:
                solution.append({
                    "tipo": recorte["tipo"],
                    "largura": largura,
                    "altura": altura,
                    "x": real_x,
                    "y": real_y
                })

            ant["path"].append((real_x, real_y))

            # Atualizar a matriz de ocupação para evitar sobreposição
            self.update_occupancy_matrix(chosen_x, chosen_y, largura, altura, occupancy_matrix)

        return solution
    
    def update_occupancy_matrix(self, x, y, largura, altura, occupancy_matrix):
        # Atualiza a matriz de ocupação marcando a posição do recorte.
        # :param x: Posição x do recorte na matriz de feromônios.
        # :param y: Posição y do recorte na matriz de feromônios.
        # :param largura: Largura do recorte em pixels.
        # :param altura: Altura do recorte em pixels.
        # :param occupancy_matrix: Matriz de ocupação a ser atualizada.

        # Converter dimensões do recorte para unidades da matriz de ocupação
        recorte_width_cells = largura // self.min_width  
        recorte_height_cells = altura // self.min_height

        # Percorrer a área do recorte e marcar como ocupada na matriz
        for i in range(y, y + recorte_height_cells):
            for j in range(x, x + recorte_width_cells):
                if 0 <= i < len(occupancy_matrix) and 0 <= j < len(occupancy_matrix[0]):
                    occupancy_matrix[i][j] = 1 

    def is_valid_position(self, x, y, largura, altura, occupancy_matrix):
        # Método que verifica se uma posição (x, y) é válida para um recorte.
        # Retorna True se:
        # - O recorte estiver dentro da chapa.
        # - O recorte não sobrepor outro recorte.

        # Dimensões da matriz de ocupação (quantidade de células)
        num_rows = len(occupancy_matrix)
        num_cols = len(occupancy_matrix[0])

        # Converte as dimensões do recorte para células na matriz de ocupação
        recorte_width_cells = largura // self.min_width
        recorte_height_cells = altura // self.min_height

        # Verifica se a peça cabe dentro da chapa (limites da matriz)
        if x + recorte_width_cells > num_cols or y + recorte_height_cells > num_rows:
            return False

        # Verifica se a posição está livre (sem sobreposição)
        for i in range(y, y + recorte_height_cells):
            for j in range(x, x + recorte_width_cells):
                if occupancy_matrix[i][j] == 1:
                    return False

        return True

    def update_pheromones(self, solutions, Q=100):
        # Update the pheromone matrix based on the solutions found by the ants.
        # :param solutions: Lista de soluções geradas pelas formigas.
        # :param Q: Fator de reforço, controla a influência das boas soluções (padrão: 100).
        if not solutions:
            return

        for solution in solutions:
            # Define um critério de qualidade da solução
            cost = self.evaluate_solution(solution) 
            pheromone_deposit = Q / (cost + 1e-6)

            # Percorrer cada recorte da solução e reforçar o feromônio na matriz
            for recorte in solution:
                x = int(recorte["x"] / self.min_width) 
                y = int(recorte["y"] / self.min_height)

                if 0 <= y < len(self.pheromone_matrix) and 0 <= x < len(self.pheromone_matrix[0]):
                    self.pheromone_matrix[y][x] += pheromone_deposit
    
    def evaluate_solution(self, solution):
        # Método que avalia a qualidade de uma solução com base no desperdício de material.
        # Quanto menor o desperdício, melhor a solução.
 
        total_area = self.sheet_width * self.sheet_height
        used_area = 0 

        for recorte in solution:
            if recorte["tipo"] == "circular":
                used_area += math.pi * (recorte["r"] ** 2)  # Usa área do círculo
            else:
                used_area += recorte["largura"] * recorte["altura"]  

        waste = total_area - used_area

        return waste

    def evaporate_pheromones(self, evaporation_rate=0.1):
        # Apply pheromone evaporation.
        # :param evaporation_rate: Taxa de evaporação (ρ), entre 0 e 1. Quanto mais próximo de 1, mais rápida será a taxa de evaporação.

        for i in range(len(self.pheromone_matrix)):
            for j in range(len(self.pheromone_matrix[0])):
                self.pheromone_matrix[i][j] *= (1 - evaporation_rate)

    def get_best_solution(self):
        # Return the best solution found.

        # Verifica a existência de soluções
        if not hasattr(self, 'solutions') or not self.solutions:
            return None  
        
        # Inicializa a melhor solução com um valor muito alto de desperdício
        best_solution = None
        best_waste = float('inf')
        
        # Percorre todas as soluções encontradas pelas formigas
        for solution in self.solutions:
            waste = self.evaluate_solution(solution)

            # Se for a melhor até agora, atualiza
            if waste < best_waste:
                best_solution = solution
                best_waste = waste

        return best_solution 

    def run(self):
        # Main loop of the ant colony algorithm.
        # For each iteration:
        #   1. Each ant constructs a solution.
        #   2. Update pheromones.
        #   3. Optionally, record the best solution.
        # This method should return the optimized layout (JSON structure).
        
        # Lista para armazenar todas as soluções ao longo das iterações
        self.solutions = []

        for iteration in range(self.num_iterations):
            iteration_solutions = []  # Lista de soluções de cada iteração

            # Cada formiga gera uma solução
            for _ in range(self.num_ants):
                ant = {"id": _, "path": []}
                solution = self.construct_solution(ant)
                iteration_solutions.append(solution)

            # Atualizar feromônios com base nas soluções da iteração
            self.update_pheromones(iteration_solutions)

            # Evaporação dos feromônios para incentivar exploração
            self.evaporate_pheromones()

            # Armazena as soluções desta iteração
            self.solutions.extend(iteration_solutions)

            print(f"Iteração {iteration + 1}/{self.num_iterations} concluída.")

         # Após todas as iterações, escolhemos a melhor solução encontrada
        self.optimized_layout = self.get_best_solution()

        return self.optimized_layout


    def optimize_and_display(self):
        """
        Displays the initial layout, runs the optimization, and then displays the optimized layout.
        """
        # Display initial layout
        self.display_layout(self.initial_layout, title="Initial Layout - Ant Colony")

        # Run the optimization (this should update self.optimized_layout)
        self.optimized_layout = self.run()

        # Display optimized layout
        self.display_layout(self.optimized_layout, title="Optimized Layout - Ant Colony")
        return self.optimized_layout
    
