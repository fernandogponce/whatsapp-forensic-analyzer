import re
import os
import sys
import csv
import argparse
import html
import unicodedata
import webbrowser
import threading
import time
import shutil
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import unquote

def limpar_nome_arquivo(nome):
    """
    Remove caracteres invisíveis e normaliza o nome do arquivo,
    eliminando espaços estranhos e caracteres de controle Unicode.
    """
    if not nome:
        return ""
    
    nome = unicodedata.normalize('NFKC', nome)
    # Remove caracteres invisíveis comuns do WhatsApp
    for ch in ['\u200e', '\u200f', '\ufeff', '\xa0', '‎']:
        nome = nome.replace(ch, '')
    
    # Remove caracteres de controle Unicode
    nome = ''.join(c for c in nome if not unicodedata.category(c).startswith('C'))
    return nome.strip()

def verificar_arquivo_existe(nome_arquivo, pasta_midias):
    """
    Verifica se o arquivo existe, testando diferentes possibilidades
    """
    if not pasta_midias or not nome_arquivo:
        return None
        
    # Testa o nome exato
    caminho_completo = os.path.join(pasta_midias, nome_arquivo)
    if os.path.isfile(caminho_completo):
        return caminho_completo
    
    # Testa sem prefixos numéricos (00000006- etc)
    nome_sem_prefixo = re.sub(r'^\d+-', '', nome_arquivo)
    if nome_sem_prefixo != nome_arquivo:
        caminho_sem_prefixo = os.path.join(pasta_midias, nome_sem_prefixo)
        if os.path.isfile(caminho_sem_prefixo):
            return caminho_sem_prefixo
    
    # Busca por padrão similar na pasta (case-insensitive)
    try:
        arquivos_pasta = os.listdir(pasta_midias)
        nome_base = nome_sem_prefixo.lower()
        
        for arquivo in arquivos_pasta:
            if nome_base in arquivo.lower() or arquivo.lower() in nome_base:
                return os.path.join(pasta_midias, arquivo)
    except Exception:
        pass
    
    return None

class CustomHTTPRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, pasta_anexos=None, **kwargs):
        self.pasta_anexos = pasta_anexos
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        # Remove parâmetros da URL
        path = self.path.split('?')[0]
        
        # Se solicitar um anexo, redireciona para a pasta correta
        if path.startswith('/anexos/'):
            nome_arquivo = unquote(path[8:])  # Remove '/anexos/'
            if self.pasta_anexos:
                arquivo_real = os.path.join(self.pasta_anexos, nome_arquivo)
                if os.path.isfile(arquivo_real):
                    # Serve o arquivo diretamente
                    with open(arquivo_real, 'rb') as f:
                        self.send_response(200)
                        
                        # Define Content-Type baseado na extensão
                        if nome_arquivo.lower().endswith('.pdf'):
                            self.send_header('Content-Type', 'application/pdf')
                        elif nome_arquivo.lower().endswith(('.jpg', '.jpeg')):
                            self.send_header('Content-Type', 'image/jpeg')
                        elif nome_arquivo.lower().endswith('.png'):
                            self.send_header('Content-Type', 'image/png')
                        else:
                            self.send_header('Content-Type', 'application/octet-stream')
                        
                        self.send_header('Content-Disposition', f'inline; filename="{nome_arquivo}"')
                        self.end_headers()
                        
                        shutil.copyfileobj(f, self.wfile)
                    return
        
        # Para outros arquivos, usa o comportamento padrão
        super().do_GET()

def criar_servidor_temporario(pasta_anexos, porta=8000):
    """
    Cria um servidor HTTP temporário para servir os arquivos
    """
    def handler(*args, **kwargs):
        return CustomHTTPRequestHandler(*args, pasta_anexos=pasta_anexos, **kwargs)
    
    httpd = HTTPServer(('localhost', porta), handler)
    return httpd

