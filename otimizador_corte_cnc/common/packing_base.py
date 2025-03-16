import math
import numpy as np

# PackingBase é uma classe base que centraliza métodos comuns para o empacotamento de peças,
# como o cálculo da área, determinação do bounding box, rotação de vértices e geração de máscara
# para peças circulares. Essa classe serve como fundação para classes que implementam algoritmos
# de empacotamento (por exemplo, FlexiblePacking e GeneticAlgorithm), evitando duplicação de código
# e facilitando a manutenção e extensão dos métodos relacionados ao posicionamento das peças.
class PackingBase:
    def get_area(self, peca):
        """ Retorna a área de uma peça """

        if peca["tipo"] == "retangular":
            return peca["largura"] * peca["altura"]
        elif peca["tipo"] == "circular":
            return math.pi * (peca["r"] ** 2)
        elif peca["tipo"] == "diamante":
            return (peca["largura"] * peca["altura"]) / 2
        return 0

    def get_bounding_box(self, peca):
        """ Retorna a largura e altura reais da peça após rotação """

        if peca["tipo"] == "circular":
            return 2 * peca["r"], 2 * peca["r"]
        angulo = math.radians(peca["rotacao"])
        largura_original = peca.get("largura", 2 * peca.get("r", 0))
        altura_original = peca.get("altura", 2 * peca.get("r", 0))
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
        vertices_originais = [
            (cx, y),
            (x + largura, cy),
            (cx, y + altura),
            (x, cy)
        ]
        return [
            (
                (vx - cx) * math.cos(angulo) - (vy - cy) * math.sin(angulo) + cx,
                (vx - cx) * math.sin(angulo) + (vy - cy) * math.cos(angulo) + cy
            )
            for vx, vy in vertices_originais
        ]
    
    def get_circle_mask(self, raio, margem=0):
        """
        Gera uma máscara booleana para um círculo com raio 'raio' e margem self.margem.
        A máscara terá tamanho = 2*(raio + margem) + 1 e True para os pontos dentro do círculo expandido.
        """
         
        total = raio + margem
        y, x = np.ogrid[-total:total+1, -total:total+1]
        return x**2 + y**2 <= (raio + margem)**2
    
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