import copy
import math
import numpy as np

"""
Implementa um algoritmo flexível de empacotamento de peças em uma chapa, permitindo diferentes estratégias de posicionamento.

- Permite configurar a ordem de varredura da chapa:
    - Da esquerda para a direita ou da direita para a esquerda.
    - De cima para baixo ou de baixo para cima.
- Suporta peças retangulares, circulares e diamantes, aplicando rotações configuráveis (0 a 90 graus em incrementos de 10 graus).
- Utiliza uma matriz de ocupação (grid) para verificar colisões e garantir que as peças não se sobreponham.
- Adiciona uma margem opcional entre os recortes para evitar cortes imprecisos ou colisões mecânicas.
- Mantém a ordem original dos recortes na entrada.

Essa abordagem é ideal para otimizar o corte de materiais em processos industriais, como fabricação de móveis, corte de chapas metálicas, vidro, madeira e tecidos.
"""
class FlexiblePacking:
    def __init__(self, sheet_width, sheet_height, recortes_disponiveis, varrer_esquerda_direita=True, varrer_cima_baixo=True,
                 priorizar_horizontal=True, margem=1):
        self.sheet_width = sheet_width
        self.sheet_height = sheet_height
        self.recortes = recortes_disponiveis
        self.layout = []
        self.grid = np.zeros((sheet_width, sheet_height), dtype=int)
        self.margem = margem
        self.varrer_esquerda_direita = varrer_esquerda_direita
        self.varrer_cima_baixo = varrer_cima_baixo	
        self.priorizar_horizontal = priorizar_horizontal

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
        Agora adiciona uma margem de 1 pixel entre os recortes.
        """

        if peca["tipo"] == "circular":
            raio = peca["r"]
            centro_x = x + raio
            centro_y = y + raio

            # Verifica se o círculo está dentro dos limites
            if (
                centro_x - raio - self.margem < 0 or 
                centro_x + raio + self.margem > self.sheet_width or 
                centro_y - raio - self.margem < 0 or 
                centro_y + raio + self.margem > self.sheet_height
            ):
                return False

            # Verifica sobreposição com outras peças no grid
            range_i = list(range(-raio - self.margem, raio + self.margem + 1))
            range_j = list(range(-raio - self.margem, raio + self.margem + 1))

            if not self.varrer_esquerda_direita:
                range_i.reverse()
            if not self.varrer_cima_baixo:
                range_j.reverse()

            for i in range_i:
                for j in range_j:
                    if i ** 2 + j ** 2 <= (raio + self.margem) ** 2:
                        cx, cy = int(round(centro_x + i)), int(round(centro_y + j))
                        if 0 <= cx < self.sheet_width and 0 <= cy < self.sheet_height:
                            if self.grid[cx, cy] == 1:
                                return False

            #  Adiciona verificação específica para círculos já posicionados
            for outra_peca in self.layout:
                if outra_peca["tipo"] == "circular":
                    outro_raio = outra_peca["r"]
                    outro_centro_x = outra_peca["x"] + outro_raio
                    outro_centro_y = outra_peca["y"] + outro_raio

                    # Calcula a distância entre os centros dos dois círculos
                    distancia_centros = math.sqrt((centro_x - outro_centro_x) ** 2 + (centro_y - outro_centro_y) ** 2)

                    # Se a distância for menor que a soma dos raios, há sobreposição
                    if distancia_centros < (raio + outro_raio + self.margem):
                        return False

        elif peca["tipo"] == "diamante":
            vertices = self.get_rotated_vertices(peca, x, y)

            for vx, vy in vertices:
                if not (self.margem <= vx < self.sheet_width - self.margem and self.margem <= vy < self.sheet_height - self.margem):
                    return False

            min_x = max(int(min(v[0] for v in vertices)) - self.margem, 0)
            max_x = min(int(max(v[0] for v in vertices)) + self.margem, self.sheet_width - 1)
            min_y = max(int(min(v[1] for v in vertices)) - self.margem, 0)
            max_y = min(int(max(v[1] for v in vertices)) + self.margem, self.sheet_height - 1)

            range_x = range(min_x, max_x + 1) if self.varrer_esquerda_direita else range(max_x, min_x - 1, -1)
            range_y = range(min_y, max_y + 1) if self.varrer_cima_baixo else range(max_y, min_y - 1, -1)

            for i in range_x:
                for j in range_y:
                    if self.is_point_inside_diamond(i, j, vertices):
                        if self.grid[i, j] == 1:
                            return False

        else:
            largura, altura = self.get_bounding_box(peca)

            if (
                x - self.margem < 0 or 
                y - self.margem < 0 or 
                x + largura + self.margem > self.sheet_width or 
                y + altura + self.margem > self.sheet_height
            ):
                return False  

            range_x = range(-self.margem, largura + self.margem) if self.varrer_esquerda_direita else range(largura + self.margem - 1, -self.margem - 1, -1)
            range_y = range(-self.margem, altura + self.margem) if self.varrer_cima_baixo else range(altura + self.margem - 1, -self.margem - 1, -1)

            for i in range_x:
                for j in range_y:
                    if 0 <= x + i < self.sheet_width and 0 <= y + j < self.sheet_height:
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

    def marcar_ocupacao(self, peca):
        """
        Marca a área ocupada pela peça na matriz de ocupação, garantindo uma margem de 1 pixel.
        """
        x, y = peca["x"], peca["y"]

        if peca["tipo"] == "circular":
            raio = peca["r"]
            centro_x = x + raio
            centro_y = y + raio

            range_i = range(-raio - self.margem, raio + self.margem + 1)
            range_j = range(-raio - self.margem, raio + self.margem + 1)

            if not self.varrer_esquerda_direita:
                range_i = reversed(range_i)
            if not self.varrer_cima_baixo:
                range_j = reversed(range_j)

            for i in range_i:
                for j in range_j:
                    if i ** 2 + j ** 2 <= (raio + self.margem) ** 2:
                        cx, cy = int(centro_x + i), int(centro_y + j)
                        if 0 <= cx < self.sheet_width and 0 <= cy < self.sheet_height:
                            self.grid[cx, cy] = 1

        elif peca["tipo"] == "diamante":
            vertices = self.get_rotated_vertices(peca, x, y)

            min_x = max(int(min(v[0] for v in vertices)) - self.margem, 0)
            max_x = min(int(max(v[0] for v in vertices)) + self.margem, self.sheet_width - 1)
            min_y = max(int(min(v[1] for v in vertices)) - self.margem, 0)
            max_y = min(int(max(v[1] for v in vertices)) + self.margem, self.sheet_height - 1)

            range_x = range(min_x, max_x + 1) if self.varrer_esquerda_direita else range(max_x, min_x - 1, -1)
            range_y = range(min_y, max_y + 1) if self.varrer_cima_baixo else range(max_y, min_y - 1, -1)

            for i in range_x:
                for j in range_y:
                    if self.is_point_inside_diamond(i, j, vertices):
                        if 0 <= i < self.sheet_width and 0 <= j < self.sheet_height:
                            self.grid[i, j] = 1

        else:  
            largura, altura = self.get_bounding_box(peca)

            range_x = range(-self.margem, largura + self.margem) if self.varrer_esquerda_direita else range(largura + self.margem - 1, -self.margem - 1, -1)
            range_y = range(-self.margem, altura + self.margem) if self.varrer_cima_baixo else range(altura + self.margem - 1, -self.margem - 1, -1)

            for i in range_x:
                for j in range_y:
                    if 0 <= x + i < self.sheet_width and 0 <= y + j < self.sheet_height:
                        self.grid[x + i, y + j] = 1

    
    def empacotar(self):
        """ Organiza as peças dentro da chapa considerando as configurações de varredura e margem. """
        for peca in self.recortes:
            encontrou_posicao = False
            
            # Retângulos só poderão rotacionar em 0 ou 90
            if peca["tipo"] == 'retangular':
                rotacoes = [0, 90]
            else:
                # Mantém a rotação original primeiro, depois testa outras de 0 a 90 (se necessário)
                rotacoes = [0] if peca["tipo"] == "circular" else [peca.get("rotacao", 0)] + [r for r in range(0, 100, 10) if r != peca.get("rotacao", 0)]

            for rotacao in rotacoes:
                peca["rotacao"] = rotacao
                largura, altura = self.get_bounding_box(peca)

                # Define as ordens de varredura da chapa
                range_x = range(0, self.sheet_width - largura + 1) if self.varrer_esquerda_direita else range(self.sheet_width - largura, -1, -1)
                range_y = range(0, self.sheet_height - altura + 1) if self.varrer_cima_baixo else range(self.sheet_height - altura, -1, -1)

                # Alterna entre percorrer horizontalmente ou verticalmente
                if self.priorizar_horizontal:
                    iteracoes = [(x, y) for y in range_y for x in range_x]
                else:
                    iteracoes = [(x, y) for x in range_x for y in range_y]

                # Testa cada posição disponível
                for x, y in iteracoes:
                    if self.cabe_no_espaco(peca, x, y):
                        peca["x"], peca["y"] = x, y
                        self.layout.append(copy.deepcopy(peca))
                        self.marcar_ocupacao(peca)
                        encontrou_posicao = True
                        break

                # Se encontrou um local, não precisa testar outras rotações
                if encontrou_posicao:
                    break

        return self.layout


