from common.layout_display import LayoutDisplayMixin
import copy
import math
import numpy as np

class BottomLeftPacking (LayoutDisplayMixin):
    def __init__(self, sheet_width, sheet_height, recortes_disponiveis):
        self.sheet_width = sheet_width
        self.sheet_height = sheet_height
        self.recortes = sorted(recortes_disponiveis, key=lambda p: self.get_area(p), reverse=True)
        self.layout = []
        self.grid = np.zeros((sheet_width, sheet_height), dtype=int)

    def get_area(self, peca):
        """ Retorna a área da peça """
        if peca["tipo"] == "retangular":
            return peca["largura"] * peca["altura"]
        if peca["tipo"] == "circular":
            return math.pi * (peca["r"] ** 2)
        if peca["tipo"] == "diamante":
            return (peca["largura"] * peca["altura"]) / 2
        return 0

    def get_bounding_box(self, peca):
        """ Retorna a largura e altura reais da peça após rotação """
        if peca["tipo"] == "circular":
            return 2 * peca["r"], 2 * peca["r"]
        
        angulo = math.radians(peca["rotacao"])
        largura_original = peca.get("largura", 2 * peca.get("r", 0))
        altura_original = peca.get("altura", 2 * peca.get("r", 0))

        # Calcula bounding box após rotação usando trigonometria
        largura_rotacionada = abs(largura_original * math.cos(angulo)) + abs(altura_original * math.sin(angulo))
        altura_rotacionada = abs(largura_original * math.sin(angulo)) + abs(altura_original * math.cos(angulo))

        return int(round(largura_rotacionada)), int(round(altura_rotacionada))
    
    def get_rotated_vertices(self, peca, x, y):
        """
        Retorna os vértices reais do diamante após a rotação, preservando seu tamanho original.
        """
        largura = peca["largura"]
        altura = peca["altura"]
        cx, cy = x + largura / 2, y + altura / 2 
        angulo = math.radians(peca["rotacao"])

        # Vértices antes da rotação
        vertices_originais = [
            (cx, y),  # Topo
            (x + largura, cy),  # Direita
            (cx, y + altura),  # Base
            (x, cy)  # Esquerda
        ]

        # Aplica rotação a cada vértice
        vertices_rotacionados = [
            (
                (vx - cx) * math.cos(angulo) - (vy - cy) * math.sin(angulo) + cx,
                (vx - cx) * math.sin(angulo) + (vy - cy) * math.cos(angulo) + cy
            )
            for vx, vy in vertices_originais
        ]

        return vertices_rotacionados

    def cabe_no_espaco(self, peca, x, y):
        """
        Verifica se a peça pode ser colocada sem ultrapassar os limites da chapa e sem sobreposição.
        Agora evita que um diamante rotacionado sobreponha um círculo.
        """

        if peca["tipo"] == "circular":
            raio = peca["r"]
            centro_x = x + raio
            centro_y = y + raio

            # Evita que o círculo ultrapasse os limites da chapa
            if centro_x - raio < 0 or centro_x + raio > self.sheet_width or centro_y - raio < 0 or centro_y + raio > self.sheet_height:
                return False

            # Verifica sobreposição com outras peças
            for i in range(-raio, raio + 1):
                for j in range(-raio, raio + 1):
                    if i ** 2 + j ** 2 <= raio ** 2:  # Dentro do círculo
                        cx, cy = int(centro_x + i), int(centro_y + j)
                        if 0 <= cx < self.sheet_width and 0 <= cy < self.sheet_height:
                            if self.grid[cx, cy] == 1:
                                return False

        elif peca["tipo"] == "diamante":
            vertices = self.get_rotated_vertices(peca, x, y)

            # Verifica se os vértices estão dentro dos limites da chapa
            for vx, vy in vertices:
                if not (0 <= vx < self.sheet_width and 0 <= vy < self.sheet_height):
                    return False

            # **Verifica sobreposição de TODOS os pontos internos e das vértices**
            min_x = max(int(min(v[0] for v in vertices)), 0)
            max_x = min(int(max(v[0] for v in vertices)), self.sheet_width - 1)
            min_y = max(int(min(v[1] for v in vertices)), 0)
            max_y = min(int(max(v[1] for v in vertices)), self.sheet_height - 1)

            for i in range(min_x, max_x + 1):
                for j in range(min_y, max_y + 1):
                    if self.is_point_inside_diamond(i, j, vertices) or (i, j) in vertices: 
                        if self.grid[i, j] == 1:
                            return False
                        
        else:
            largura, altura = self.get_bounding_box(peca)
            if x + largura > self.sheet_width or y + altura > self.sheet_height:
                return False  

            for i in range(largura):
                for j in range(altura):
                    if self.grid[x + i, y + j] == 1:
                        return False

        return True


    def ajustar_posicao_para_dentro(self, peca, x, y):
        """
        Ajusta a posição da peça para garantir que ela não ultrapasse os limites da chapa.
        """
        largura, altura = self.get_bounding_box(peca)

        # Se estiver saindo da chapa, ajusta o x e y
        if x + largura > self.sheet_width:
            x = self.sheet_width - largura
        if y + altura > self.sheet_height:
            y = self.sheet_height - altura

        return x, y

    def marcar_ocupacao(self, peca):
        """
        Marca a área ocupada pela peça na matriz de ocupação, garantindo que os índices estejam dentro dos limites.
        Agora usa os vértices reais do diamante para evitar marcações erradas.
        """
        x, y = peca["x"], peca["y"]

        if peca["tipo"] == "circular":
            raio = peca["r"]
            centro_x = x + raio
            centro_y = y + raio

            for i in range(-raio, raio + 1):
                for j in range(-raio, raio + 1):
                    if i ** 2 + j ** 2 <= raio ** 2:  # Dentro do círculo
                        cx, cy = int(centro_x + i), int(centro_y + j)
                        if 0 <= cx < self.sheet_width and 0 <= cy < self.sheet_height:
                            self.grid[cx, cy] = 1  # Marca a área ocupada

        elif peca["tipo"] == "diamante":
            vertices = self.get_rotated_vertices(peca, x, y)

            # Calcula os limites do diamante na grade
            min_x = max(int(min(v[0] for v in vertices)), 0)
            max_x = min(int(max(v[0] for v in vertices)), self.sheet_width - 1)
            min_y = max(int(min(v[1] for v in vertices)), 0)
            max_y = min(int(max(v[1] for v in vertices)), self.sheet_height - 1)

            # Preenche o interior do diamante na grade
            for i in range(min_x, max_x + 1):
                for j in range(min_y, max_y + 1):
                    # Verifica se o ponto (i, j) está dentro do diamante OU É UM DOS VÉRTICES
                    if self.is_point_inside_diamond(i, j, vertices) or (i, j) in vertices:
                        if 0 <= i < self.sheet_width and 0 <= j < self.sheet_height:
                            self.grid[i, j] = 1  # Marca corretamente

        else:            
            largura, altura = self.get_bounding_box(peca)

            for i in range(largura):
                for j in range(altura):
                    if 0 <= x + i < self.sheet_width and 0 <= y + j < self.sheet_height:
                        self.grid[x + i, y + j] = 1  # Marca a área ocupada

    def is_point_inside_diamond(self, px, py, vertices):
        """
        Verifica se um ponto (px, py) está dentro do diamante definido por seus vértices.
        Utiliza a fórmula do produto vetorial para determinar se está dentro do losango.
        """
        A, B, C, D = vertices  # Vértices do diamante em ordem

        def sign(p1, p2, p3):
            return (p1[0] - p3[0]) * (p2[1] - p3[1]) - (p2[0] - p3[0]) * (p1[1] - p3[1])

        b1 = sign((px, py), A, B) < 0.0
        b2 = sign((px, py), B, C) < 0.0
        b3 = sign((px, py), C, D) < 0.0
        b4 = sign((px, py), D, A) < 0.0

        return b1 == b2 == b3 == b4

    def empacotar(self):
        """
        Executa a heurística Bottom-Left para organizar as peças dentro da chapa.
        - Para peças circulares, não tenta rotação.
        - Para outras peças, tenta rotação de 10° em 10° até 90° se necessário.
        - **Se a peça rotacionada ultrapassar os limites, ajusta a posição.**
        - **Atualiza largura e altura na peça para evitar inconsistências.**
        """
        recortes = self.recortes.copy();

        for peca in recortes:
            encontrou_posicao = False
            rotacoes = [0] if peca["tipo"] == "circular" else range(0, 100, 10)  # Círculos não giram

            # Percorre toda a chapa tentando a rotação permitida
            for rotacao in rotacoes:
                peca["rotacao"] = rotacao
                largura, altura = self.get_bounding_box(peca)

                if rotacao == 80:
                    print("Aqui")

                # **Ajusta a posição para evitar que a peça saia da chapa**
                for y in range(self.sheet_height - altura + 1):  # De baixo para cima
                    for x in range(self.sheet_width - largura + 1):  # Da esquerda para a direita
                        if self.cabe_no_espaco(peca, x, y):
                            x, y = self.ajustar_posicao_para_dentro(peca, x, y)

                            # **ATUALIZA A PEÇA COM AS NOVAS DIMENSÕES APÓS ROTAÇÃO**
                            peca["x"], peca["y"] = x, y
                            peca["largura"], peca["altura"] = largura, altura  # 🔹 Corrigindo valores

                            self.layout.append(copy.deepcopy(peca))
                            self.marcar_ocupacao(peca)  # Atualiza a malha ocupada
                            encontrou_posicao = True
                            break  
                    if encontrou_posicao:
                        break  
                if encontrou_posicao:
                    break  

        return self.layout

    
