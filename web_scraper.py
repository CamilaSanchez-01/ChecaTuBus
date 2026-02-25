"""
Módulo base de web scraping.
Proporciona funcionalidades comunes: sesión HTTP, user-agents, delays, reintentos.
"""

import requests
from bs4 import BeautifulSoup
import random
import time
import logging

logger = logging.getLogger(__name__)


class WebScraper:
    """Clase base para scraping web con manejo de errores y rate limiting."""

    def __init__(self, config):
        """
        Inicializa el scraper con la configuración.
        
        Args:
            config: Diccionario con configuración de scraping
        """
        self.user_agents = config.get("user_agents", [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/131.0.0.0"
        ])
        self.delay_min = config.get("delay_min", 2)
        self.delay_max = config.get("delay_max", 5)
        self.max_reintentos = config.get("max_reintentos", 3)
        self.timeout = config.get("timeout", 30)
        self.session = requests.Session()
        self._rotar_user_agent()

    def _rotar_user_agent(self):
        """Establece un user-agent aleatorio en la sesión."""
        ua = random.choice(self.user_agents)
        self.session.headers.update({
            "User-Agent": ua,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "es-MX,es;q=0.9,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive"
        })

    def _esperar(self):
        """Espera un tiempo aleatorio entre peticiones."""
        delay = random.uniform(self.delay_min, self.delay_max)
        time.sleep(delay)

    def obtener_pagina(self, url):
        """
        Obtiene el contenido HTML de una URL con reintentos.
        
        Args:
            url: URL a consultar
            
        Returns:
            BeautifulSoup object o None si falla
        """
        for intento in range(1, self.max_reintentos + 1):
            try:
                self._rotar_user_agent()
                self._esperar()
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, "lxml")
                logger.info(f"✅ Página obtenida: {url[:80]}...")
                return soup
            except requests.exceptions.HTTPError as e:
                logger.warning(f"⚠ HTTP Error {e} - Intento {intento}/{self.max_reintentos}")
            except requests.exceptions.ConnectionError:
                logger.warning(f"⚠ Error de conexión - Intento {intento}/{self.max_reintentos}")
            except requests.exceptions.Timeout:
                logger.warning(f"⚠ Timeout - Intento {intento}/{self.max_reintentos}")
            except Exception as e:
                logger.warning(f"⚠ Error inesperado: {e} - Intento {intento}/{self.max_reintentos}")

            if intento < self.max_reintentos:
                time.sleep(intento * 3)  # Backoff exponencial

        logger.error(f"❌ No se pudo obtener: {url}")
        return None

    def buscar_noticias_google(self, query, num_resultados=20):
        """
        Busca noticias en Google sobre transporte en Tijuana.
        
        Args:
            query: Término de búsqueda
            num_resultados: Número aproximado de resultados deseados
            
        Returns:
            Lista de diccionarios con título, enlace y snippet
        """
        resultados = []
        url = (
            f"https://www.google.com/search?q={requests.utils.quote(query)}"
            f"&tbm=nws&num={num_resultados}&hl=es"
        )
        soup = self.obtener_pagina(url)
        if not soup:
            return resultados

        # Intentar extraer resultados de noticias de Google
        for item in soup.select("div.SoaBEf, div.dbsr, div.g"):
            try:
                titulo_elem = item.select_one("div.n0jPhd, h3, div.JheGif")
                enlace_elem = item.select_one("a[href]")
                snippet_elem = item.select_one("div.GI74Re, div.st, div.Y3v8qd")

                titulo = titulo_elem.get_text(strip=True) if titulo_elem else "No disponible"
                enlace = enlace_elem.get("href", "") if enlace_elem else ""
                snippet = snippet_elem.get_text(strip=True) if snippet_elem else "No disponible"

                if titulo != "No disponible" and enlace:
                    resultados.append({
                        "titulo": titulo,
                        "enlace": enlace,
                        "snippet": snippet
                    })
            except Exception:
                continue

        logger.info(f"📰 Encontrados {len(resultados)} resultados para: {query[:50]}")
        return resultados

    def scrape_moovit_rutas(self):
        """
        Intenta obtener listado de rutas de Moovit para Tijuana.
        Moovit usa JavaScript dinámico, así que puede no funcionar con requests.
        
        Returns:
            Lista de diccionarios con datos de rutas, o lista vacía
        """
        rutas = []
        urls_moovit = [
            "https://moovitapp.com/index/es-419/transporte_p%C3%BAblico-Tijuana-3960",
            "https://moovitapp.com/index/es/transporte_p%C3%BAblico-Tijuana-3960",
        ]

        for url in urls_moovit:
            soup = self.obtener_pagina(url)
            if not soup:
                continue

            # Buscar elementos de rutas en la página
            selectores = [
                "a.line-title", "div.line-name", "span.route-name",
                "li.line-item", "div.transit-line", "a[href*='line']"
            ]
            for selector in selectores:
                elementos = soup.select(selector)
                if elementos:
                    logger.info(f"🔍 Encontrados {len(elementos)} elementos con '{selector}'")
                    for elem in elementos:
                        nombre = elem.get_text(strip=True)
                        if nombre and len(nombre) > 1:
                            rutas.append({
                                "nombre": nombre,
                                "fuente": url
                            })
                    break

        logger.info(f"🚌 Rutas obtenidas de Moovit: {len(rutas)}")
        return rutas

    def scrape_noticias_transporte(self, num_paginas=5):
        """
        Busca noticias sobre incidencias de transporte en Tijuana.
        
        Returns:
            Lista de diccionarios con datos de incidencias
        """
        queries = [
            "transporte público Tijuana problemas",
            "rutas camiones Tijuana retraso",
            "autobuses Tijuana accidente",
            "SITT Tijuana incidente",
            "transporte Tijuana manifestación bloqueo",
            "camiones Tijuana avería descompuesto",
            "transporte público Tijuana desvío ruta",
            "ATT Tijuana transporte noticias",
            "ALTISA Tijuana transporte noticias",
            "unidades nuevas transporte Tijuana",
        ]

        todas_noticias = []
        for query in queries:
            noticias = self.buscar_noticias_google(query)
            todas_noticias.extend(noticias)
            self._esperar()

        # Eliminar duplicados por título
        vistos = set()
        unicas = []
        for n in todas_noticias:
            if n["titulo"] not in vistos:
                vistos.add(n["titulo"])
                unicas.append(n)

        logger.info(f"📰 Total noticias únicas encontradas: {len(unicas)}")
        return unicas
