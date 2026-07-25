from bs4 import BeautifulSoup
import logfire

def parse_html(file_path: str) -> str:
    """parses HTML content using BeautifulSoup and returns the text content.
       Clean scripts, styles and extracts redable text for RAG ingestion.
    """
    with logfire.span("HTML Parsing", filename=file_path):
        try:
            with open(file_path, 'r', encoding='utf-8', errors="ignore") as file:
                content = file.read()

            soup = BeautifulSoup(content, 'html.parser')
            
            #1. Remove Junks (script and style elements)
            for script in soup(['script', 'style', 'noscript', 'meta']):
                script.decompose()
            
            #2. Get text and clean it up
            text = soup.get_text(separator='\n')

            # 3. Clean Whitespace (Collapse multiple newlines)
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            cleaned_text = '\n'.join(chunk for chunk in chunks if chunk)
            
            return cleaned_text
        except Exception as e:
            logfire.error(f"HTML parser failed: {e}")
            return e
