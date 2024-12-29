import os
import time
import sys
import logging
from logging.handlers import RotatingFileHandler
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.prompt import Prompt, Confirm
from rich.text import Text
from rich.layout import Layout
from rich.live import Live
from rich import print
import threading

# Import your existing modules
from tor_connection import connect_to_tor
from scraper import scrape_onion_site
from analyzer import analyze_text, sentiment_analysis
from db_helper import initialize_database, insert_data
from alerts import send_email

class LogFormatter(logging.Formatter):
    """Custom log formatter to make logs more readable"""
    def format(self, record):
        # Color coding for different log levels
        log_colors = {
            logging.DEBUG: "dim white",
            logging.INFO: "green",
            logging.WARNING: "yellow",
            logging.ERROR: "red",
            logging.CRITICAL: "bold red"
        }
        
        # Format the log message with color
        log_fmt = f"[{log_colors.get(record.levelno, 'white')}]{self.formatTime(record)} - {record.levelname} - {record.msg}[/]"
        return log_fmt

class TerminalDarkWebMonitor:
    def __init__(self, log_level=logging.INFO):
        # Setup console
        self.console = Console()
        
        # Setup logging
        self.logger = self._setup_logging(log_level)
        
        # Initialize database
        initialize_database()
        
        # Log initialization
        self.logger.info("Dark Web Monitoring Tool Initialized")

    def _setup_logging(self, log_level):
        """Setup logging with both file and console handlers"""
        # Create logs directory if it doesn't exist
        os.makedirs('logs', exist_ok=True)
        
        # Create a logger
        logger = logging.getLogger('DarkWebMonitor')
        logger.setLevel(log_level)
        
        # Clear any existing handlers to prevent duplicate logs
        logger.handlers.clear()
        
        # Create a file handler with log rotation
        file_handler = RotatingFileHandler(
            'logs/dark_web_monitor.log', 
            maxBytes=10*1024*1024,  # 10 MB
            backupCount=5  # Keep 5 backup logs
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        ))
        file_handler.setLevel(log_level)
        
        # Create a custom console handler using Rich
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(LogFormatter())
        console_handler.setLevel(log_level)
        
        # Add handlers to logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger

    def draw_banner(self):
        banner = Panel(
            Text("Dark Web Monitoring Tool", style="bold magenta"),
            title="[bold green]🌐 Cyber Intelligence System ",
            border_style="bold blue",
            expand=False
        )
        self.console.print(banner)
        self.logger.info("Banner displayed")

    def get_user_input(self):
        self.console.rule("[bold cyan]Configuration")
        
        urls_input = Prompt.ask(
            "[bold yellow]Enter URLs", 
            default="example.onion", 
            show_default=True
        )
        urls = [url.strip() for url in urls_input.split(',')]
        
        keywords_input = Prompt.ask(
            "[bold yellow]Enter Keywords", 
            default="threat,risk,security", 
            show_default=True
        )
        keywords = [keyword.strip() for keyword in keywords_input.split(',')]
        
        self.logger.info(f"URLs to monitor: {urls}")
        self.logger.info(f"Keywords to search: {keywords}")
        
        return urls, keywords

    def scrape_with_progress(self, urls, keywords):
        results = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            transient=True
        ) as progress:
            overall_task = progress.add_task("[green]Scraping Dark Web...", total=len(urls))
            
            try:
                session = connect_to_tor()
                if not session:
                    self.logger.error("Failed to establish Tor session!")
                    self.console.print("[bold red]Failed to establish Tor session!")
                    return []
            except Exception as e:
                self.logger.error(f"Tor Connection Error: {e}")
                self.console.print(f"[bold red]Tor Connection Error: {e}")
                return []

            for url in urls:
                try:
                    progress.update(overall_task, advance=0, description=f"[yellow]Scraping {url}")
                    self.logger.info(f"Attempting to scrape URL: {url}")
        
                    soup = scrape_onion_site(url, session)
                    if soup:
                        text = soup.get_text()
                        detected_keywords = analyze_text(text, keywords)
                        sentiment = sentiment_analysis(text)

                        result = {
                            'url': url,
                            'keywords': detected_keywords,
                            'sentiment': sentiment,
                            'snippet': text[:200]
                        }
                        results.append(result)

                        insert_data(url, detected_keywords, sentiment, text[:200])
                        
                        # Log successful scraping and findings
                        if detected_keywords:
                            self.logger.warning(f"Keywords detected on {url}: {detected_keywords}")
                        self.logger.info(f"Scraped {url} successfully. Sentiment: {sentiment}")
                    
                    progress.update(overall_task, advance=1)
                    time.sleep(1) 
                
                except Exception as e:
                    self.logger.error(f"Error scraping {url}: {e}")
                    self.console.print(f"[bold red]Error scraping {url}: {e}")
                
        return results

    def display_results(self, results):
        """Display results in a rich, formatted table"""
        if not results:
            self.logger.warning("No results found during scraping")
            self.console.print("[bold red]No results found.")
            return

        # Create results table
        table = Table(title="Dark Web Monitoring Results")
        table.add_column("URL", style="cyan")
        table.add_column("Keywords", style="green")
        table.add_column("Sentiment", style="magenta")
        table.add_column("Snippet", style="dim")

        for result in results:
            table.add_row(
                result['url'], 
                ", ".join(result['keywords']), 
                result['sentiment'], 
                result['snippet']
            )
            # Log each result
            self.logger.info(f"Result - URL: {result['url']}, Keywords: {result['keywords']}")

        self.console.print(table)

    def export_option(self, results):
        """Export results with rich confirmation and logging"""
        if results:
            export = Confirm.ask("[bold yellow]Do you want to export results?")
            if export:
                export_type = Prompt.ask(
                    "[bold green]Select Export Format", 
                    choices=["json", "csv"], 
                    default="json"
                )
                
                filename = f"logs/dark_web_results.{export_type}"
                
                try:
                    with open(filename, 'w') as f:
                        if export_type == 'json':
                            import json
                            json.dump(results, f, indent=4)
                        else:
                            import csv
                            writer = csv.DictWriter(f, fieldnames=results[0].keys())
                            writer.writeheader()
                            writer.writerows(results)
                    
                    self.logger.info(f"Results exported to {filename}")
                    self.console.print(f"[bold green]Exported to {filename}")
                
                except Exception as e:
                    self.logger.error(f"Export failed: {e}")
                    self.console.print(f"[bold red]Export failed: {e}")

    def email_option(self):
        """Email results with rich styling and logging"""
        send_email_choice = Confirm.ask("[bold yellow]Send results via email?")
        if send_email_choice:
            email = Prompt.ask("[bold green]Enter email address")
            try:
                send_email(email)
                self.logger.info(f"Results sent to {email}")
                self.console.print(f"[bold green]Results sent to {email}!")
            except Exception as e:
                self.logger.error(f"Email sending failed: {e}")
                self.console.print(f"[bold red]Email sending failed: {e}")

    def run(self):
        """Main application flow with logging"""
        try:
            # Clear screen (cross-platform)
            os.system('cls' if os.name == 'nt' else 'clear')
            
            # Draw banner
            self.draw_banner()
            
            # Get user input
            urls, keywords = self.get_user_input()
            
            # Scrape with progress
            results = self.scrape_with_progress(urls, keywords)
            
            # Display results
            self.display_results(results)
            
            # Export option
            self.export_option(results)
            
            # Email option
            self.email_option()
            
        except Exception as e:
            self.logger.critical(f"Unhandled exception in run method: {e}", exc_info=True)
            self.console.print(f"[bold red]An unexpected error occurred: {e}")

def main():
    try:
        monitor = TerminalDarkWebMonitor()
        monitor.run()
    except KeyboardInterrupt:
        print("\n[bold red]Operation cancelled by user.")
    except Exception as e:
        print(f"[bold red]An error occurred: {e}")

if __name__ == "__main__":
    main()