import os
import time
import sys
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

class TerminalDarkWebMonitor:
    def __init__(self):
        self.console = Console()
        initialize_database()

    def draw_banner(self):
        banner = Panel(
            Text("Dark Web Monitoring Tool", style="bold magenta"),
            title="[bold green]🌐 Cyber Intelligence System ",
            border_style="bold blue",
            expand=False
        )
        self.console.print(banner)

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
                    self.console.print("[bold red]Failed to establish Tor session!")
                    return []
            except Exception as e:
                self.console.print(f"[bold red]Tor Connection Error: {e}")
                return []

            for url in urls:
                try:
                    progress.update(overall_task, advance=0, description=f"[yellow]Scraping {url}")
        
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
                    
                    progress.update(overall_task, advance=1)
                    time.sleep(1) 
                
                except Exception as e:
                    self.console.print(f"[bold red]Error scraping {url}: {e}")
                
        return results

    def display_results(self, results):
        """Display results in a rich, formatted table"""
        if not results:
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

        self.console.print(table)

    def export_option(self, results):
        """Export results with rich confirmation"""
        if results:
            export = Confirm.ask("[bold yellow]Do you want to export results?")
            if export:
                export_type = Prompt.ask(
                    "[bold green]Select Export Format", 
                    choices=["json", "csv"], 
                    default="json"
                )
                
                filename = f"dark_web_results.{export_type}"
                
                # Mock export (you'd replace with actual export logic)
                with open(filename, 'w') as f:
                    if export_type == 'json':
                        import json
                        json.dump(results, f, indent=4)
                    else:
                        import csv
                        writer = csv.DictWriter(f, fieldnames=results[0].keys())
                        writer.writeheader()
                        writer.writerows(results)
                
                self.console.print(f"[bold green]Exported to {filename}")

    def email_option(self):
        """Email results with rich styling"""
        send_email_choice = Confirm.ask("[bold yellow]Send results via email?")
        if send_email_choice:
            email = Prompt.ask("[bold green]Enter email address")
            try:
                send_email(email)
                self.console.print(f"[bold green]Results sent to {email}!")
            except Exception as e:
                self.console.print(f"[bold red]Email sending failed: {e}")

    def run(self):
        """Main application flow"""
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