def iniciar_servidor_background(pasta_anexos, porta=8000):
    """
    Inicia servidor em background
    """
    httpd = criar_servidor_temporario(pasta_anexos, porta)
    
    def servidor_thread():
        print(f"🌐 Servidor local iniciado em http://localhost:{porta}")
        print("⚠️  Mantenha este terminal aberto enquanto visualiza os anexos")
        httpd.serve_forever()
    
    thread = threading.Thread(target=servidor_thread, daemon=True)
    thread.start()
    return httpd

def gerar_html_anexo(anexo, pasta_midias, usar_servidor=False, porta=8000, pasta_html=""):
    """
    Gera HTML específico para cada tipo de anexo
    """
    caminho_arquivo = verificar_arquivo_existe(anexo, pasta_midias)
    
    if not caminho_arquivo:
        return f'<span style="color:red;font-size:90%;background:#ffe6e6;padding:2px 6px;border-radius:3px;">📋 Arquivo "{anexo}" não encontrado</span>'
    
    # Arquivo existe - determina o tipo
    nome_arquivo = os.path.basename(caminho_arquivo)
    extensao = nome_arquivo.lower().split('.')[-1] if '.' in nome_arquivo else ''
    
    # Define o caminho baseado no modo
    if usar_servidor:
        # Usa localhost para servidor local
        caminho_url = f"http://localhost:{porta}/anexos/{nome_arquivo}"
    else:
        # Copia arquivo para pasta local e usa caminho relativo
        if pasta_html:
            pasta_anexos_local = os.path.join(pasta_html, "anexos_conversa")
            os.makedirs(pasta_anexos_local, exist_ok=True)
            
            # Copia arquivo se não existir
            destino_arquivo = os.path.join(pasta_anexos_local, nome_arquivo)
            if not os.path.exists(destino_arquivo):
                shutil.copy2(caminho_arquivo, destino_arquivo)
            
            caminho_url = f"anexos_conversa/{nome_arquivo}"
        else:
            caminho_url = nome_arquivo
    
    if extensao in ['jpg', 'jpeg', 'png', 'webp', 'gif', 'bmp']:
        return f'''
        <div style="margin:8px 0;">
            <strong>🖼️ {nome_arquivo}</strong><br>
            <img src="{caminho_url}" alt="{nome_arquivo}" 
                 style="max-width:400px;max-height:300px;border-radius:8px;margin:5px 0;border:1px solid #ddd;cursor:pointer;"
                 onclick="window.open(this.src, '_blank')" onerror="this.style.display='none'; this.nextElementSibling.style.display='block';">
            <div style="display:none;padding:20px;background:#f0f0f0;text-align:center;border-radius:8px;">
                <p>❌ Erro ao carregar imagem</p>
                <a href="{caminho_url}" target="_blank" style="color:#1976d2;">Clique para abrir</a>
            </div>
        </div>'''
    
    elif extensao == 'pdf':
        if usar_servidor:
            # Com servidor, pode usar iframe
            return f'''
            <div style="border:1px solid #ccc;padding:12px;margin:8px 0;border-radius:8px;background:#f9f9f9;max-width:500px;">
                <strong>📄 {nome_arquivo}</strong><br>
                <iframe src="{caminho_url}" width="100%" height="400px" style="margin-top:8px;border:none;border-radius:4px;"></iframe>
                <br><a href="{caminho_url}" target="_blank" 
                       style="display:inline-block;padding:8px 16px;background:#dc3545;color:white;text-decoration:none;border-radius:4px;font-weight:bold;margin-top:8px;">
                       📄 ABRIR PDF EM NOVA ABA</a>
            </div>'''
        else:
            # Sem servidor, apenas link de download
            return f'''
            <div style="border:1px solid #ccc;padding:12px;margin:8px 0;border-radius:8px;background:#f9f9f9;max-width:500px;">
                <strong>📄 {nome_arquivo}</strong><br>
                <div style="text-align:center;padding:20px;background:#f0f0f0;margin:8px 0;border-radius:4px;">
                    <p style="margin:0 0 10px 0;">📄 Documento PDF</p>
                    <p style="font-size:12px;color:#666;margin:0 0 15px 0;">Arquivo copiado para a pasta local</p>
                    <a href="{caminho_url}" target="_blank" download="{nome_arquivo}"
                       style="display:inline-block;padding:10px 20px;background:#dc3545;color:white;text-decoration:none;border-radius:6px;font-weight:bold;">
                       📄 BAIXAR PDF</a>
                    <br><br>
                    <p style="font-size:11px;color:#888;">Ou navegue até a pasta 'anexos_conversa' para abrir o arquivo</p>
                </div>
            </div>'''
    
    elif extensao in ['mp4', 'mov', 'avi', 'mkv', 'webm']:
        return f'''
        <div style="margin:8px 0;">
            <strong>🎬 {nome_arquivo}</strong><br>
            <video controls style="max-width:400px;border-radius:8px;margin:5px 0;">
                <source src="{caminho_url}" type="video/{extensao}">
                Seu navegador não suporta reprodução de vídeo.
                <p><a href="{caminho_url}" target="_blank" download="{nome_arquivo}">Clique para baixar o vídeo</a></p>
            </video>
        </div>'''
    
    elif extensao in ['mp3', 'wav', 'ogg', 'm4a', 'aac']:
        return f'''
        <div style="margin:8px 0;padding:8px;background:#f0f8ff;border-radius:8px;max-width:350px;">
            <strong>🎵 {nome_arquivo}</strong><br>
            <audio controls style="width:100%;margin-top:5px;">
                <source src="{caminho_url}" type="audio/{extensao}">
                Seu navegador não suporta reprodução de áudio.
                <p><a href="{caminho_url}" target="_blank" download="{nome_arquivo}">Clique para baixar o áudio</a></p>
            </audio>
        </div>'''
    
    elif extensao in ['doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx']:
        return f'''
        <div style="border:1px solid #e0e0e0;padding:12px;margin:8px 0;border-radius:6px;background:#fff3cd;display:inline-block;">
            <strong>📎 {nome_arquivo}</strong><br>
            <p style="font-size:12px;margin:5px 0;color:#856404;">Documento Office</p>
            <a href="{caminho_url}" target="_blank" download="{nome_arquivo}"
               style="display:inline-block;padding:8px 15px;background:#28a745;color:white;text-decoration:none;border-radius:4px;font-weight:bold;">
               📎 BAIXAR DOCUMENTO</a>
        </div>'''
    
    else:
        return f'''
        <div style="border:1px solid #e0e0e0;padding:10px;margin:5px 0;border-radius:4px;background:#f8f9fa;display:inline-block;">
            <strong>📎 {nome_arquivo}</strong><br>
            <a href="{caminho_url}" target="_blank" download="{nome_arquivo}"
               style="display:inline-block;margin-top:5px;padding:6px 12px;background:#007bff;color:white;text-decoration:none;border-radius:3px;">
               💾 BAIXAR ARQUIVO</a>
        </div>'''

