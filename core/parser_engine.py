# core/parser_engine.py
import requests
from bs4 import BeautifulSoup
import json
import time
import random
from typing import Optional, List, Union, Dict

class ParserEngine:
    """Мощный движок для загрузки и парсинга любых страниц"""
    
    def __init__(self, use_selenium=False, headless=True):
        """
        use_selenium: использовать ли Selenium для JavaScript
        headless: показывать ли окно браузера
        """
        self.use_selenium = use_selenium
        self.headless = headless
        self.driver = None
        self.session = requests.Session()
        
        # Маскируемся под реального пользователя
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Connection': 'keep-alive',
        })
    
    def load_from_url(self, url: str, retries=3, delay=1) -> Optional[BeautifulSoup]:
        """
        Загрузить страницу по URL с защитой от блокировок
        retries: количество попыток при ошибке
        delay: задержка между попытками
        """
        if self.use_selenium:
            return self._load_with_selenium(url)
        
        for attempt in range(retries):
            try:
                # Добавляем случайную задержку между запросами
                time.sleep(random.uniform(delay, delay + 1))
                
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                
                # Определяем кодировку
                content = response.content
                
                # Пробуем найти кодировку в HTML
                import re
                charset_match = re.search(b'charset=([^"\'>\\s]+)', content[:5000])
                if charset_match:
                    encoding = charset_match.group(1).decode('ascii', 'ignore')
                    try:
                        text = content.decode(encoding)
                        print(f"✅ Страница загружена (попытка {attempt + 1})")
                        return BeautifulSoup(text, "html.parser")
                    except:
                        pass
                
                # Пробуем основные кодировки
                encodings_to_try = ['utf-8', 'windows-1251', 'koi8-r', 'cp866']
                for enc in encodings_to_try:
                    try:
                        text = content.decode(enc)
                        print(f"✅ Страница загружена (попытка {attempt + 1}) в кодировке {enc}")
                        return BeautifulSoup(text, "html.parser")
                    except UnicodeDecodeError:
                        continue
                
                # Если ничего не помогло, пробуем с ошибками
                text = content.decode('utf-8', errors='ignore')
                print(f"✅ Страница загружена (попытка {attempt + 1}) с игнорированием ошибок")
                return BeautifulSoup(text, "html.parser")
                
            except requests.exceptions.RequestException as e:
                print(f"⚠️ Ошибка загрузки (попытка {attempt + 1}/{retries}): {e}")
                if attempt < retries - 1:
                    time.sleep(delay * 2)
                else:
                    print(f"❌ Не удалось загрузить {url} после {retries} попыток")
                    return None
    
    def _load_with_selenium(self, url: str, wait_for=None) -> Optional[BeautifulSoup]:
        """Загрузка страницы с JavaScript через Selenium"""
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.chrome.service import Service
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from webdriver_manager.chrome import ChromeDriverManager
            
            options = Options()
            if self.headless:
                options.add_argument('--headless')
            
            # Маскируем Selenium
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            # Добавляем реальный user-agent
            options.add_argument(f'user-agent={self.session.headers["User-Agent"]}')
            
            # Отключаем автоматизацию
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--no-sandbox')
            
            print("🔄 Запускаем браузер...")
            
            # Запускаем браузер
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            
            # Маскируем WebDriver
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # Загружаем страницу
            print(f"📱 Загружаем: {url}")
            self.driver.get(url)
            
            # Ждём загрузки JavaScript
            if wait_for:
                try:
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, wait_for))
                    )
                    print(f"✅ Элемент '{wait_for}' загружен")
                except Exception as e:
                    print(f"⚠️ Таймаут ожидания элемента: {e}")
            else:
                time.sleep(3)
            
            # Прокручиваем страницу вниз
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
            
            # Получаем HTML
            html = self.driver.page_source
            self.driver.quit()
            
            print("✅ Страница с JavaScript загружена")
            return BeautifulSoup(html, "html.parser")
            
        except Exception as e:
            print(f"❌ Ошибка Selenium: {e}")
            if self.driver:
                self.driver.quit()
            return None
    
    def load_from_html(self, html_content: str) -> BeautifulSoup:
        """Загрузить из HTML строки"""
        return BeautifulSoup(html_content, "html.parser")
    
    def extract_css(self, soup: BeautifulSoup, selector: str, attribute: str = None) -> List[str]:
        """
        Извлечь данные по CSS селектору
        attribute: если указан, берём атрибут (например 'href' для ссылок)
        """
        if soup is None:
            return []
        
        elements = soup.select(selector)
        result = []
        
        for el in elements:
            if attribute:
                # Берём значение атрибута
                value = el.get(attribute)
                if value:
                    result.append(str(value).strip())
            else:
                # Берём текст
                result.append(el.get_text(strip=True))
        
        return result
    
    def extract_xpath(self, soup: BeautifulSoup, xpath: str, attribute: str = None) -> List[str]:
        """
        Извлечь данные по XPath
        Требуется установка: pip3 install lxml
        """
        try:
            from lxml import html
            
            # Преобразуем BeautifulSoup в lxml дерево
            dom = html.fromstring(str(soup))
            
            # Извлекаем по XPath
            elements = dom.xpath(xpath)
            result = []
            
            for el in elements:
                if hasattr(el, 'text') and not attribute:
                    result.append(str(el.text).strip())
                elif isinstance(el, str):
                    result.append(el.strip())
                elif attribute and hasattr(el, 'get'):
                    value = el.get(attribute)
                    if value:
                        result.append(str(value).strip())
            
            return result
            
        except Exception as e:
            print(f"⚠️ Ошибка XPath: {e}")
            return []
    
    def extract_json_next_data(self, soup: BeautifulSoup) -> Optional[Dict]:
        """Извлечь JSON из __NEXT_DATA__ (React сайты)"""
        if soup is None:
            return None
        
        script = soup.find("script", id="__NEXT_DATA__")
        if not script:
            return None
        
        try:
            return json.loads(script.string)
        except Exception as e:
            print(f"⚠️ Ошибка парсинга __NEXT_DATA__: {e}")
            return None
    
    def extract_json_ld(self, soup: BeautifulSoup) -> List[Dict]:
        """
        Извлечь структурированные данные JSON-LD
        (используется многими сайтами для SEO)
        """
        if soup is None:
            return []
        
        scripts = soup.find_all("script", type="application/ld+json")
        result = []
        
        for script in scripts:
            try:
                data = json.loads(script.string)
                result.append(data)
            except:
                pass
        
        return result
    
    def extract_json_path(self, json_data: Union[Dict, List], path: str):
        """
        Извлечь данные из JSON по пути вида:
        props.pageProps.initialState.entities.recipes.0.title
        Поддерживает массивы и фильтры
        """
        if json_data is None:
            return None
        
        try:
            parts = path.split(".")
            current = json_data
            
            for part in parts:
                if isinstance(current, list):
                    try:
                        idx = int(part)
                        if 0 <= idx < len(current):
                            current = current[idx]
                        else:
                            return None
                    except ValueError:
                        result = []
                        for item in current:
                            if isinstance(item, dict) and part in item:
                                result.append(item[part])
                        return result
                        
                elif isinstance(current, dict):
                    current = current.get(part)
                    if current is None:
                        return None
                else:
                    return None
            
            return current
            
        except Exception as e:
            print(f"⚠️ Ошибка извлечения JSON: {e}")
            return None
    
    def extract_from_iframe(self, soup: BeautifulSoup, iframe_selector: str, inner_selector: str):
        """
        Извлечь данные из iframe
        iframe_selector: CSS селектор для iframe
        inner_selector: CSS селектор внутри iframe
        """
        iframes = soup.select(iframe_selector)
        result = []
        
        for iframe in iframes:
            src = iframe.get('src')
            if src and src.startswith('http'):
                iframe_soup = self.load_from_url(src)
                if iframe_soup:
                    result.extend(self.extract_css(iframe_soup, inner_selector))
        
        return result
    
    def extract_regex(self, text: str, pattern: str, group=0):
        """Извлечь данные по регулярному выражению"""
        import re
        try:
            matches = re.findall(pattern, text, re.DOTALL)
            if matches:
                if group > 0 and isinstance(matches[0], tuple):
                    return [m[group-1] for m in matches]
                return matches
            return []
        except Exception as e:
            print(f"⚠️ Ошибка regex: {e}")
            return []
    
    def extract_all_methods(self, soup: BeautifulSoup, url: str = None):
        """
        Извлечь всё, что можно, всеми методами
        Полезно для разведки структуры сайта
        """
        result = {
            'title': self.extract_css(soup, 'title'),
            'h1': self.extract_css(soup, 'h1'),
            'meta': {},
            'links': self.extract_css(soup, 'a', 'href')[:10],
            'images': self.extract_css(soup, 'img', 'src')[:5],
            'json_ld': self.extract_json_ld(soup),
            'next_data': self.extract_json_next_data(soup)
        }
        
        # Извлекаем meta-теги
        for meta in soup.find_all('meta'):
            if meta.get('name'):
                result['meta'][meta['name']] = meta.get('content')
            elif meta.get('property'):
                result['meta'][meta['property']] = meta.get('content')
        
        return result