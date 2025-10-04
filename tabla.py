import requests
import time
import random
from bs4 import BeautifulSoup
import json
from urllib.parse import urljoin
from datetime import datetime
import threading
from concurrent.futures import ThreadPoolExecutor
import ssl
import urllib3
import logging

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LigaMXScraper:
    def __init__(self):
        self.session = requests.Session()
        self.setup_session()
        
        # Fuentes alternativas más confiables
        self.sources = {
            'ligamx_oficial': 'https://www.ligamx.net/cancha/stats',
            'espn_mx': 'https://www.espn.com.mx/futbol/posiciones/_/liga/mex.1',
            'foxsports': 'https://www.foxsports.com.mx/futbol/liga-mx/tabla-de-posiciones',
            'medio_tiempo': 'https://www.mediotiempo.com/futbol/liga-mx/tabla-posiciones',
            'transfermarkt': 'https://www.transfermarkt.com/liga-mx-clausura/tabelle/wettbewerb/MEXC',
        }
        
        # User Agents más actualizados y diversos
        self.user_agents = [
            # Chrome on Windows
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            # Firefox on Windows
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
            # Safari on macOS
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
            # Chrome on macOS
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            # Mobile User Agents
            'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (Android 14; Mobile; rv:121.0) Gecko/121.0 Firefox/121.0',
        ]
        
        self.teams_data = {}
        self.last_update = None
        
    def setup_session(self):
        """Configura la sesión con headers realistas y configuraciones avanzadas"""
        # Configurar SSL context más permisivo
        self.session.verify = False
        
        # Configurar timeout y reintento
        adapter = requests.adapters.HTTPAdapter(
            max_retries=3,
            pool_connections=10,
            pool_maxsize=10
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
    def get_random_headers(self):
        """Genera headers aleatorios más realistas"""
        user_agent = random.choice(self.user_agents)
        
        # Headers base más completos
        headers = {
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'es-MX,es;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'max-age=0',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'DNT': '1',
            'Connection': 'keep-alive',
        }
        
        # Agregar referer aleatorio ocasionalmente
        if random.random() < 0.7:
            referers = [
                'https://www.google.com.mx/',
                'https://www.google.com/',
                'https://www.bing.com/',
                'https://duckduckgo.com/',
            ]
            headers['Referer'] = random.choice(referers)
            
        return headers
    
    def make_request(self, url, retries=3):
        """Request mejorada con técnicas anti-detección avanzadas"""
        for attempt in range(retries):
            try:
                # Delay más inteligente
                if attempt > 0:
                    delay = random.uniform(3, 8) * (attempt + 1)
                else:
                    delay = random.uniform(2, 5)
                
                logger.info(f"Esperando {delay:.2f}s antes del intento {attempt + 1}")
                time.sleep(delay)
                
                # Headers frescos para cada intento
                headers = self.get_random_headers()
                
                # Configuración de request más robusta
                response = self.session.get(
                    url,
                    headers=headers,
                    timeout=(10, 30),  # (connect timeout, read timeout)
                    allow_redirects=True,
                    stream=False
                )
                
                logger.info(f"Response status: {response.status_code} para {url}")
                
                if response.status_code == 200:
                    return response
                elif response.status_code == 403:
                    logger.warning(f"Acceso prohibido (403) - {url}")
                    time.sleep(random.uniform(10, 20))
                elif response.status_code == 429:
                    wait_time = random.uniform(15, 30)
                    logger.warning(f"Rate limited (429), esperando {wait_time:.2f}s")
                    time.sleep(wait_time)
                elif response.status_code in [404, 500, 502, 503]:
                    logger.warning(f"Error del servidor ({response.status_code}) - {url}")
                    
            except requests.exceptions.Timeout:
                logger.warning(f"Timeout en intento {attempt + 1}")
            except requests.exceptions.ConnectionError:
                logger.warning(f"Error de conexión en intento {attempt + 1}")
            except Exception as e:
                logger.error(f"Error en intento {attempt + 1}: {e}")
                
            if attempt < retries - 1:
                time.sleep(random.uniform(5, 10))
                
        return None
    
    def scrape_simple_source(self):
        """Scraper simple para fuente de respaldo usando datos estáticos de ejemplo"""
        try:
            # Simulamos datos para testing
            teams_data = [
                {'position': '1', 'team': 'Club América', 'points': '25', 'games': '12', 'wins': '8', 'draws': '1', 'losses': '3'},
                {'position': '2', 'team': 'Cruz Azul', 'points': '23', 'games': '12', 'wins': '7', 'draws': '2', 'losses': '3'},
                {'position': '3', 'team': 'Monterrey', 'points': '22', 'games': '12', 'wins': '7', 'draws': '1', 'losses': '4'},
                {'position': '4', 'team': 'Guadalajara', 'points': '21', 'games': '12', 'wins': '6', 'draws': '3', 'losses': '3'},
                {'position': '5', 'team': 'Tigres UANL', 'points': '20', 'games': '12', 'wins': '6', 'draws': '2', 'losses': '4'},
                {'position': '6', 'team': 'Pumas UNAM', 'points': '19', 'games': '12', 'wins': '6', 'draws': '1', 'losses': '5'},
                {'position': '7', 'team': 'Santos Laguna', 'points': '18', 'games': '12', 'wins': '5', 'draws': '3', 'losses': '4'},
                {'position': '8', 'team': 'Toluca', 'points': '17', 'games': '12', 'wins': '5', 'draws': '2', 'losses': '5'},
                {'position': '9', 'team': 'León', 'points': '16', 'games': '12', 'wins': '5', 'draws': '1', 'losses': '6'},
                {'position': '10', 'team': 'Atlas', 'points': '15', 'games': '12', 'wins': '4', 'draws': '3', 'losses': '5'},
                {'position': '11', 'team': 'Pachuca', 'points': '14', 'games': '12', 'wins': '4', 'draws': '2', 'losses': '6'},
                {'position': '12', 'team': 'Necaxa', 'points': '13', 'games': '12', 'wins': '4', 'draws': '1', 'losses': '7'},
                {'position': '13', 'team': 'Puebla', 'points': '12', 'games': '12', 'wins': '3', 'draws': '3', 'losses': '6'},
                {'position': '14', 'team': 'Tijuana', 'points': '11', 'games': '12', 'wins': '3', 'draws': '2', 'losses': '7'},
                {'position': '15', 'team': 'Mazatlán FC', 'points': '10', 'games': '12', 'wins': '3', 'draws': '1', 'losses': '8'},
                {'position': '16', 'team': 'Querétaro', 'points': '9', 'games': '12', 'wins': '2', 'draws': '3', 'losses': '7'},
                {'position': '17', 'team': 'Juárez', 'points': '8', 'games': '12', 'wins': '2', 'draws': '2', 'losses': '8'},
                {'position': '18', 'team': 'Atlético San Luis', 'points': '7', 'games': '12', 'wins': '2', 'draws': '1', 'losses': '9'}
            ]
            
            for team in teams_data:
                team['source'] = 'Demo Data'
                team['goal_diff'] = str(random.randint(-10, 15))
            
            logger.info("✓ Usando datos de demostración")
            return teams_data
            
        except Exception as e:
            logger.error(f"Error en datos de demo: {e}")
            return None
    
    def scrape_espn_alternative(self):
        """Scraper alternativo para ESPN con mejor parsing"""
        try:
            espn_url = 'https://www.espn.com.mx/futbol/posiciones/_/liga/mex.1'
            response = self.make_request(espn_url)
            
            if not response:
                return self.scrape_ligamx_oficial()
                
            soup = BeautifulSoup(response.content, 'html.parser')
            teams = []
            
            # Buscar tabla de posiciones específica de ESPN
            table_selectors = [
                'table.Table--align-right',
                'table.Table',
                '.Table__TBODY tr',
                'tbody tr',
                '.standings-table tbody tr',
                'table tbody tr'
            ]
            
            rows = []
            for selector in table_selectors:
                if 'tr' in selector:
                    rows = soup.select(selector)
                else:
                    table = soup.select_one(selector)
                    if table:
                        rows = table.find_all('tr')[1:]  # Skip header
                if rows:
                    break
            
            logger.info(f"Encontradas {len(rows)} filas en ESPN")
            
            if rows:
                for i, row in enumerate(rows[:18], 1):
                    cells = row.find_all(['td', 'th'])
                    
                    if len(cells) >= 6:
                        try:
                            # Extraer datos de las celdas
                            team_cell = cells[1] if len(cells) > 1 else cells[0]
                            team_name = team_cell.get_text(strip=True)
                            
                            # Limpiar nombre del equipo
                            if team_name:
                                team_name = team_name.replace('\n', ' ').strip()
                                
                            points = cells[2].get_text(strip=True) if len(cells) > 2 else '0'
                            games = cells[3].get_text(strip=True) if len(cells) > 3 else '0'
                            wins = cells[4].get_text(strip=True) if len(cells) > 4 else '0'
                            draws = cells[5].get_text(strip=True) if len(cells) > 5 else '0'
                            losses = cells[6].get_text(strip=True) if len(cells) > 6 else '0'
                            goal_diff = cells[7].get_text(strip=True) if len(cells) > 7 else '0'
                            
                            team_data = {
                                'position': str(i),
                                'team': self.normalize_team_name(team_name),
                                'points': points,
                                'games': games,
                                'wins': wins,
                                'draws': draws,
                                'losses': losses,
                                'goal_diff': goal_diff,
                                'source': 'ESPN MX'
                            }
                            teams.append(team_data)
                            
                        except Exception as e:
                            logger.warning(f"Error procesando fila {i}: {e}")
                            continue
                        
                logger.info(f"✓ ESPN: {len(teams)} equipos obtenidos")
                return teams if teams else self.scrape_ligamx_oficial()
            else:
                logger.warning("No se encontraron filas de tabla en ESPN")
                return self.scrape_ligamx_oficial()
                
        except Exception as e:
            logger.error(f"Error scraping ESPN: {e}")
            return self.scrape_ligamx_oficial()
            
    def scrape_ligamx_oficial(self):
        """Scraper para sitio oficial de Liga MX"""
        try:
            url = 'https://www.ligamx.net/cancha/stats'
            response = self.make_request(url)
            
            if not response:
                return self.scrape_medio_tiempo()
                
            soup = BeautifulSoup(response.content, 'html.parser')
            teams = []
            
            # Buscar tabla en Liga MX oficial
            table_selectors = [
                '.tabla-general tbody tr',
                '.standings tbody tr',
                'table tbody tr',
                '.table-stats tbody tr'
            ]
            
            rows = []
            for selector in table_selectors:
                rows = soup.select(selector)
                if rows:
                    break
            
            logger.info(f"Liga MX oficial: {len(rows)} filas encontradas")
            
            for i, row in enumerate(rows[:18], 1):
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 4:
                    try:
                        team_name = cells[1].get_text(strip=True) if len(cells) > 1 else f"Equipo {i}"
                        points = cells[2].get_text(strip=True) if len(cells) > 2 else '0'
                        
                        team_data = {
                            'position': str(i),
                            'team': self.normalize_team_name(team_name),
                            'points': points,
                            'games': cells[3].get_text(strip=True) if len(cells) > 3 else '0',
                            'wins': cells[4].get_text(strip=True) if len(cells) > 4 else '0',
                            'draws': cells[5].get_text(strip=True) if len(cells) > 5 else '0',
                            'losses': cells[6].get_text(strip=True) if len(cells) > 6 else '0',
                            'goal_diff': cells[7].get_text(strip=True) if len(cells) > 7 else '0',
                            'source': 'Liga MX Oficial'
                        }
                        teams.append(team_data)
                    except Exception as e:
                        logger.warning(f"Error procesando equipo {i}: {e}")
                        continue
            
            logger.info(f"✓ Liga MX oficial: {len(teams)} equipos")
            return teams if teams else self.scrape_medio_tiempo()
            
        except Exception as e:
            logger.error(f"Error en Liga MX oficial: {e}")
            return self.scrape_medio_tiempo()
    
    def scrape_medio_tiempo(self):
        """Scraper para Medio Tiempo como respaldo"""
        try:
            url = 'https://www.mediotiempo.com/futbol/liga-mx/tabla-posiciones'
            response = self.make_request(url)
            
            if not response:
                return self.scrape_simple_source()
                
            soup = BeautifulSoup(response.content, 'html.parser')
            teams = []
            
            # Buscar tabla en Medio Tiempo
            rows = soup.select('table tbody tr, .tabla-posiciones tr, .standings tr')
            
            logger.info(f"Medio Tiempo: {len(rows)} filas encontradas")
            
            for i, row in enumerate(rows[:18], 1):
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 3:
                    try:
                        team_name = cells[1].get_text(strip=True) if len(cells) > 1 else f"Equipo {i}"
                        points = cells[2].get_text(strip=True) if len(cells) > 2 else '0'
                        
                        team_data = {
                            'position': str(i),
                            'team': self.normalize_team_name(team_name),
                            'points': points,
                            'games': cells[3].get_text(strip=True) if len(cells) > 3 else '0',
                            'wins': cells[4].get_text(strip=True) if len(cells) > 4 else '0',
                            'draws': cells[5].get_text(strip=True) if len(cells) > 5 else '0',
                            'losses': cells[6].get_text(strip=True) if len(cells) > 6 else '0',
                            'goal_diff': '0',
                            'source': 'Medio Tiempo'
                        }
                        teams.append(team_data)
                    except Exception as e:
                        continue
            
            logger.info(f"✓ Medio Tiempo: {len(teams)} equipos")
            return teams if teams else self.scrape_simple_source()
            
        except Exception as e:
            logger.error(f"Error en Medio Tiempo: {e}")
            return self.scrape_simple_source()
    
    def scrape_foxsports(self):
        """Scraper para Fox Sports México"""
        try:
            url = 'https://www.foxsports.com.mx/futbol/liga-mx/tabla-de-posiciones'
            response = self.make_request(url)
            
            if not response:
                return None
                
            soup = BeautifulSoup(response.content, 'html.parser')
            teams = []
            
            # Buscar tabla en Fox Sports
            rows = soup.select('table tbody tr, .standings-table tr, .tabla tr')
            
            logger.info(f"Fox Sports: {len(rows)} filas encontradas")
            
            for i, row in enumerate(rows[:18], 1):
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 3:
                    try:
                        team_name = cells[1].get_text(strip=True) if len(cells) > 1 else f"Equipo {i}"
                        points = cells[2].get_text(strip=True) if len(cells) > 2 else '0'
                        
                        team_data = {
                            'position': str(i),
                            'team': self.normalize_team_name(team_name),
                            'points': points,
                            'games': cells[3].get_text(strip=True) if len(cells) > 3 else '0',
                            'wins': cells[4].get_text(strip=True) if len(cells) > 4 else '0',
                            'draws': cells[5].get_text(strip=True) if len(cells) > 5 else '0',
                            'losses': cells[6].get_text(strip=True) if len(cells) > 6 else '0',
                            'goal_diff': cells[7].get_text(strip=True) if len(cells) > 7 else '0',
                            'source': 'Fox Sports MX'
                        }
                        teams.append(team_data)
                    except Exception as e:
                        continue
            
            logger.info(f"✓ Fox Sports: {len(teams)} equipos")
            return teams if teams else None
            
        except Exception as e:
            logger.error(f"Error en Fox Sports: {e}")
            return None

    def scrape_all_sources(self):
        """Ejecuta scrapers de múltiples fuentes en tiempo real"""
        results = {}
        
        # Lista de scrapers en orden de prioridad
        scrapers = [
            ('espn_mx', self.scrape_espn_alternative),
            ('ligamx_oficial', self.scrape_ligamx_oficial),
            ('foxsports', self.scrape_foxsports),
            ('medio_tiempo', self.scrape_medio_tiempo)
        ]
        
        # Intentar cada scraper hasta obtener datos reales
        for source_name, scraper_func in scrapers:
            try:
                logger.info(f"🔄 Intentando {source_name}...")
                result = scraper_func()
                
                if result and len(result) >= 10:  # Necesitamos al menos 10 equipos para considerarlo válido
                    results[source_name] = result
                    logger.info(f"✅ {source_name}: {len(result)} equipos obtenidos")
                    break  # Usar la primera fuente exitosa
                else:
                    logger.warning(f"⚠️ {source_name}: datos insuficientes o vacíos")
                    
            except Exception as e:
                logger.error(f"❌ Error en {source_name}: {e}")
                continue
        
        # Solo usar datos de demostración como último recurso
        if not results:
            logger.warning("🔄 Todas las fuentes fallaron, usando datos de demostración")
            demo_data = self.scrape_simple_source()
            if demo_data:
                results['demo_data'] = demo_data
                logger.info("✓ Datos de demostración cargados")
        
        return results
    
    def consolidate_data(self, results):
        """Consolida datos de múltiples fuentes"""
        consolidated = {}
        
        for source, teams in results.items():
            for team in teams:
                team_name = self.normalize_team_name(team['team'])
                
                if team_name not in consolidated:
                    consolidated[team_name] = {
                        'name': team_name,
                        'sources': {},
                        'consensus': {}
                    }
                
                consolidated[team_name]['sources'][source] = team
        
        # Calcular consenso
        for team_name, data in consolidated.items():
            sources = data['sources']
            if sources:
                primary_source = list(sources.values())[0]
                data['consensus'] = primary_source
        
        return consolidated
    
    def normalize_team_name(self, name):
        """Normaliza nombres de equipos"""
        if not name:
            return "Equipo Desconocido"
            
        name = name.lower().strip()
        
        # Mapeo de nombres
        name_mapping = {
            'américa': 'Club América',
            'america': 'Club América',
            'cruz azul': 'Cruz Azul',
            'chivas': 'Guadalajara',
            'guadalajara': 'Guadalajara',
            'pumas': 'Pumas UNAM',
            'tigres': 'Tigres UANL',
            'monterrey': 'Monterrey',
            'santos': 'Santos Laguna',
            'toluca': 'Toluca',
            'león': 'León',
            'leon': 'León',
            'atlas': 'Atlas',
            'necaxa': 'Necaxa',
            'puebla': 'Puebla',
            'pachuca': 'Pachuca',
            'tijuana': 'Tijuana',
            'mazatlán': 'Mazatlán FC',
            'mazatlan': 'Mazatlán FC',
            'querétaro': 'Querétaro',
            'queretaro': 'Querétaro',
            'juárez': 'Juárez',
            'juarez': 'Juárez',
            'atlético san luis': 'Atlético San Luis',
            'atletico san luis': 'Atlético San Luis',
            'san luis': 'Atlético San Luis'
        }
        
        for key, value in name_mapping.items():
            if key in name:
                return value
        
        # Si no se encuentra mapping, capitalizar primera letra
        return name.title()
    
    def run_continuous_scraping(self, interval_minutes=1):
        """Ejecuta scraping continuo en tiempo real"""
        print(f"🚀 Iniciando scraper Liga MX TIEMPO REAL (actualización cada {interval_minutes} minuto)")
        print("🔴 MODO TIEMPO REAL ACTIVADO - Datos actualizados constantemente")
        
        while True:
            try:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                print(f"\n🔄 ACTUALIZANDO DATOS EN TIEMPO REAL - {timestamp}")
                
                # Ejecutar scrapers
                results = self.scrape_all_sources()
                
                if results and any(source != 'demo_data' for source in results.keys()):
                    # Consolidar datos reales
                    self.teams_data = self.consolidate_data(results)
                    self.last_update = datetime.now()
                    
                    # Mostrar resultados
                    self.display_table()
                    
                    # Guardar en JSON
                    self.save_to_json()
                    
                    source_names = list(results.keys())
                    print(f"✅ DATOS REALES obtenidos de: {', '.join(source_names)}")
                    
                elif results:
                    # Solo datos de demostración disponibles
                    self.teams_data = self.consolidate_data(results)
                    self.last_update = datetime.now()
                    self.display_table()
                    self.save_to_json()
                    print("⚠️  Usando datos de demostración (fuentes reales no disponibles)")
                    
                else:
                    print("❌ No se pudieron obtener datos de ninguna fuente")
                
                # Esperar menos tiempo para más frecuencia
                sleep_time = interval_minutes * 60
                print(f"⏰ Próxima actualización en {interval_minutes} minuto...")
                
                # Mostrar countdown más detallado
                for remaining in range(sleep_time, 0, -5):
                    time.sleep(5)
                    if remaining <= 30:
                        print(f"⌛ {remaining}s restantes...")
                    elif remaining % 30 == 0:
                        print(f"⌛ {remaining}s restantes...")
                
            except KeyboardInterrupt:
                print("\n🛑 Deteniendo scraper en tiempo real...")
                break
            except Exception as e:
                logger.error(f"Error general: {e}")
                print(f"⚠️  Error detectado, reintentando en 15 segundos...")
                time.sleep(15)  # Esperar menos tiempo para recuperación rápida
    
    def display_table(self):
        """Muestra la tabla de posiciones mejorada"""
        if not self.teams_data:
            print("❌ No hay datos para mostrar")
            return
            
        print("\n" + "="*90)
        print("🏆 TABLA GENERAL LIGA MX - TORNEO CLAUSURA 2024")
        print("="*90)
        print(f"{'Pos':<4} {'Equipo':<20} {'Pts':<5} {'PJ':<4} {'G':<3} {'E':<3} {'P':<3} {'DG':<4} {'Fuente':<12}")
        print("-"*90)
        
        # Ordenar por puntos
        try:
            sorted_teams = sorted(
                self.teams_data.values(), 
                key=lambda x: int(x['consensus'].get('points', 0)), 
                reverse=True
            )
        except:
            sorted_teams = list(self.teams_data.values())
        
        for i, team in enumerate(sorted_teams[:18], 1):
            consensus = team['consensus']
            print(f"{i:<4} {consensus.get('team', 'N/A'):<20} "
                  f"{consensus.get('points', 'N/A'):<5} "
                  f"{consensus.get('games', 'N/A'):<4} "
                  f"{consensus.get('wins', 'N/A'):<3} "
                  f"{consensus.get('draws', 'N/A'):<3} "
                  f"{consensus.get('losses', 'N/A'):<3} "
                  f"{consensus.get('goal_diff', 'N/A'):<4} "
                  f"{consensus.get('source', 'N/A'):<12}")
        
        print("="*90)
        if self.last_update:
            print(f"🕐 Última actualización: {self.last_update.strftime('%Y-%m-%d %H:%M:%S')}")
    
    def save_to_json(self):
        """Guarda los datos en archivo JSON"""
        try:
            data = {
                'last_update': self.last_update.isoformat() if self.last_update else None,
                'total_teams': len(self.teams_data),
                'teams': self.teams_data,
                'metadata': {
                    'scraper_version': '2.0',
                    'update_interval': '3 minutes',
                    'sources_available': list(self.sources.keys())
                }
            }
            
            with open('liga_mx_table.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Datos guardados en liga_mx_table.json ({len(self.teams_data)} equipos)")
            
        except Exception as e:
            logger.error(f"Error guardando JSON: {e}")

def main():
    scraper = LigaMXScraper()
    
    print("🏆 SCRAPER LIGA MX - TIEMPO REAL MULTIFUENTES v3.0")
    print("=" * 70)
    print("🔴 MODO TIEMPO REAL ACTIVADO:")
    print("✓ ESPN México - Datos en vivo")
    print("✓ Liga MX Oficial - Fuente primaria")
    print("✓ Fox Sports MX - Datos alternativos")
    print("✓ Medio Tiempo - Respaldo confiable")
    print("✓ Actualización cada 1 minuto")
    print("✓ Anti-detección avanzado")
    print("✓ Headers realistas 2024")
    print("✓ Manejo inteligente de errores")
    print("✓ Datos reales vs demostración")
    print("=" * 70)
    
    try:
        # Ejecutar scraping en tiempo real (cada minuto)
        scraper.run_continuous_scraping(interval_minutes=1)
    except KeyboardInterrupt:
        print("\n👋 ¡Scraper en tiempo real detenido! ¡Hasta luego!")

if __name__ == "__main__":
    main()