def processar_anexos(texto):
    """
    Processa diferentes tipos de anexos e referências de mídia
    CORRIGIDO: Elimina duplicações e melhora captura de nomes de arquivo
    """
    anexos_encontrados = []
    
    # Padrão 1: <anexado: arquivo> - mais confiável (PRIORIDADE)
    anexos_tag = re.findall(r'<anexado:\s*([^>]+)>', texto, re.IGNORECASE)
    anexos_encontrados.extend(anexos_tag)
    
    # Padrão 2: arquivo.ext • descrição ‎ (formato comum do WhatsApp)
    # REGEX CORRIGIDO para capturar nomes completos de arquivo
    anexos_midia = re.findall(r'([^\s‎/\\]+(?:\s+[^\s‎/\\]*)*\.(?:pdf|jpg|jpeg|png|mp4|mp3|doc|docx|xls|xlsx|wav|ogg|m4a|avi|mov|mkv|webm|gif|bmp|aac|ppt|pptx))\s*•', texto, re.IGNORECASE)
    anexos_encontrados.extend(anexos_midia)
    
    # Padrão 3: referências a anexos em mensagens mistas (como no seu exemplo)
    # Procura por linhas que contêm informações de anexo
    linhas_anexo = re.findall(r'‎\[.*?\]\s+.*?:\s*([^‎\s/\\]+\.(?:pdf|jpg|jpeg|png|mp4|mp3|doc|docx|xls|xlsx|wav|ogg|m4a|avi|mov|mkv|webm|gif|bmp|aac|ppt|pptx))', texto, re.IGNORECASE)
    anexos_encontrados.extend(linhas_anexo)
    
    # Padrão 4: ‎<anexado: arquivo> isolado
    anexos_isolados = re.findall(r'‎<anexado:\s*([^>]+)>', texto, re.IGNORECASE)
    anexos_encontrados.extend(anexos_isolados)
    
    # Padrão 5: apenas arquivos de mídia mencionados
    if not anexos_encontrados:
        arquivos_isolados = re.findall(r'([^‎\s/\\]+\.(?:pdf|jpg|jpeg|png|mp4|mp3|doc|docx|xls|xlsx|wav|ogg|m4a|avi|mov|mkv|webm|gif|bmp|aac|ppt|pptx))(?!\s*•)', texto, re.IGNORECASE)
        anexos_encontrados.extend(arquivos_isolados)
    
    # Limpa e valida anexos
    anexos_limpos = []
    for anexo in anexos_encontrados:
        anexo_limpo = limpar_nome_arquivo(anexo.strip())
        if anexo_limpo:
            # Remove prefixos de timestamp ou caracteres especiais
            anexo_limpo = re.sub(r'^‎+', '', anexo_limpo)
            anexos_limpos.append(anexo_limpo)
    
    # *** CORREÇÃO MELHORADA: Remove duplicações baseadas no nome base do arquivo ***
    anexos_unicos = []
    nomes_base_processados = set()
    
    for anexo in anexos_limpos:
        # Remove prefixo numérico (como "00000043-") para comparação
        nome_base = re.sub(r'^\d+-', '', anexo).lower()
        # Remove também possíveis espaços e caracteres especiais
        nome_base = re.sub(r'[^\w\.-]', '', nome_base)
        
        # Se o nome base ainda não foi processado, adiciona o anexo
        if nome_base not in nomes_base_processados:
            anexos_unicos.append(anexo)
            nomes_base_processados.add(nome_base)
        else:
            # Verifica se deve substituir por uma versão melhor
            for i, anexo_existente in enumerate(anexos_unicos):
                nome_base_existente = re.sub(r'^\d+-', '', anexo_existente).lower()
                nome_base_existente = re.sub(r'[^\w\.-]', '', nome_base_existente)
                
                if nome_base_existente == nome_base:
                    # Prioriza versões com prefixo numérico (mais específicas)
                    if re.match(r'^\d+-', anexo) and not re.match(r'^\d+-', anexo_existente):
                        anexos_unicos[i] = anexo
                    # Prioriza nomes mais completos
                    elif len(anexo) > len(anexo_existente):
                        anexos_unicos[i] = anexo
                    break
    
    return anexos_unicos

