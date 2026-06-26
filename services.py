def extrair_preco_e_beneficio(link: str):
    """Tenta extrair preço e benefício do produto"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        response = requests.get(link, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # =========================
        # EXTRAIR PREÇO
        # =========================
        preco = None
        
        # Tenta encontrar preço com desconto
        padroes_preco = [
            r'R\$\s*[\d.,]+',
            r'R\$\s*[\d.,]+\s*[\d.,]+',
            r'de\s*R\$\s*[\d.,]+\s*por\s*R\$\s*[\d.,]+',
            r'~R\$\s*[\d.,]+~',
        ]
        
        for padrao in padroes_preco:
            match = re.search(padrao, response.text, re.IGNORECASE)
            if match:
                preco = match.group(0)
                break
        
        # =========================
        # EXTRAIR BENEFÍCIO
        # =========================
        beneficio = None
        
        # Tenta encontrar descrição/benefício
        descricao = soup.find("meta", {"name": "description"})
        if descricao and descricao.get("content"):
            beneficio = descricao["content"][:100]  # Primeiros 100 caracteres
        
        if not beneficio:
            # Tenta encontrar no texto
            texto = soup.get_text()
            frases = texto.split(".")
            for frase in frases:
                if "pra" in frase or "para" in frase or "com" in frase:
                    if len(frase) > 20 and len(frase) < 100:
                        beneficio = frase.strip()
                        break
        
        return preco, beneficio
        
    except Exception as e:
        logger.error(f"❌ Erro ao extrair preço/benefício: {e}")
        return None, None

def extrair_imagem(link: str):
    """Extrai imagem, preço e benefício do produto"""
    
    # Primeiro, tenta extrair preço e benefício
    preco, beneficio = extrair_preco_e_beneficio(link)
    
    # Depois, tenta extrair a imagem (como antes)
    imagem = None
    
    # Tenta BS4 Avançado
    imagem = extrair_imagem_com_bs4_avancado(link)
    
    if not imagem:
        # Tenta API de Captura
        imagem = capturar_imagem_com_api(link)
    
    return imagem, preco, beneficio