def main():
    
    recortes_disponiveis = [
        {"tipo": "retangular", "largura": 29, "altura": 29, "x": 1, "y": 1, "rotacao": 0},
        {"tipo": "retangular", "largura": 29, "altura": 29, "x": 31, "y": 1, "rotacao": 0},
        {"tipo": "retangular", "largura": 29, "altura": 29, "x": 1, "y": 31, "rotacao": 0},
        {"tipo": "retangular", "largura": 29, "altura": 29, "x": 1, "y": 69, "rotacao": 0},
        {"tipo": "retangular", "largura": 139, "altura": 29, "x": 60, "y": 70, "rotacao": 0},
        {"tipo": "retangular", "largura": 60, "altura": 8, "x": 66, "y": 52, "rotacao": 0},
        {"tipo": "retangular", "largura": 44, "altura": 4, "x": 117, "y": 39, "rotacao": 0},
        {"tipo": "diamante", "largura": 29, "altura": 48, "x": 32, "y": 31, "rotacao": 0},
        {"tipo": "diamante", "largura": 29, "altura": 48, "x": 62, "y": 2, "rotacao": 0},
        {"tipo": "diamante", "largura": 29, "altura": 48, "x": 94, "y": 2, "rotacao": 0},
        {"tipo": "circular", "r": 16, "x": 124, "y": 2},
        {"tipo": "circular", "r": 16, "x": 158, "y": 2}
    ]

    bl_packing = BottomLeftPacking(sheet_width=200, sheet_height=100, recortes_disponiveis=recortes_disponiveis)

    print("Exibindo layout inicial...")
    bl_packing.display_layout(recortes_disponiveis, title="Layout Inicial")

    novo_layout = bl_packing.empacotar()
    
    print("Novo Layout")
    bl_packing.display_layout(novo_layout, title="Novo Layout")

if __name__ == "__main__":
    main()