def mapear_participantes(mensagens):
    """
    Identifica padrões nos nomes dos usuários para mapeamento automático
    """
    usuarios = {}
    for msg in mensagens:
        user = msg.get("user", "")
        if user and user not in usuarios:
            # Detecta números de telefone vs nomes salvos
            if re.match(r'^\+?\d+', user):
                usuarios[user] = {"tipo": "numero", "nome": user}
            else:
                usuarios[user] = {"tipo": "contato", "nome": user}
    return usuarios

def parse_whatsapp_txt(arquivo_txt):
    """
    Lê o arquivo .txt exportado do WhatsApp e retorna mensagens com:
    usuário, texto limpo, timestamp e info_extra (anexos).
    """
    mensagens = []
    
    try:
        with open(arquivo_txt, encoding="utf-8") as f:
            linhas = f.readlines()
    except UnicodeDecodeError:
        # Tenta outras codificações
        for encoding in ['latin1', 'cp1252', 'iso-8859-1']:
            try:
                with open(arquivo_txt, encoding=encoding) as f:
                    linhas = f.readlines()
                break
            except UnicodeDecodeError:
                continue
        else:
            raise Exception("Não foi possível decodificar o arquivo. Verifique a codificação.")

    # Regex para identificar início de mensagem (corrigida)
    expressao_linha = re.compile(r'^[\u200e\u200f\ufeff]*\[(\d{1,2}\/\d{1,2}\/\d{4}),\s+(\d{1,2}:\d{2}:\d{2})\]\s+([^:]+?):\s*(.*)$')
    # Regex alternativa para linhas com caractere invisível
    expressao_linha_alt = re.compile(r'^‎\[(\d{1,2}\/\d{1,2}\/\d{4}),\s+(\d{1,2}:\d{2}:\d{2})\]\s+([^:]+?):\s*(.*)$')

    msg_atual = None
    for numero_linha, linha in enumerate(linhas, 1):
        linha_original = linha
        linha = linha.strip()
        if not linha:
            continue

        # Tenta primeiro a regex normal
        match = expressao_linha.match(linha)
        if not match:
            # Tenta a regex alternativa para linhas com caractere invisível
            match = expressao_linha_alt.match(linha)

        if match:
            # Salva mensagem anterior se existir
            if msg_atual:
                mensagens.append(msg_atual)

            data_str, hora_str, usuario, texto = match.groups()
            
            # Processa anexos
            anexos_encontrados = processar_anexos(texto)
            info_extra = ", ".join(anexos_encontrados) if anexos_encontrados else ""

            # Remove marcadores de anexo do texto
            texto_limpo = re.sub(r'<anexado:[^>]*>', '', texto)
            texto_limpo = re.sub(r'[^‎\s]+\.(?:pdf|jpg|jpeg|png|mp4|mp3|doc|docx|xls|xlsx|wav|ogg|m4a|avi|mov|mkv|webm|gif|bmp|aac|ppt|pptx)\s*•[^‎]*', '', texto_limpo, flags=re.IGNORECASE)
            texto_limpo = texto_limpo.strip()

            # Processa timestamp
            try:
                dt = datetime.strptime(f"{data_str} {hora_str}", "%d/%m/%Y %H:%M:%S")
                timestamp_iso = dt.isoformat(sep=' ')
            except Exception:
                timestamp_iso = f"{data_str} {hora_str}"

            # Detecta tipo de mensagem
            tipo_msg = "mensagem"
            if "‎Ligação" in texto:
                tipo_msg = "ligacao"
            elif "‎Mensagem apagada" in texto:
                tipo_msg = "apagada"
            elif "‎áudio ocultado" in texto:
                tipo_msg = "audio_oculto"
            elif "mudou o nome do grupo" in texto or "saiu" in texto or "foi adicionado" in texto:
                tipo_msg = "sistema"

            msg_atual = {
                "user": usuario.strip(),
                "texto": texto_limpo,
                "timestamp": timestamp_iso,
                "info_extra": info_extra,
                "tipo": tipo_msg,
                "linha": numero_linha
            }
        else:
            # Continua mensagem multilinha
            if msg_atual:
                # Processa anexos também nas linhas adicionais
                anexos_linha = processar_anexos(linha)
                if anexos_linha:
                    anexos_existentes = [a.strip() for a in msg_atual["info_extra"].split(",") if a.strip()]
                    anexos_existentes.extend(anexos_linha)
                    msg_atual["info_extra"] = ", ".join(set(anexos_existentes))
                
                # Remove anexos da linha antes de adicionar ao texto
                linha_limpa = re.sub(r'<anexado:[^>]*>', '', linha)
                linha_limpa = re.sub(r'[^‎\s]+\.(?:pdf|jpg|jpeg|png|mp4|mp3|doc|docx|xls|xlsx|wav|ogg|m4a|avi|mov|mkv|webm|gif|bmp|aac|ppt|pptx)\s*•[^‎]*', '', linha_limpa, flags=re.IGNORECASE)
                linha_limpa = linha_limpa.strip()
                
                if linha_limpa:
                    msg_atual["texto"] += "\n" + linha_limpa

    # Adiciona última mensagem
    if msg_atual:
        mensagens.append(msg_atual)

    return mensagens

