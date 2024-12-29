import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import ttkbootstrap as ttkb
import threading
import os
import time
from tor_connection import connect_to_tor
from scraper import scrape_onion_site
from analyzer import analyze_text, sentiment_analysis
from db_helper import initialize_database, insert_data
from alerts import send_email

class DarkWebMonitorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Dark Web Monitoring Tool")
        self.root.geometry("800x600")
        
        # Configure style
        self.style = ttkb.Style(theme='darkly')
        
        # Create main container
        self.main_container = ttkb.Frame(root, padding="20")
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        # Header
        self.header_frame = ttkb.Frame(self.main_container, bootstyle='dark')
        self.header_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.title_label = ttkb.Label(
            self.header_frame, 
            text="Dark Web Monitoring Tool", 
            font=('Helvetica', 16, 'bold'),
            bootstyle='inverse-dark'
        )
        self.title_label.pack(pady=10)
        
        # Input Frame
        self.input_frame = ttkb.LabelFrame(self.main_container, text="Monitoring Configuration", bootstyle='primary')
        self.input_frame.pack(fill=tk.X, pady=10)
        
        # URLs Input
        ttkb.Label(self.input_frame, text="URLs (comma-separated):").pack(anchor='w', padx=10, pady=(10,0))
        self.urls_entry = ttkb.Entry(self.input_frame, width=70)
        self.urls_entry.pack(padx=10, pady=5, fill=tk.X)
        
        # Keywords Input
        ttkb.Label(self.input_frame, text="Keywords (comma-separated):").pack(anchor='w', padx=10, pady=(10,0))
        self.keywords_entry = ttkb.Entry(self.input_frame, width=70)
        self.keywords_entry.pack(padx=10, pady=5, fill=tk.X)
        
        # Results Frame
        self.results_frame = ttkb.LabelFrame(self.main_container, text="Scraping Results", bootstyle='primary')
        self.results_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Results Table
        self.results_table = ttk.Treeview(
            self.results_frame, 
            columns=('URL', 'Keywords', 'Sentiment', 'Snippet'), 
            show='headings'
        )
        self.results_table.heading('URL', text='URL')
        self.results_table.heading('Keywords', text='Keywords')
        self.results_table.heading('Sentiment', text='Sentiment')
        self.results_table.heading('Snippet', text='Snippet')
        
        # Scrollbar for results
        results_scrollbar = ttkb.Scrollbar(
            self.results_frame, 
            orient=tk.VERTICAL, 
            bootstyle='primary-round', 
            command=self.results_table.yview
        )
        self.results_table.configure(yscroll=results_scrollbar.set)
        
        self.results_table.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0,10))
        results_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Action Buttons Frame
        self.action_frame = ttkb.Frame(self.main_container)
        self.action_frame.pack(fill=tk.X, pady=10)
        
        # Start Scraping Button
        self.start_button = ttkb.Button(
            self.action_frame, 
            text="Start Scraping", 
            bootstyle='success-outline',
            command=self.start_scraping_thread
        )
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        # Email Results Button
        self.email_button = ttkb.Button(
            self.action_frame, 
            text="Email Results", 
            bootstyle='info-outline',
            command=self.send_email_results
        )
        self.email_button.pack(side=tk.LEFT, padx=5)
        
        # Progress Bar
        self.progress = ttkb.Progressbar(
            self.main_container, 
            bootstyle='success-striped', 
            length=200, 
            mode='indeterminate'
        )
        self.progress.pack(pady=10)
        
        # Initialize Database
        initialize_database()
    
    def start_scraping_thread(self):
        """Start scraping in a separate thread to keep GUI responsive"""
        urls = [url.strip() for url in self.urls_entry.get().split(',')]
        keywords = [keyword.strip() for keyword in self.keywords_entry.get().split(',')]
        
        if not urls or not keywords:
            messagebox.showerror("Error", "Please enter URLs and keywords.")
            return
        
        # Clear previous results
        for i in self.results_table.get_children():
            self.results_table.delete(i)
        
        # Start progress
        self.progress.start()
        self.start_button.config(state=tk.DISABLED)
        
        # Threading for non-blocking scraping
        threading.Thread(
            target=self.perform_scraping, 
            args=(urls, keywords), 
            daemon=True
        ).start()
    
    def perform_scraping(self, urls, keywords):
        """Actual scraping logic"""
        try:
            session = connect_to_tor()
            if not session:
                self.show_error("Failed to establish Tor session")
                return
            
            scraped_data = []
            for url in urls:
                try:
                    soup = scrape_onion_site(url, session)
                    if soup:
                        text = soup.get_text()
                        detected_keywords = analyze_text(text, keywords)
                        sentiment = sentiment_analysis(text)
                        
                        # Insert into database
                        insert_data(url, detected_keywords, sentiment, text[:200])
                        
                        # Populate results table
                        scraped_item = (
                            url, 
                            ", ".join(detected_keywords), 
                            sentiment, 
                            text[:200]
                        )
                        scraped_data.append(scraped_item)
                        
                        # Update GUI
                        self.root.after(0, self.update_results_table, scraped_item)
                    
                    time.sleep(1)  # Simulating delay between requests
                except Exception as e:
                    print(f"Error scraping {url}: {e}")
        except Exception as e:
            self.show_error(str(e))
        finally:
            # Stop progress and re-enable button
            self.root.after(0, self.scraping_complete)
    
    def update_results_table(self, result):
        """Thread-safe method to update results table"""
        self.results_table.insert('', 'end', values=result)
    
    def scraping_complete(self):
        """Reset UI after scraping"""
        self.progress.stop()
        self.start_button.config(state=tk.NORMAL)
        messagebox.showinfo("Complete", "Scraping process finished!")
    
    def send_email_results(self):
        """Send results via email"""
        email = tk.simpledialog.askstring("Email Results", "Enter email address:")
        if email:
            try:
                send_email(email)
                messagebox.showinfo("Success", f"Results sent to {email}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to send email: {str(e)}")
    
    def show_error(self, message):
        """Display error messages"""
        self.root.after(0, messagebox.showerror, "Error", message)

def main():
    root = ttkb.Window(themename="darkly")
    app = DarkWebMonitorApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()