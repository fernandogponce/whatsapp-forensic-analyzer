[README.md](https://github.com/user-attachments/files/21926729/README.md)
# 🔍 WhatsApp Forensic Analyzer

> **Ferramenta profissional para análise forense de conversas exportadas do WhatsApp**

Uma solução completa desenvolvida para profissionais de segurança digital, investigadores e analistas forenses que precisam processar e analisar conversas exportadas do WhatsApp de forma eficiente e profissional.

## ✨ Características Principais

- 📱 **Processamento Completo**: Converte arquivos .txt exportados do WhatsApp em HTML interativo
- 🖼️ **Suporte Multimídia**: Visualização automática de imagens, PDFs, vídeos e documentos
- 🌐 **Servidor Web Integrado**: Servidor HTTP local para visualização completa de anexos
- 📊 **Análise Estatística**: Estatísticas detalhadas da conversa (mensagens, participantes, anexos)
- 💾 **Exportação CSV**: Dados estruturados para análise em planilhas
- 🎯 **Detecção Inteligente**: Reconhecimento automático de tipos de mensagem (sistema, ligações, etc.)
- 🔍 **Modo Forense**: Preserva metadados e timeline das conversas
- 📋 **Standalone**: Cria versões portáteis com anexos inclusos

## 🛠️ Tecnologias Utilizadas

- **Python 3.x**
- **HTML5/CSS3** com design responsivo
- **Servidor HTTP** integrado
- **Regex avançado** para parsing de mensagens
- **Unicode normalization** para caracteres especiais

## 📦 Instalação

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/whatsapp-forensic-analyzer.git

# Entre no diretório
cd whatsapp-forensic-analyzer

# Execute o script (Python 3.x necessário)
python gerar_html_whatsapp.py conversa.txt --pasta-midias ./anexos/
```

## 🚀 Uso Básico

### Conversão Simples
```bash
python gerar_html_whatsapp.py conversa_whatsapp.txt
```

### Com Anexos e Servidor Web
```bash
python gerar_html_whatsapp.py conversa.txt --pasta-midias ./anexos/ --servidor
```

### Modo Standalone (Portátil)
```bash
python gerar_html_whatsapp.py conversa.txt --pasta-midias ./anexos/ --standalone
```

### Exportação para CSV
```bash
python gerar_html_whatsapp.py conversa.txt --exportar-csv
```

## 📋 Parâmetros Disponíveis

| Parâmetro | Descrição |
|-----------|-----------|
| `arquivo` | Arquivo .txt da conversa exportada do WhatsApp |
| `--pasta-midias` | Pasta contendo arquivos de mídia e anexos |
| `--servidor` | Inicia servidor web local para visualização |
| `--standalone` | Cria versão portátil copiando anexos |
| `--exportar-csv` | Exporta dados em formato CSV |
| `--porta` | Define porta do servidor (padrão: 8000) |

## 🎯 Casos de Uso

- **Investigações Digitais**: Análise forense de evidências digitais
- **Compliance Corporativo**: Auditoria de comunicações empresariais
- **Documentação Legal**: Preparação de evidências para processos judiciais
- **Backup Pessoal**: Preservação de conversas importantes
- **Análise de Comportamento**: Estudos de padrões de comunicação

## 📸 Funcionalidades de Mídia Suportadas

- 🖼️ **Imagens**: JPG, PNG, WebP, GIF, BMP
- 📄 **Documentos**: PDF, DOC, DOCX, XLS, XLSX, PPT, PPTX
- 🎵 **Áudio**: MP3, WAV, OGG, M4A, AAC
- 🎬 **Vídeo**: MP4, MOV, AVI, MKV, WebM

## 🔒 Recursos de Segurança

- ✅ Preservação de timestamps originais
- ✅ Detecção de mensagens apagadas
- ✅ Mapeamento automático de participantes
- ✅ Tratamento de caracteres Unicode especiais
- ✅ Validação de integridade de arquivos

## 📊 Estatísticas Geradas

- Total de mensagens processadas
- Contagem de anexos por tipo
- Distribuição de mensagens por participante
- Timeline da conversa
- Tipos de mensagem (texto, sistema, ligações)

## 🌟 Desenvolvido Por

**Sistema desenvolvido por:**
- **Gustavo Godoy Alevado** - [gustavoalevado@pjc.mt.gov.br](mailto:gustavoalevado@pjc.mt.gov.br)
- **Fernando Gonçalves Ponce Corrêa da Costa** - [fernandocosta@pjc.mt.gov.br](mailto:fernandocosta@pjc.mt.gov.br)

*© 2025 - Poder Judiciário do Estado de Mato Grosso*

## 📄 Licença

Este projeto está licenciado sob a [MIT License](LICENSE) - veja o arquivo LICENSE para detalhes.

## 🤝 Contribuições

Contribuições são bem-vindas! Por favor:

1. Faça um Fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## ⚠️ Disclaimer

Esta ferramenta é destinada para uso em investigações legais e análises forenses legítimas. Os usuários são responsáveis por garantir que o uso esteja em conformidade com as leis locais de privacidade e proteção de dados.

---

<div align="center">

**⭐ Se este projeto foi útil, considere dar uma estrela no repositório!**

[Reportar Bug](../../issues) • [Solicitar Feature](../../issues) • [Documentação](../../wiki)

</div>