class Conversa:
    def __init__(self, mensagens, pasta_midias="", usar_servidor=False, porta=8000, pasta_html=""):
        self.mensagens = mensagens
        if pasta_midias and not pasta_midias.endswith(os.sep):
            pasta_midias += os.sep
        self.pasta_midias = pasta_midias
        self.usar_servidor = usar_servidor
        self.porta = porta
        self.pasta_html = pasta_html

    def gerar_html(self):
        html_content = '''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Conversa WhatsApp - Análise Investigativa</title>
            <style>
                body { 
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    padding: 20px; 
                    margin: 0;
                    min-height: 100vh;
                }
                .container {
                    max-width: 900px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 15px;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.3);
                    overflow: hidden;
                }
                .header {
                    background: #075e54;
                    color: white;
                    padding: 20px;
                    text-align: center;
                }
                .chat-area {
                    padding: 20px;
                    background: #e5ddd5;
                    min-height: 500px;
                }
                .msg { 
                    padding: 12px 18px; 
                    margin-bottom: 15px; 
                    border-radius: 15px; 
                    max-width: 70%; 
                    clear: both; 
                    word-wrap: break-word;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                    position: relative;
                }
                .user1 { 
                    background: #dcf8c6; 
                    float: right; 
                    text-align: left;
                    border-bottom-right-radius: 5px;
                }
                .user2 { 
                    background: white; 
                    float: left; 
                    text-align: left;
                    border-bottom-left-radius: 5px;
                }
                .sistema {
                    background: #fff3cd;
                    border: 1px solid #ffeaa7;
                    margin: 10px auto;
                    text-align: center;
                    max-width: 80%;
                    float: none;
                    font-style: italic;
                    color: #856404;
                }
                .ligacao {
                    background: #d1ecf1;
                    border: 1px solid #bee5eb;
                    color: #0c5460;
                }
                .apagada {
                    background: #f8d7da;
                    border: 1px solid #f5c6cb;
                    color: #721c24;
                    font-style: italic;
                }
                .username {
                    font-weight: bold;
                    color: #075e54;
                    margin-bottom: 5px;
                    font-size: 14px;
                }
                .timestamp { 
                    font-size: 11px; 
                    color: #666; 
                    margin-top: 8px; 
                    display: block;
                    text-align: right;
                }
                .clear { clear: both; height: 0; }
                .anexo {
                    margin-top: 8px;
                }
                .stats {
                    background: #f8f9fa;
                    padding: 15px;
                    border-top: 1px solid #dee2e6;
                    font-size: 14px;
                    color: #6c757d;
                }
                @media(max-width:768px) { 
                    .msg { max-width: 90%; }
                    body { padding: 10px; }
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📱 Análise de Conversa WhatsApp</h1>
                    <p>Processado em: ''' + datetime.now().strftime("%d/%m/%Y às %H:%M:%S") + '''</p>
                </div>
                <div class="chat-area">
        '''

        # Mapeia usuários
        usuarios = sorted(set(msg.get("user", "Desconhecido") for msg in self.mensagens))
        mapa_usuarios = {}
        if len(usuarios) >= 1:
            mapa_usuarios[usuarios[0]] = "user1"
        if len(usuarios) >= 2:
            mapa_usuarios[usuarios[1]] = "user2"

        # Processa mensagens
        for msg in self.mensagens:
            user = msg.get("user", "Desconhecido")
            cor = mapa_usuarios.get(user, "user1")
            texto = html.escape(msg.get("texto", ""))
            tstamp = msg.get("timestamp", "")
            info_extra = msg.get("info_extra", "")
            tipo = msg.get("tipo", "mensagem")

            # Adiciona classes específicas para tipos especiais
            classes = [cor]
            if tipo != "mensagem":
                classes.append(tipo)

            html_content += f'<div class="msg {" ".join(classes)}">'
            html_content += f'<div class="username">{html.escape(user)}</div>'
            
            # Conteúdo da mensagem
            if texto.strip():
                html_content += f'<div>{texto}</div>'
            
            # Anexos
            if info_extra:
                anexos = [anexo.strip() for anexo in info_extra.split(",") if anexo.strip()]
                for anexo in anexos:
                    html_content += f'<div class="anexo">{gerar_html_anexo(anexo, self.pasta_midias, self.usar_servidor, self.porta, self.pasta_html)}</div>'
            
            html_content += f'<div class="timestamp">{tstamp}</div>'
            html_content += '</div>\n'
            html_content += '<div class="clear"></div>\n'

        # Estatísticas
        total_msgs = len(self.mensagens)
        msgs_por_usuario = {}
        anexos_total = 0
        
        for msg in self.mensagens:
            user = msg.get("user", "Desconhecido")
            msgs_por_usuario[user] = msgs_por_usuario.get(user, 0) + 1
            if msg.get("info_extra"):
                anexos_total += len([a for a in msg.get("info_extra", "").split(",") if a.strip()])

        html_content += f'''
                </div>
                <div class="stats">
                    <strong>📊 Estatísticas da Conversa:</strong><br>
                    Total de mensagens: {total_msgs}<br>
                    Total de anexos: {anexos_total}<br>
                    Participantes: {", ".join(usuarios)}<br>
                    Mensagens por usuário: {" | ".join([f"{u}: {c}" for u, c in msgs_por_usuario.items()])}
                </div>
            </div>
        </body>
        </html>
        '''

        return html_content

    def exportar_csv(self, arquivo_saida):
        """
        Exporta mensagens em formato CSV para análise
        """
        with open(arquivo_saida, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Timestamp', 'Usuario', 'Texto', 'Anexos', 'Tipo', 'Linha'])
            for msg in self.mensagens:
                writer.writerow([
                    msg.get('timestamp', ''),
                    msg.get('user', ''),
                    msg.get('texto', ''),
                    msg.get('info_extra', ''),
                    msg.get('tipo', 'mensagem'),
                    msg.get('linha', '')
                ])

def main():
    parser = argparse.ArgumentParser(
        description='Conversor de conversas WhatsApp para HTML com suporte a anexos',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Exemplos de uso:
  python whatsapp_converter.py conversa.txt
  python whatsapp_converter.py conversa.txt --pasta-midias ./anexos/
  python whatsapp_converter.py conversa.txt --pasta-midias ./anexos/ --servidor
        '''
    )
    
    parser.add_argument('arquivo', help='Arquivo .txt da conversa exportada do WhatsApp')
    parser.add_argument('--pasta-midias', help='Pasta contendo os arquivos de mídia e anexos')
    parser.add_argument('--exportar-csv', action='store_true', help='Exportar também em formato CSV')
    parser.add_argument('--servidor', action='store_true', help='Iniciar servidor web local para visualizar anexos')
    parser.add_argument('--standalone', action='store_true', help='Criar versão standalone copiando anexos localmente')
    parser.add_argument('--porta', type=int, default=8000, help='Porta do servidor local (padrão: 8000)')
    parser.add_argument('--encoding', default='utf-8', help='Codificação do arquivo (padrão: utf-8)')
    
    args = parser.parse_args()

    # Verificações
    if not os.path.isfile(args.arquivo):
        print(f"❌ Arquivo não encontrado: {args.arquivo}")
        sys.exit(1)

    if args.pasta_midias and not os.path.isdir(args.pasta_midias):
        print(f"⚠️  Pasta de mídias não encontrada: {args.pasta_midias}")
        print("Continuando sem anexos...")
        args.pasta_midias = ""

    print(f"📖 Lendo arquivo: {args.arquivo}")
    if args.pasta_midias:
        print(f"📁 Pasta de mídias: {args.pasta_midias}")
        arquivos_midias = len([f for f in os.listdir(args.pasta_midias) if os.path.isfile(os.path.join(args.pasta_midias, f))])
        print(f"📎 Encontrados {arquivos_midias} arquivos na pasta de mídias")

    try:
        mensagens = parse_whatsapp_txt(args.arquivo)
        print(f"✅ Processadas {len(mensagens)} mensagens")
        
        # Conta anexos encontrados e mostra detalhes
        anexos_encontrados = 0
        anexos_detalhes = []
        for msg in mensagens:
            if msg.get("info_extra"):
                anexos_na_msg = [a.strip() for a in msg.get("info_extra", "").split(",") if a.strip()]
                anexos_encontrados += len(anexos_na_msg)
                anexos_detalhes.extend(anexos_na_msg)
        
        if anexos_encontrados > 0:
            print(f"📎 Encontrados {anexos_encontrados} anexos nas mensagens:")
            for anexo in set(anexos_detalhes):
                caminho_encontrado = verificar_arquivo_existe(anexo, args.pasta_midias or "")
                status = "✅ ENCONTRADO" if caminho_encontrado else "❌ NÃO ENCONTRADO"
                print(f"   - {anexo} → {status}")
        else:
            print("⚠️  Nenhum anexo foi detectado nas mensagens")

        # Inicia servidor se solicitado
        httpd = None
        pasta_html_base = ""
        
        if args.servidor and args.pasta_midias and anexos_encontrados > 0:
            httpd = iniciar_servidor_background(args.pasta_midias, args.porta)
            time.sleep(1)  # Aguarda servidor iniciar
        elif args.standalone or (not args.servidor and args.pasta_midias):
            # Modo standalone: cria pasta para copiar anexos
            pasta_html_base = os.path.dirname(os.path.abspath(args.arquivo))

        gerador = Conversa(mensagens, args.pasta_midias or "", args.servidor, args.porta, pasta_html_base)
        conteudo_html = gerador.gerar_html()

        # Gera arquivo HTML
        arquivo_saida_html = os.path.splitext(args.arquivo)[0] + "_conversa.html"
        with open(arquivo_saida_html, "w", encoding="utf-8") as f:
            f.write(conteudo_html)
        
        print(f"🌐 Arquivo HTML gerado: {arquivo_saida_html}")
        
        # Informa sobre anexos copiados
        if args.standalone or (not args.servidor and args.pasta_midias and anexos_encontrados > 0):
            pasta_anexos_criada = os.path.join(pasta_html_base, "anexos_conversa")
            if os.path.exists(pasta_anexos_criada):
                arquivos_copiados = len(os.listdir(pasta_anexos_criada))
                print(f"📁 Anexos copiados para: {pasta_anexos_criada}")
                print(f"📎 Total de {arquivos_copiados} arquivos copiados")

        # Exporta CSV se solicitado
        if args.exportar_csv:
            arquivo_saida_csv = os.path.splitext(args.arquivo)[0] + "_conversa.csv"
            gerador.exportar_csv(arquivo_saida_csv)
            print(f"📊 Arquivo CSV gerado: {arquivo_saida_csv}")

        print(f"\n🎉 Processamento concluído!")
        
        if args.servidor and httpd:
            print(f"🌐 Abrindo navegador...")
            webbrowser.open(f'http://localhost:{args.porta}/{os.path.basename(arquivo_saida_html)}')
            print(f"\n📖 INSTRUÇÕES:")
            print(f"   • O navegador abrirá automaticamente")
            print(f"   • Os anexos agora funcionarão corretamente")
            print(f"   • Para PARAR o servidor: pressione Ctrl+C")
            print(f"   • URL: http://localhost:{args.porta}")
            
            try:
                print(f"\n⏳ Servidor rodando... (Ctrl+C para parar)")
                httpd.serve_forever()
            except KeyboardInterrupt:
                print(f"\n🛑 Servidor parado pelo usuário")
                httpd.shutdown()
        else:
            if args.standalone or (args.pasta_midias and anexos_encontrados > 0):
                print(f"\n📖 COMO USAR:")
                print(f"   • Abra o arquivo HTML: {arquivo_saida_html}")
                print(f"   • Imagens carregarão automaticamente")
                print(f"   • PDFs e documentos: clique para baixar")
                print(f"   • Anexos foram copiados para pasta local")
                print(f"\n💡 Para visualização completa de PDFs no navegador:")
                print(f"   python {sys.argv[0]} {args.arquivo} --pasta-midias {args.pasta_midias or 'Anexos'} --servidor")
            else:
                print(f"💡 DICAS:")
                print(f"   • Modo standalone: --standalone")
                print(f"   • Servidor completo: --servidor")
        
    except Exception as e:
        print(f"❌ Erro durante o processamento: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()